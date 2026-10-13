frappe.pages["wafd-administration-console"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("WAFD Administration Console"),
    single_column: true,
  });

  $(wrapper).find(".layout-main-section").html(`
    <div class="wafd-admin-console">
      <div class="alert alert-success">
        <strong>${__("Data protection is enabled")}</strong><br>
        ${__("Destructive reset is permanently disabled. Hotels, recipes, projects, financial records, and operational data will not be deleted from this console.")}
      </div>
      <div class="mb-3 d-flex gap-2 flex-wrap">
        <button class="btn btn-primary btn-sm wafd-refresh-summary">${__("Refresh summary")}</button>
        <button class="btn btn-default btn-sm wafd-install-master">${__("Install missing master data")}</button>
      </div>
      <div class="wafd-database-summary mb-4"></div>
      <div class="alert alert-info">
        ${__("Install Missing Master Data only creates records that do not already exist; it does not overwrite or delete user-entered hotels, recipes, ingredients, or transactions.")}
      </div>
    </div>
  `);

  const $root = $(wrapper).find(".wafd-admin-console");
  const escape = (value) => frappe.utils.escape_html(String(value ?? ""));

  function loadSummary() {
    const $summary = $root.find(".wafd-database-summary");
    $summary.html(`<div class="text-muted">${__("Loading...")}</div>`);
    frappe.call({
      method: "wafd_one.administration.get_database_summary",
      callback(r) {
        const data = r.message || {};
        const rows = Object.entries(data.counts || {})
          .filter(([, count]) => Number(count) > 0)
          .map(([doctype, count]) => `<tr><td>${escape(doctype)}</td><td class="text-end">${Number(count)}</td></tr>`)
          .join("");
        $summary.html(`
          <div class="mb-2"><strong>${__("Total records")}: ${Number(data.total || 0)}</strong></div>
          ${rows ? `<div class="table-responsive"><table class="table table-bordered table-sm"><thead><tr><th>${__("DocType")}</th><th>${__("Records")}</th></tr></thead><tbody>${rows}</tbody></table></div>` : `<div class="text-muted">${__("No WAFD records found.")}</div>`}
        `);
      },
    });
  }

  $root.on("click", ".wafd-refresh-summary", loadSummary);
  $root.on("click", ".wafd-install-master", () => {
    frappe.confirm(__("Install only missing WAFD ONE master data now? Existing records will not be changed or deleted."), () => {
      frappe.call({
        method: "wafd_one.administration.install_master_data",
        type: "POST",
        freeze: true,
        freeze_message: __("Installing missing master data..."),
        callback(r) {
          const data = r.message || {};
          frappe.msgprint({
            title: __("Master data checked"),
            indicator: "green",
            message: `${__("Created missing records")}: ${Number(data.created_total || 0)}<br>${__("Existing records were preserved.")}`,
          });
          loadSummary();
        },
      });
    });
  });

  loadSummary();
};
