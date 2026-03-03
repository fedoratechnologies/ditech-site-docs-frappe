from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


ROLES = [
	"Ditech Site Docs User",
	"Ditech Site Docs Manager",
	"Ditech Credentials Admin",
	"Ditech Insurance Admin",
]


def after_install() -> None:
	ensure_roles()
	ensure_doctype_permissions()
	ensure_custom_fields()


def after_migrate() -> None:
	"""Keep DocType perms/roles consistent across GitOps deploys."""
	ensure_roles()
	ensure_doctype_permissions()
	ensure_custom_fields()


def ensure_roles() -> None:
	for role_name in ROLES:
		if frappe.db.exists("Role", role_name):
			continue
		role = frappe.get_doc({"doctype": "Role", "role_name": role_name})
		role.insert(ignore_permissions=True)


def _set_perms(doctype: str, permissions: list[dict]) -> None:
	dt = frappe.get_doc("DocType", doctype)
	dt.permissions = []
	for p in permissions:
		dt.append("permissions", p)
	dt.save(ignore_permissions=True)
	frappe.clear_cache(doctype=doctype)


def ensure_doctype_permissions() -> None:
	_set_perms(
		"MSP Site",
		[
			{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "export": 1, "print": 1},
			{"role": "Ditech Site Docs User", "read": 1, "export": 1, "print": 1},
			{"role": "Ditech Site Docs Manager", "read": 1, "write": 1, "create": 1, "export": 1, "print": 1},
		],
	)

	_set_perms(
		"MSP Site Device",
		[
			{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "export": 1, "print": 1},
			{"role": "Ditech Site Docs User", "read": 1, "export": 1, "print": 1},
			{"role": "Ditech Site Docs Manager", "read": 1, "write": 1, "create": 1, "export": 1, "print": 1},
		],
	)

	_set_perms(
		"MSP Site Account",
		[
			{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "export": 1, "print": 1},
			{"role": "Ditech Credentials Admin", "read": 1, "write": 1, "create": 1, "export": 1, "print": 1},
		],
	)

	_set_perms(
		"MSP Google Workspace",
		[
			{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "export": 1, "print": 1},
			{"role": "Ditech Credentials Admin", "read": 1, "write": 1, "create": 1, "export": 1, "print": 1},
			{"role": "Ditech Site Docs Manager", "read": 1, "export": 0, "print": 0},
		],
	)

	_set_perms(
		"MSP Site User",
		[
			{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "export": 1, "print": 1},
			{"role": "Ditech Site Docs User", "read": 1, "export": 1, "print": 1},
			{"role": "Ditech Site Docs Manager", "read": 1, "write": 1, "create": 1, "export": 1, "print": 1},
		],
	)

	_set_perms(
		"MSP Device Event",
		[
			{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "export": 1, "print": 1},
			{"role": "Ditech Site Docs User", "read": 1, "export": 1, "print": 1},
			{"role": "Ditech Site Docs Manager", "read": 1, "write": 1, "create": 1, "export": 1, "print": 1},
		],
	)

	_set_perms(
		"MSP Insurance Policy",
		[
			{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "export": 1, "print": 1},
			{"role": "Ditech Insurance Admin", "read": 1, "write": 1, "create": 1, "export": 1, "print": 1},
			{"role": "Ditech Site Docs User", "read": 1, "export": 1, "print": 1},
			{"role": "Ditech Site Docs Manager", "read": 1, "export": 1, "print": 1},
		],
	)

	_set_perms(
		"MSP Insurance Transaction",
		[
			{
				"role": "System Manager",
				"read": 1,
				"write": 1,
				"create": 1,
				"delete": 1,
				"export": 1,
				"print": 1,
				"submit": 1,
				"cancel": 1,
			},
			{
				"role": "Ditech Insurance Admin",
				"read": 1,
				"write": 1,
				"create": 1,
				"export": 1,
				"print": 1,
				"submit": 1,
				"cancel": 1,
			},
			{"role": "Ditech Site Docs User", "read": 1, "print": 1},
			{"role": "Ditech Site Docs Manager", "read": 1, "print": 1},
		],
	)


def ensure_custom_fields() -> None:
	"""Add stable, GitOps-managed fields needed for MSP workflows."""
	fields = [
		{
			"fieldname": "msp_site",
			"label": "MSP Site",
			"fieldtype": "Link",
			"options": "MSP Site",
			"insert_after": "customer",
		},
		{
			"fieldname": "msp_site_device",
			"label": "MSP Site Device",
			"fieldtype": "Link",
			"options": "MSP Site Device",
			"insert_after": "msp_site",
		},
	]

	create_custom_fields({"HD Ticket": fields}, update=True)
