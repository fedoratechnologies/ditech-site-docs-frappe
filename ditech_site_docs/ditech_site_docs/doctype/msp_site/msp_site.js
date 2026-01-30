frappe.ui.form.on("MSP Site", {
  refresh(frm) {
    frm.add_custom_button("Devices", () => {
      frappe.set_route("List", "MSP Site Device", { site: frm.doc.name });
    });
    frm.add_custom_button("Accounts", () => {
      frappe.set_route("List", "MSP Site Account", { site: frm.doc.name });
    });
  },
});

