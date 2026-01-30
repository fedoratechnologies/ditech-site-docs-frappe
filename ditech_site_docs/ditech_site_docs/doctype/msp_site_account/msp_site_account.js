frappe.ui.form.on("MSP Site Account", {
  refresh(frm) {
    frm.add_custom_button("Linked Devices", () => {
      frappe.set_route("List", "MSP Site Device", { site_account: frm.doc.name });
    });
  },
});

