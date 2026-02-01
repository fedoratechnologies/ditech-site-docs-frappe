frappe.ui.form.on("MSP Room", {
  refresh(frm) {
    frm.add_custom_button("Devices", () => {
      frappe.set_route("List", "MSP Site Device", { assigned_room: frm.doc.name });
    });
  },
});

