from __future__ import annotations

import frappe


ROLES = [
	"Ditech Site Docs User",
	"Ditech Site Docs Manager",
	"Ditech Credentials Admin",
]


def after_install() -> None:
	ensure_roles()
	ensure_doctype_permissions()


def ensure_roles() -> None:
	for role_name in ROLES:
		if frappe.db.exists("Role", role_name):
			continue
		role = frappe.get_doc({"doctype": "Role", "role_name": role_name})
		role.insert(ignore_permissions=True)


def _set_perms(doctype: str, permissions: list[dict]) -> None:
	dt = frappe.get_doc("DocType", doctype)
	dt.permissions = []
	for p in permissions:
		dt.append("permissions", p)
	dt.save(ignore_permissions=True)
	frappe.clear_cache(doctype=doctype)


def ensure_doctype_permissions() -> None:
	_set_perms(
		"MSP Site",
		[
			{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "export": 1, "print": 1},
			{"role": "Ditech Site Docs User", "read": 1, "export": 1, "print": 1},
			{"role": "Ditech Site Docs Manager", "read": 1, "write": 1, "create": 1, "export": 1, "print": 1},
		],
	)

	_set_perms(
		"MSP Site Device",
		[
			{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "export": 1, "print": 1},
			{"role": "Ditech Site Docs User", "read": 1, "export": 1, "print": 1},
			{"role": "Ditech Site Docs Manager", "read": 1, "write": 1, "create": 1, "export": 1, "print": 1},
		],
	)

	_set_perms(
		"MSP Site Account",
		[
			{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "export": 1, "print": 1},
			{"role": "Ditech Credentials Admin", "read": 1, "write": 1, "create": 1, "export": 1, "print": 1},
		],
	)

