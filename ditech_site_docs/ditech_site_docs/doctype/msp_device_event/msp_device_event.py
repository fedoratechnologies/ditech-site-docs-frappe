from __future__ import annotations

import frappe
from frappe.model.document import Document


class MSPDeviceEvent(Document):
	def validate(self) -> None:
		if not self.event_at:
			self.event_at = frappe.utils.now()

