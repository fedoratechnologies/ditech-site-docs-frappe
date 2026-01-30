from __future__ import annotations


def get_data():
	return {
		"fieldname": "site_account",
		"non_standard_fieldnames": {"MSP Site Device": "site_account"},
		"transactions": [
			{"label": "Linked", "items": ["MSP Site Device"]},
		],
	}

