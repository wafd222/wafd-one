frappe.ui.form.on("WAFD Administration Console", {
  refresh(frm) {
    frm.disable_save();
    frm.trigger("load_summary");
  },

  refresh_summary(frm) {
    frm.trigger("load_summary");
  },

  load_summary(frm) {
    const field = frm.get_field("database_summary");
    if (field && field.$wrapper) {
      field.$wrapper.html(`<div class="text-muted">${__("Loading...")}</div>`);
    }

    frappe.call({
      method: "wafd_one.administration.get_database_summary",
      callback(r) {
        const data = r.message || {};
        const rows = Object.entries(data.counts || {})
          .filter(([, count]) => Number(count) > 0)
          .map(([doctype, count]) => `<tr><td>${frappe.utils.escape_html(doctype)}</td><td class="text-end">${Number(count)}</td></tr>`)
          .join("");
        const html = `
          <div class="mb-2"><strong>${__("Total records")}: ${Number(data.total || 0)}</strong></div>
          ${rows ? `<div class="table-responsive"><table class="table table-bordered table-sm"><thead><tr><th>${__("DocType")}</th><th>${__("Records")}</th></tr></thead><tbody>${rows}</tbody></table></div>` : `<div class="text-muted">${__("No WAFD records found.")}</div>`}
        `;
        if (field && field.$wrapper) field.$wrapper.html(html);
      },
    });
  },

  install_master_data(frm) {
    frappe.confirm(__("Install all missing WAFD ONE master data now?"), () => {
      frappe.call({
        method: "wafd_one.administration.install_master_data",
        type: "POST",
        freeze: true,
        freeze_message: __("Installing master data..."),
        callback(r) {
          const data = r.message || {};
          frappe.msgprint({
            title: __("Master data installed"),
            indicator: "green",
            message: `${__("Created records")}: ${Number(data.created_total || 0)}`,
          });
          frm.trigger("load_summary");
        },
      });
    });
  },

  reset_database() {
    frappe.msgprint({
      title: __("Protected operation"),
      indicator: "orange",
      message: __("Data reset is disabled. This button never deletes hotels, recipes, projects, or operational records. Use Install Missing Master Data to add only missing reference records."),
    });
  },
});
