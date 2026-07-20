frappe.pages["wafd-administration-console"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("WAFD Administration Console"),
    single_column: true,
  });

  $(wrapper).find(".layout-main-section").html(`
    <div class="wafd-admin-console">
      <div class="alert alert-warning">
        <strong>${__("Restricted administration area")}</strong><br>
        ${__("Reset deletes WAFD ONE operational and reference records only. Users, roles, permissions and system settings are not deleted.")}
      </div>
      <div class="mb-3 d-flex gap-2 flex-wrap">
        <button class="btn btn-primary btn-sm wafd-refresh-summary">${__("Refresh summary")}</button>
        <button class="btn btn-default btn-sm wafd-install-master">${__("Install missing master data")}</button>
      </div>
      <div class="wafd-database-summary mb-4"></div>
      <div class="card">
        <div class="card-body">
          <h4>${__("Reset WAFD ONE data")}</h4>
          <p class="text-muted">${__("Type RESET WAFD ONE exactly to enable the reset action.")}</p>
          <div class="form-group">
            <input class="form-control wafd-confirmation" type="text" autocomplete="off" placeholder="RESET WAFD ONE">
          </div>
          <div class="checkbox mt-2 mb-3">
            <label><input class="wafd-reload-master" type="checkbox" checked> ${__("Reinstall reference master data after reset")}</label>
          </div>
          <button class="btn btn-danger btn-sm wafd-reset-database">${__("Reset WAFD ONE data")}</button>
        </div>
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
          loadSummary();
        },
      });
    });
  });

  $root.on("click", ".wafd-reset-database", () => {
    const confirmation = String($root.find(".wafd-confirmation").val() || "").trim();
    if (confirmation !== "RESET WAFD ONE") {
      frappe.msgprint(__("Type RESET WAFD ONE exactly before continuing."));
      return;
    }
    frappe.confirm(__("This will permanently delete all WAFD operational and reference records. Continue?"), () => {
      frappe.call({
        method: "wafd_one.administration.reset_demo_database",
        type: "POST",
        args: {
          confirmation,
          reload_master_data: $root.find(".wafd-reload-master").is(":checked") ? 1 : 0,
        },
        freeze: true,
        freeze_message: __("Resetting WAFD ONE data..."),
        callback(r) {
          const data = r.message || {};
          frappe.msgprint({
            title: __("Reset completed"),
            indicator: "green",
            message: `${__("Deleted records")}: ${Number(data.deleted_total || 0)}<br>${__("Created reference records")}: ${Number(data.created_total || 0)}`,
          });
          $root.find(".wafd-confirmation").val("");
          loadSummary();
        },
      });
    });
  });

  loadSummary();
};
