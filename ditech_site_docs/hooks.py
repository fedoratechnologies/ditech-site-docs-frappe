app_name = "ditech_site_docs"
app_title = "Ditech Site Docs"
app_publisher = "Ditech"
app_description = "Site documentation + inventory DocTypes for ERPNext (Ditech MSP use)"
app_email = "support@fedoratechnology.com"
app_license = "mit"

after_install = "ditech_site_docs.install.after_install"
after_migrate = "ditech_site_docs.install.after_migrate"

doc_events = {
	"HD Ticket": {
		"on_update": "ditech_site_docs.integrations.helpdesk.on_hd_ticket_update",
	},
}

scheduler_events = {
	"cron": {
		"0 */3 * * *": [
			"ditech_site_docs.integrations.google_admin.sync_all_enabled_workspaces",
		],
	},
}
