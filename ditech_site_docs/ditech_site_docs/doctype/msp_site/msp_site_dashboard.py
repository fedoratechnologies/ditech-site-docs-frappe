from __future__ import annotations


def get_data():
	return {
		"fieldname": "site",
		"non_standard_fieldnames": {"MSP Site Account": "site", "MSP Site Device": "site"},
		"transactions": [
			{"label": "Site Docs", "items": ["MSP Site Device", "MSP Site Account"]},
		],
	}

