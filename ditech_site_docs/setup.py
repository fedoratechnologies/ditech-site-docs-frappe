from __future__ import annotations

import json

import frappe


REPORT_NAME = "Site Docs Overview"
WORKSPACE_NAME = "Ditech Site Docs"
CARD_SITES = "MSP Sites"
CARD_DEVICES = "MSP Devices"
CARD_ROOMS = "MSP Rooms"
CARD_ACCOUNTS = "MSP Accounts"
CARD_UNLINKED = "Devices Missing Account"


def ensure_site_docs_report() -> None:
	# Query Report: combined view of Site + Device + linked Account (vendor/system).
	query = """
SELECT
  s.customer AS customer,
  s.name AS site,
  s.site_name AS site_name,
  d.name AS device,
  d.item AS item,
  d.section AS section,
  d.location AS location,
  d.model AS model,
  d.serial_number AS serial_number,
  d.assigned_to_type AS assigned_to,
  d.assigned_user_email AS assigned_user_email,
  d.assigned_room AS assigned_room,
  r.room_name AS assigned_room_name,
  d.mac AS mac,
  d.lan1_ip AS lan1_ip,
  d.wan_ip AS wan_ip,
  d.site_account AS site_account,
  a.vendor AS account_vendor
FROM `tabMSP Site Device` d
JOIN `tabMSP Site` s ON s.name = d.site
LEFT JOIN `tabMSP Site Account` a ON a.name = d.site_account
LEFT JOIN `tabMSP Room` r ON r.name = d.assigned_room
WHERE 1=1
  AND (%(customer)s IS NULL OR %(customer)s = '' OR s.customer = %(customer)s)
  AND (%(site)s IS NULL OR %(site)s = '' OR d.site = %(site)s)
  AND (%(assigned_room)s IS NULL OR %(assigned_room)s = '' OR d.assigned_room = %(assigned_room)s)
  AND (%(assigned_user_email)s IS NULL OR %(assigned_user_email)s = '' OR d.assigned_user_email LIKE CONCAT('%%', %(assigned_user_email)s, '%%'))
  AND (%(account_vendor)s IS NULL OR %(account_vendor)s = '' OR a.vendor LIKE CONCAT('%%', %(account_vendor)s, '%%'))
  AND (%(item)s IS NULL OR %(item)s = '' OR d.item LIKE CONCAT('%%', %(item)s, '%%'))
  AND (%(serial_number)s IS NULL OR %(serial_number)s = '' OR d.serial_number LIKE CONCAT('%%', %(serial_number)s, '%%'))
  AND (%(mac)s IS NULL OR %(mac)s = '' OR d.mac LIKE CONCAT('%%', %(mac)s, '%%'))
ORDER BY s.site_name, d.item, d.serial_number
""".strip()

	exists = bool(frappe.db.exists("Report", REPORT_NAME))
	if exists:
		doc = frappe.get_doc("Report", REPORT_NAME)
	else:
		doc = frappe.get_doc(
			{
				"doctype": "Report",
				"report_name": REPORT_NAME,
				"name": REPORT_NAME,
				"ref_doctype": "MSP Site Device",
				"report_type": "Query Report",
				"module": "Ditech Site Docs",
				"is_standard": "No",
				"disabled": 0,
				"query": query,
			}
		)

	if getattr(doc, "is_standard", "No") != "Yes":
		doc.report_type = "Query Report"
		doc.ref_doctype = "MSP Site Device"
		doc.module = "Ditech Site Docs"
		doc.query = query

	# Avoid duplicating rows on repeated migrations.
	doc.roles = []
	doc.filters = []

	# Roles allowed to run the report.
	for role in (
		"System Manager",
		"Ditech Site Docs User",
		"Ditech Site Docs Manager",
		"Ditech Credentials Admin",
	):
		doc.append("roles", {"role": role})

	# Filters (like the Stock workspace / report style).
	doc.append("filters", {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer"})
	doc.append("filters", {"label": "Site", "fieldname": "site", "fieldtype": "Link", "options": "MSP Site"})
	doc.append("filters", {"label": "Room", "fieldname": "assigned_room", "fieldtype": "Link", "options": "MSP Room"})
	doc.append("filters", {"label": "User Email", "fieldname": "assigned_user_email", "fieldtype": "Data"})
	doc.append("filters", {"label": "Account Vendor", "fieldname": "account_vendor", "fieldtype": "Data"})
	doc.append("filters", {"label": "Item", "fieldname": "item", "fieldtype": "Data"})
	doc.append("filters", {"label": "Serial Number", "fieldname": "serial_number", "fieldtype": "Data"})
	doc.append("filters", {"label": "MAC", "fieldname": "mac", "fieldtype": "Data"})

	if exists:
		doc.save(ignore_permissions=True)
	else:
		doc.insert(ignore_permissions=True)


def ensure_number_card(
	*,
	name: str,
	document_type: str,
	filters: list[list] | None = None,
) -> None:
	exists = bool(frappe.db.exists("Number Card", name))
	if exists:
		doc = frappe.get_doc("Number Card", name)
	else:
		doc = frappe.get_doc({"doctype": "Number Card", "name": name})

	doc.label = name
	doc.type = "Document Type"
	doc.function = "Count"
	doc.document_type = document_type
	doc.is_public = 1
	doc.is_standard = 0
	doc.module = "Ditech Site Docs"
	doc.filters_json = json.dumps(filters or [])

	if exists:
		doc.save(ignore_permissions=True)
	else:
		doc.insert(ignore_permissions=True)


def ensure_site_docs_number_cards() -> None:
	ensure_number_card(name=CARD_SITES, document_type="MSP Site", filters=[["MSP Site", "is_archived", "=", 0]])
	ensure_number_card(name=CARD_DEVICES, document_type="MSP Site Device")
	ensure_number_card(name=CARD_ROOMS, document_type="MSP Room", filters=[["MSP Room", "is_archived", "=", 0]])
	ensure_number_card(name=CARD_ACCOUNTS, document_type="MSP Site Account")
	ensure_number_card(
		name=CARD_UNLINKED,
		document_type="MSP Site Device",
		filters=[["MSP Site Device", "site_account", "is", "not set"]],
	)


def ensure_site_docs_workspace() -> None:
	# Workspace with shortcuts + the combined report.
	ensure_site_docs_number_cards()

	content = [
		{"id": "sd-header", "type": "header", "data": {"text": "Ditech Site Docs", "col": 12}},
		{"id": "sd-sites-card", "type": "number_card", "data": {"number_card_name": CARD_SITES, "col": 3}},
		{"id": "sd-devices-card", "type": "number_card", "data": {"number_card_name": CARD_DEVICES, "col": 3}},
		{"id": "sd-rooms-card", "type": "number_card", "data": {"number_card_name": CARD_ROOMS, "col": 3}},
		{"id": "sd-accounts-card", "type": "number_card", "data": {"number_card_name": CARD_ACCOUNTS, "col": 3}},
		{"id": "sd-unlinked-card", "type": "number_card", "data": {"number_card_name": CARD_UNLINKED, "col": 3}},
		{
			"id": "sd-shortcuts",
			"type": "shortcut",
			"data": {
				"shortcut_name": "Site Docs Overview",
				"label": "Site Docs Overview",
				"type": "Report",
				"link_to": REPORT_NAME,
				"color": "blue",
				"icon": "chart",
				"col": 4,
			},
		},
		{
			"id": "sd-sites",
			"type": "shortcut",
			"data": {"shortcut_name": "Sites", "label": "Sites", "type": "DocType", "link_to": "MSP Site", "col": 4},
		},
		{
			"id": "sd-rooms",
			"type": "shortcut",
			"data": {"shortcut_name": "Rooms", "label": "Rooms", "type": "DocType", "link_to": "MSP Room", "col": 4},
		},
		{
			"id": "sd-devices",
			"type": "shortcut",
			"data": {
				"shortcut_name": "Devices",
				"label": "Devices",
				"type": "DocType",
				"link_to": "MSP Site Device",
				"col": 4,
			},
		},
		{
			"id": "sd-accounts",
			"type": "shortcut",
			"data": {
				"shortcut_name": "Accounts",
				"label": "Accounts",
				"type": "DocType",
				"link_to": "MSP Site Account",
				"col": 4,
			},
		},
	]

	exists = bool(frappe.db.exists("Workspace", WORKSPACE_NAME))
	if exists:
		ws = frappe.get_doc("Workspace", WORKSPACE_NAME)
	else:
		ws = frappe.get_doc({"doctype": "Workspace", "name": WORKSPACE_NAME, "title": WORKSPACE_NAME})

	ws.module = "Ditech Site Docs"
	ws.public = 1
	ws.content = json.dumps(content)
	ws.icon = "tool"
	ws.label = WORKSPACE_NAME

	if exists:
		ws.save(ignore_permissions=True)
	else:
		ws.insert(ignore_permissions=True)
