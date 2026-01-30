frappe.ui.form.on("MSP Site Device", {
  refresh(frm) {
    frm.set_query("site_account", () => {
      if (!frm.doc.site) return {};
      return { filters: { site: frm.doc.site } };
    });
  },
  site(frm) {
    if (!frm.doc.site_account) return;
    // If the site changes, force re-selection so the link constraint is respected.
    frm.set_value("site_account", null);
  },
});

