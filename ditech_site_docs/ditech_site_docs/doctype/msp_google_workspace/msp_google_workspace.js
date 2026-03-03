frappe.ui.form.on("MSP Google Workspace", {
	refresh(frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(__("Sync Now"), async () => {
			await frappe.call({
				method: "ditech_site_docs.ditech_site_docs.integrations.google_admin.enqueue_sync_workspace",
				args: { workspace_name: frm.doc.name },
				freeze: true,
				freeze_message: __("Queuing sync..."),
			});
			frappe.show_alert({ message: __("Sync queued"), indicator: "green" });
		});
	},
});
