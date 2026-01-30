from __future__ import annotations

import frappe
from frappe.model.document import Document


class MSPSiteDevice(Document):
	def validate(self):
		# Ensure any linked account belongs to the same site.
		if self.site_account and self.site:
			account_site = frappe.db.get_value("MSP Site Account", self.site_account, "site")
			if account_site and account_site != self.site:
				frappe.throw("Selected Site Account must belong to the same Site.")
	pass
