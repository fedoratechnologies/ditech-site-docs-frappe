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

		# If the user filled one of the assignment fields directly, infer the type.
		if not self.assigned_to_type:
			if self.assigned_room:
				self.assigned_to_type = "Room"
			elif self.assigned_user_email:
				self.assigned_to_type = "User"

		# Enforce mutually exclusive assignment.
		if self.assigned_room and self.assigned_user_email:
			frappe.throw("Choose either a Room or a User Email (not both).")

		if self.assigned_to_type == "Room":
			if not self.assigned_room:
				frappe.throw("Room is required when Assigned To is Room.")
			if self.assigned_user_email:
				frappe.throw("User Email must be empty when Assigned To is Room.")
			if self.site:
				room_site = frappe.db.get_value("MSP Room", self.assigned_room, "site")
				if room_site and room_site != self.site:
					frappe.throw("Selected Room must belong to the same Site.")
		elif self.assigned_to_type == "User":
			if not self.assigned_user_email:
				frappe.throw("User Email is required when Assigned To is User.")
			if self.assigned_room:
				frappe.throw("Room must be empty when Assigned To is User.")
		else:
			# No assignment.
			self.assigned_room = None
			self.assigned_user_email = None
