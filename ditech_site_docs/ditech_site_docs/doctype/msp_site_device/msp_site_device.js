frappe.ui.form.on("MSP Site Device", {
  refresh(frm) {
    frm.set_query("site_account", () => {
      if (!frm.doc.site) return {};
      return { filters: { site: frm.doc.site } };
    });

    frm.set_query("assigned_room", () => {
      if (!frm.doc.site) return {};
      return { filters: { site: frm.doc.site } };
    });
  },
  site(frm) {
    // If the site changes, force re-selection so the link constraints are respected.
    if (frm.doc.site_account) frm.set_value("site_account", null);
    if (frm.doc.assigned_room) frm.set_value("assigned_room", null);
  },

  assigned_to_type(frm) {
    if (frm.doc.assigned_to_type === "Room") {
      if (frm.doc.assigned_user_email) frm.set_value("assigned_user_email", null);
      return;
    }
    if (frm.doc.assigned_to_type === "User") {
      if (frm.doc.assigned_room) frm.set_value("assigned_room", null);
      return;
    }
    // Cleared
    if (frm.doc.assigned_room) frm.set_value("assigned_room", null);
    if (frm.doc.assigned_user_email) frm.set_value("assigned_user_email", null);
  },

  assigned_room(frm) {
    if (frm.doc.assigned_room && !frm.doc.assigned_to_type) {
      frm.set_value("assigned_to_type", "Room");
    }
  },

  assigned_user_email(frm) {
    if (frm.doc.assigned_user_email && !frm.doc.assigned_to_type) {
      frm.set_value("assigned_to_type", "User");
    }
  },
});
