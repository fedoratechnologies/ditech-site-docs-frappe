from __future__ import annotations

import frappe
from frappe.model.document import Document


class MSPSiteUser(Document):
	def validate(self) -> None:
		if not (self.site and self.email):
			return

		duplicate = frappe.db.exists(
			"MSP Site User",
			{"site": self.site, "email": self.email, "name": ("!=", self.name)},
		)
		if duplicate:
			frappe.throw("A user with this email already exists for this site.")

