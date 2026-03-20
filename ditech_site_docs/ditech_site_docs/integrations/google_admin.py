from __future__ import annotations

import json

import frappe
from frappe import _

try:
	from google.oauth2 import service_account
	from googleapiclient.discovery import build
except Exception:  # pragma: no cover
	service_account = None  # type: ignore[assignment]
	build = None  # type: ignore[assignment]


SCOPES = [
	"https://www.googleapis.com/auth/admin.directory.user.readonly",
	"https://www.googleapis.com/auth/admin.directory.device.chromeos.readonly",
]


def sync_all_enabled_workspaces() -> None:
	"""Scheduled sync (every 3 hours) for all enabled Google Workspace configs."""
	if service_account is None or build is None:
		frappe.log_error(
			title="DiTech: Google Admin sync unavailable",
			message="Missing google-api-python-client/google-auth dependencies.",
		)
		return

	workspaces = frappe.get_all(
		"MSP Google Workspace",
		filters={"enabled": 1},
		fields=["name"],
		limit_page_length=200,
	)
	for row in workspaces:
		_sync_one_workspace(row.name)


@frappe.whitelist()
def enqueue_sync_workspace(workspace_name: str) -> None:
	"""Manually trigger a single-workspace sync (runs in the background)."""
	workspace_name = (workspace_name or "").strip()
	if not workspace_name:
		frappe.throw(_("Missing workspace name."))

	if not frappe.has_permission("MSP Google Workspace", "write", workspace_name):
		frappe.throw(_("Not permitted."))

	frappe.enqueue(
		"ditech_site_docs.ditech_site_docs.integrations.google_admin._sync_one_workspace",
		queue="long",
		job_name=f"ditech-google-admin-sync:{workspace_name}",
		workspace_name=workspace_name,
	)


def _sync_one_workspace(workspace_name: str) -> None:
	workspace = frappe.get_doc("MSP Google Workspace", workspace_name)
	workspace.last_sync_on = frappe.utils.now()

	if not workspace.delegated_admin_email:
		_set_workspace_status(workspace, "SKIPPED", "Missing delegated admin email.")
		return

	try:
		service_account_json = (workspace.get_password("service_account_json") or "").strip()
	except Exception:
		service_account_json = ""
	if not service_account_json:
		_set_workspace_status(workspace, "SKIPPED", "Missing service account JSON.")
		return

	try:
		service_account_info = json.loads(service_account_json)
	except Exception:
		_set_workspace_status(workspace, "ERROR", "Invalid service account JSON (could not parse).")
		return

	try:
		creds = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
		creds = creds.with_subject(workspace.delegated_admin_email)
		admin = build("admin", "directory_v1", credentials=creds, cache_discovery=False)

		users_ok = True
		devices_ok = True

		try:
			_sync_users(admin=admin, site=workspace.site)
		except Exception:
			users_ok = False
			frappe.log_error(
				title=f"DiTech: Google Admin users sync failed ({workspace.name})",
				message=frappe.get_traceback(),
			)

		try:
			_sync_chromeos_devices(admin=admin, site=workspace.site)
		except Exception:
			devices_ok = False
			frappe.log_error(
				title=f"DiTech: Google Admin ChromeOS sync failed ({workspace.name})",
				message=frappe.get_traceback(),
			)

		if users_ok and devices_ok:
			_set_workspace_status(workspace, "OK", "Synced users and ChromeOS devices.")
		elif devices_ok and not users_ok:
			_set_workspace_status(
				workspace,
				"OK",
				"Synced ChromeOS devices; user sync failed (check delegated admin privileges / scope: admin.directory.user.readonly).",
			)
		elif users_ok and not devices_ok:
			_set_workspace_status(
				workspace,
				"OK",
				"Synced users; ChromeOS device sync failed (check delegated admin privileges / scope: admin.directory.device.chromeos.readonly).",
			)
		else:
			_set_workspace_status(workspace, "ERROR", "Sync failed. See Error Log for details.")
	except Exception:
		frappe.log_error(title=f"DiTech: Google Admin sync failed ({workspace.name})", message=frappe.get_traceback())
		_set_workspace_status(workspace, "ERROR", "Sync failed. See Error Log for details.")


def _set_workspace_status(workspace: frappe.model.document.Document, status: str, message: str) -> None:
	# Avoid `workspace.save()` here: password fields may not be loaded and can be cleared on save.
	frappe.db.set_value(
		"MSP Google Workspace",
		workspace.name,
		{
			"last_sync_on": workspace.last_sync_on,
			"last_sync_status": status,
			"last_sync_message": message,
		},
		update_modified=False,
	)


def _sync_users(admin, site: str) -> None:
	page_token = None
	while True:
		resp = (
			admin.users()
			.list(customer="my_customer", maxResults=500, orderBy="email", pageToken=page_token)
			.execute()
		)
		for user in resp.get("users", []) or []:
			_upsert_site_user(site=site, user=user)

		page_token = resp.get("nextPageToken")
		if not page_token:
			break


def _upsert_site_user(site: str, user: dict) -> None:
	email = (user.get("primaryEmail") or "").strip()
	if not email:
		return

	google_user_id = (user.get("id") or "").strip()
	full_name = ((user.get("name") or {}).get("fullName") or "").strip()
	org_unit_path = (user.get("orgUnitPath") or "").strip()
	suspended = 1 if user.get("suspended") else 0
	is_admin = 1 if (user.get("isAdmin") or user.get("isDelegatedAdmin")) else 0
	last_login_time = user.get("lastLoginTime")

	user_name = (
		frappe.db.get_value("MSP Site User", {"site": site, "google_user_id": google_user_id}, "name")
		if google_user_id
		else None
	)
	if not user_name:
		user_name = frappe.db.get_value("MSP Site User", {"site": site, "email": email}, "name")

	if user_name:
		doc = frappe.get_doc("MSP Site User", user_name)
	else:
		doc = frappe.new_doc("MSP Site User")
		doc.site = site
		doc.email = email

	doc.full_name = full_name
	doc.org_unit_path = org_unit_path
	doc.suspended = suspended
	doc.is_admin = is_admin
	doc.google_user_id = google_user_id or doc.google_user_id
	if last_login_time:
		try:
			dt = frappe.utils.get_datetime(last_login_time)
			if getattr(dt, "tzinfo", None):
				dt = dt.replace(tzinfo=None)
			doc.last_login = dt
		except Exception:
			pass
	doc.is_archived = 0
	doc.save(ignore_permissions=True)


def _sync_chromeos_devices(admin, site: str) -> None:
	page_token = None
	while True:
		resp = (
			admin.chromeosdevices()
			.list(customerId="my_customer", maxResults=200, orderBy="serialNumber", pageToken=page_token)
			.execute()
		)
		for device in resp.get("chromeosdevices", []) or []:
			_upsert_site_device(site=site, device=device)

		page_token = resp.get("nextPageToken")
		if not page_token:
			break


def _upsert_site_device(site: str, device: dict) -> None:
	device_id = (device.get("deviceId") or "").strip()
	serial = (device.get("serialNumber") or "").strip()
	mac = (device.get("macAddress") or "").strip()

	name = None
	if device_id:
		name = frappe.db.get_value("MSP Site Device", {"site": site, "google_device_id": device_id}, "name")
	if not name and serial:
		name = frappe.db.get_value("MSP Site Device", {"site": site, "serial_number": serial}, "name")
	if not name and mac:
		name = frappe.db.get_value("MSP Site Device", {"site": site, "mac": mac}, "name")

	annotated_asset_id = (device.get("annotatedAssetId") or "").strip()
	org_unit_path = (device.get("orgUnitPath") or "").strip()
	status = (device.get("status") or "").strip()
	model = (device.get("model") or "").strip()
	assigned_user_email = (device.get("annotatedUser") or "").strip()
	last_sync = device.get("lastSync") or device.get("lastEnrollmentTime")

	if name:
		doc = frappe.get_doc("MSP Site Device", name)
		prev_status = (doc.google_status or "").strip()
		prev_assigned = (doc.google_assigned_user_email or "").strip()
	else:
		doc = frappe.new_doc("MSP Site Device")
		doc.site = site
		doc.section = "Chromebooks"
		doc.item = annotated_asset_id or serial or device_id or "Chromebook"
		prev_status = ""
		prev_assigned = ""

	doc.source_system = "Google Admin"
	doc.model = model or doc.model
	doc.serial_number = serial or doc.serial_number
	doc.mac = mac or doc.mac
	doc.location = org_unit_path or doc.location

	doc.google_device_id = device_id or doc.google_device_id
	doc.google_status = status
	doc.google_org_unit_path = org_unit_path
	doc.google_assigned_user_email = assigned_user_email
	if last_sync:
		try:
			dt = frappe.utils.get_datetime(last_sync)
			if getattr(dt, "tzinfo", None):
				dt = dt.replace(tzinfo=None)
			doc.google_last_sync_on = dt
		except Exception:
			pass

	if assigned_user_email:
		user_name = frappe.db.get_value("MSP Site User", {"site": site, "email": assigned_user_email}, "name")
		doc.assigned_user = user_name or None

	doc.save(ignore_permissions=True)

	if name and status and prev_status and status != prev_status:
		_create_device_event(
			site=site,
			device=doc.name,
			event_type="Status Change",
			old_value=prev_status,
			new_value=status,
			details="Google Admin status changed.",
		)

	if name and assigned_user_email and prev_assigned and assigned_user_email != prev_assigned:
		_create_device_event(
			site=site,
			device=doc.name,
			event_type="Assignment Change",
			old_value=prev_assigned,
			new_value=assigned_user_email,
			details="Google Admin assignment changed.",
		)


def _create_device_event(
	site: str,
	device: str,
	event_type: str,
	details: str | None = None,
	old_value: str | None = None,
	new_value: str | None = None,
) -> None:
	event = frappe.get_doc(
		{
			"doctype": "MSP Device Event",
			"site": site,
			"device": device,
			"source_system": "Google Admin",
			"event_type": event_type,
			"details": details,
			"old_value": old_value,
			"new_value": new_value,
		}
	)
	event.insert(ignore_permissions=True)
