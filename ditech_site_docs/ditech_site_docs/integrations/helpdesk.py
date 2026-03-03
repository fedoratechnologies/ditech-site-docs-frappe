from __future__ import annotations

import frappe


RESOLVED_STATUS_CATEGORIES = {"Closed", "Resolved"}
RESOLVED_STATUSES = {"Resolved", "Closed", "Done"}


def on_hd_ticket_update(doc: frappe.model.document.Document, method: str | None = None) -> None:  # noqa: ARG001
	"""Helpdesk hooks for DiTech MSP workflows.

	- Auto-deduct insurance from the annual coverage pool when a ticket is resolved.
	- Write a device event entry for audit/lifecycle history.
	"""
	try:
		_handle_insurance_deduction(doc)
	except Exception:
		frappe.log_error(title="DiTech: insurance auto-deduction failed", message=frappe.get_traceback())


def _handle_insurance_deduction(ticket: frappe.model.document.Document) -> None:
	amount = float(ticket.get("insurance_deduction_amount") or 0)
	if amount <= 0:
		return

	if ticket.get("insurance_deducted"):
		return

	if frappe.db.exists(
		"MSP Insurance Transaction",
		{"ticket": ticket.name, "transaction_type": "Deduction", "docstatus": ("!=", 2)},
	):
		frappe.db.set_value("HD Ticket", ticket.name, "insurance_deducted", 1, update_modified=False)
		return

	if not _is_ticket_resolved(ticket):
		return

	site, device = _resolve_site_and_device(ticket)
	if not site:
		return

	policy = _find_active_policy(site, on_datetime=ticket.get("resolution_date") or ticket.get("modified"))
	if not policy:
		return

	deduction = -abs(amount)
	_txn = frappe.get_doc(
		{
			"doctype": "MSP Insurance Transaction",
			"policy": policy,
			"ticket": ticket.name,
			"device": device,
			"transaction_type": "Deduction",
			"amount": deduction,
			"description": f"Auto-deduction from ticket {ticket.name}",
			"is_auto": 1,
		}
	)
	_txn.insert(ignore_permissions=True)
	_txn.submit()

	frappe.db.set_value("HD Ticket", ticket.name, "insurance_deducted", 1, update_modified=False)

	if ticket.get("customer"):
		_apply_hd_customer_balance_deduction(ticket.customer, abs(amount))

	if device:
		_create_device_event(
			site=site,
			device=device,
			ticket=ticket.name,
			event_type="Ticket Resolved",
			details=f"Insurance deducted {abs(amount)} {frappe.db.get_value('MSP Insurance Policy', policy, 'currency') or ''}".strip(),
		)


def _is_ticket_resolved(ticket: frappe.model.document.Document) -> bool:
	status = (ticket.get("status") or "").strip()
	status_category = (ticket.get("status_category") or "").strip()
	if status in RESOLVED_STATUSES:
		return True
	if status_category and status_category in RESOLVED_STATUS_CATEGORIES:
		return True
	if ticket.get("resolution_date"):
		return True
	return False


def _resolve_site_and_device(ticket: frappe.model.document.Document) -> tuple[str | None, str | None]:
	if ticket.get("msp_site_device"):
		row = frappe.db.get_value(
			"MSP Site Device",
			ticket.msp_site_device,
			["name", "site"],
			as_dict=True,
		)
		if row and row.get("site") and row.get("name"):
			return row.site, row.name

	if ticket.get("msp_site"):
		return ticket.msp_site, None

	serial = ticket.get("insured_serial_no")
	if serial:
		row = frappe.db.get_value(
			"MSP Site Device",
			{"serial_number": serial},
			["name", "site"],
			as_dict=True,
		)
		if row and row.get("site") and row.get("name"):
			return row.site, row.name

	if ticket.get("customer"):
		site = frappe.db.get_value("MSP Site", {"hd_customer": ticket.customer}, "name")
		if site:
			return site, None

	return None, None


def _find_active_policy(site: str, on_datetime: str | None = None) -> str | None:
	policies = frappe.get_all(
		"MSP Insurance Policy",
		filters={"site": site, "is_archived": 0},
		fields=["name", "start_date", "end_date"],
		order_by="start_date desc, modified desc",
		limit_page_length=25,
	)
	if not policies:
		return None

	if not on_datetime:
		return policies[0].name

	on_date = frappe.utils.getdate(on_datetime)
	for p in policies:
		start = frappe.utils.getdate(p.start_date) if p.start_date else None
		end = frappe.utils.getdate(p.end_date) if p.end_date else None

		if start and end and start <= on_date <= end:
			return p.name
		if start and not end and start <= on_date:
			return p.name
		if end and not start and on_date <= end:
			return p.name

	return policies[0].name


def _apply_hd_customer_balance_deduction(hd_customer: str, deduction: float) -> None:
	balance = frappe.db.get_value("HD Customer", hd_customer, "insurance_balance")
	if balance is None:
		return
	try:
		new_balance = float(balance) - float(deduction)
	except Exception:
		return
	frappe.db.set_value("HD Customer", hd_customer, "insurance_balance", new_balance, update_modified=False)


def _create_device_event(
	site: str,
	device: str,
	ticket: str | None,
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
			"ticket": ticket,
			"source_system": "Helpdesk",
			"event_type": event_type,
			"details": details,
			"old_value": old_value,
			"new_value": new_value,
		}
	)
	event.insert(ignore_permissions=True)
