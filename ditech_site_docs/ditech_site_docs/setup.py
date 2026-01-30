from __future__ import annotations

import json

import frappe


REPORT_NAME = "Site Docs Overview"
WORKSPACE_NAME = "Ditech Site Docs"


def ensure_site_docs_report() -> None:
	# Query Report: combined view of Site + Device + linked Account (vendor/system).
	query = """
SELECT
  s.name AS site,
  s.site_name AS site_name,
  d.name AS device,
  d.item AS item,
  d.section AS section,
  d.location AS location,
  d.model AS model,
  d.serial_number AS serial_number,
  d.mac AS mac,
  d.lan1_ip AS lan1_ip,
  d.wan_ip AS wan_ip,
  d.site_account AS site_account,
  a.vendor AS account_vendor
FROM `tabMSP Site Device` d
JOIN `tabMSP Site` s ON s.name = d.site
LEFT JOIN `tabMSP Site Account` a ON a.name = d.site_account
WHERE 1=1
  AND (%(site)s IS NULL OR %(site)s = '' OR d.site = %(site)s)
  AND (%(account_vendor)s IS NULL OR %(account_vendor)s = '' OR a.vendor LIKE CONCAT('%%', %(account_vendor)s, '%%'))
  AND (%(item)s IS NULL OR %(item)s = '' OR d.item LIKE CONCAT('%%', %(item)s, '%%'))
  AND (%(serial_number)s IS NULL OR %(serial_number)s = '' OR d.serial_number LIKE CONCAT('%%', %(serial_number)s, '%%'))
  AND (%(mac)s IS NULL OR %(mac)s = '' OR d.mac LIKE CONCAT('%%', %(mac)s, '%%'))
ORDER BY s.site_name, d.item, d.serial_number
""".strip()

	if frappe.db.exists("Report", REPORT_NAME):
		doc = frappe.get_doc("Report", REPORT_NAME)
		if getattr(doc, "is_standard", "No") != "Yes":
			doc.report_type = "Query Report"
			doc.ref_doctype = "MSP Site Device"
			doc.module = "Ditech Site Docs"
			doc.query = query
			doc.filters = []
			doc.roles = []
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

	# Roles allowed to run the report.
	for role in (
		"System Manager",
		"Ditech Site Docs User",
		"Ditech Site Docs Manager",
		"Ditech Credentials Admin",
	):
		doc.append("roles", {"role": role})

	# Filters (like the Stock workspace / report style).
	doc.append("filters", {"label": "Site", "fieldname": "site", "fieldtype": "Link", "options": "MSP Site"})
	doc.append("filters", {"label": "Account Vendor", "fieldname": "account_vendor", "fieldtype": "Data"})
	doc.append("filters", {"label": "Item", "fieldname": "item", "fieldtype": "Data"})
	doc.append("filters", {"label": "Serial Number", "fieldname": "serial_number", "fieldtype": "Data"})
	doc.append("filters", {"label": "MAC", "fieldname": "mac", "fieldtype": "Data"})

	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)


def ensure_site_docs_workspace() -> None:
	# Workspace with shortcuts + the combined report.
	content = [
		{"id": "sd-header", "type": "header", "data": {"text": "Ditech Site Docs", "col": 12}},
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

	if frappe.db.exists("Workspace", WORKSPACE_NAME):
		ws = frappe.get_doc("Workspace", WORKSPACE_NAME)
	else:
		ws = frappe.get_doc({"doctype": "Workspace", "name": WORKSPACE_NAME, "title": WORKSPACE_NAME})

	ws.module = "Ditech Site Docs"
	ws.public = 1
	ws.content = json.dumps(content)
	ws.icon = "tool"
	ws.label = WORKSPACE_NAME

	if ws.is_new():
		ws.insert(ignore_permissions=True)
	else:
		ws.save(ignore_permissions=True)

