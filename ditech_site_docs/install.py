from __future__ import annotations

import frappe


ROLES = [
	"Ditech Site Docs User",
	"Ditech Site Docs Manager",
	"Ditech Credentials Admin",
]


def after_install() -> None:
	ensure_roles()
	# DocType permissions are shipped in the DocType JSON and applied via migrate/reload-doc.


def after_migrate() -> None:
	# Keep roles present across deploys/upgrades.
	ensure_roles()


def ensure_roles() -> None:
	for role_name in ROLES:
		if frappe.db.exists("Role", role_name):
			continue
		role = frappe.get_doc({"doctype": "Role", "role_name": role_name})
		role.insert(ignore_permissions=True)


