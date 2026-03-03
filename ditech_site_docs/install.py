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
	ensure_custom_fields()


def after_migrate() -> None:
	"""Keep roles + stable custom fields consistent across GitOps deploys."""
	ensure_roles()
	ensure_custom_fields()


def ensure_roles() -> None:
	for role_name in ROLES:
		if frappe.db.exists("Role", role_name):
			continue
		role = frappe.get_doc({"doctype": "Role", "role_name": role_name})
		role.insert(ignore_permissions=True)


def ensure_custom_fields() -> None:
	"""Add stable, GitOps-managed fields needed for MSP workflows."""
	hd_ticket_fields = [
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
		{
			"fieldname": "insured_serial_no",
			"label": "Insured Serial No",
			"fieldtype": "Data",
			"insert_after": "msp_site_device",
		},
		{
			"fieldname": "insurance_deduction_amount",
			"label": "Insurance Deduction Amount",
			"fieldtype": "Currency",
			"insert_after": "insured_serial_no",
		},
		{
			"default": "0",
			"fieldname": "insurance_deducted",
			"label": "Insurance Deducted",
			"fieldtype": "Check",
			"insert_after": "insurance_deduction_amount",
			"read_only": 1,
		},
	]

	hd_customer_fields = [
		{
			"fieldname": "insurance_balance",
			"label": "Insurance Balance",
			"fieldtype": "Currency",
			"insert_after": "domain",
		},
	]

	create_custom_fields({"HD Ticket": hd_ticket_fields, "HD Customer": hd_customer_fields}, update=True)
