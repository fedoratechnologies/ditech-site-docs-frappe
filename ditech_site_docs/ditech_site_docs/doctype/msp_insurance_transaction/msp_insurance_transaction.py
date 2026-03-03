from __future__ import annotations

import frappe
from frappe.model.document import Document


class MSPInsuranceTransaction(Document):
	def validate(self) -> None:
		if not self.posting_datetime:
			self.posting_datetime = frappe.utils.now()

		self._validate_amount()
		self._validate_ticket_deduction_idempotency()

	def _validate_amount(self) -> None:
		if self.amount is None:
			return
		if float(self.amount) == 0:
			frappe.throw("Insurance transaction amount cannot be 0.")

	def _validate_ticket_deduction_idempotency(self) -> None:
		if not (self.ticket and self.transaction_type == "Deduction"):
			return

		duplicate = frappe.db.exists(
			"MSP Insurance Transaction",
			{
				"ticket": self.ticket,
				"transaction_type": "Deduction",
				"docstatus": ("!=", 2),
				"name": ("!=", self.name),
			},
		)
		if duplicate:
			frappe.throw("A deduction transaction already exists for this ticket.")

