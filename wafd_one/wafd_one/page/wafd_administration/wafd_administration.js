frappe.pages["wafd-administration"].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("WAFD Administration"),
        single_column: true,
    });

    const $body = $(page.body);
    $body.html(`
        <div class="wafd-admin" style="max-width:980px;padding:18px 4px;">
            <div class="alert alert-warning">
                <strong>${__("Restricted administration area")}</strong><br>
                ${__("Reset deletes WAFD operational and reference records only. Users, roles, permissions, DocTypes and system settings remain untouched.")}
            </div>
            <div class="card mb-4"><div class="card-body">
                <h4>${__("Current database summary")}</h4>
                <p class="text-muted">${__("Review the number of records before taking any destructive action.")}</p>
                <button class="btn btn-default btn-refresh-summary">${__("Refresh summary")}</button>
                <div class="wafd-summary mt-3">${__("Loading...")}</div>
            </div></div>

            <div class="card mb-4"><div class="card-body">
                <h4>${__("Reset Demo Database")}</h4>
                <p>${__("Deletes all WAFD transactions and master records, resolves circular links, then reinstalls missions, hotels, recipes, ingredients, warehouses, suppliers and opening balances.")}</p>
                <label class="control-label">${__("Type the confirmation phrase")}: <code>RESET WAFD ONE</code></label>
                <input class="form-control wafd-confirmation" autocomplete="off" placeholder="RESET WAFD ONE">
                <div class="mt-3">
                    <label><input type="checkbox" class="wafd-reload-master" checked> ${__("Reinstall master data immediately after reset")}</label>
                </div>
                <button class="btn btn-danger btn-reset mt-3">${__("Reset WAFD ONE data")}</button>
            </div></div>

            <div class="card"><div class="card-body">
                <h4>${__("Install Master Data")}</h4>
                <p>${__("Adds only missing reference records. Existing operations and user-entered records are not deleted or overwritten.")}</p>
                <button class="btn btn-primary btn-install-master">${__("Install missing master data")}</button>
            </div></div>
        </div>
    `);

    const refreshSummary = () => {
        $body.find(".wafd-summary").html(__("Loading..."));
        frappe.call({
            method: "wafd_one.administration.get_database_summary",
            callback: (r) => {
                const data = r.message || {};
                const rows = Object.entries(data.counts || {})
                    .filter(([, count]) => count > 0)
                    .map(([doctype, count]) => `<tr><td>${frappe.utils.escape_html(doctype)}</td><td class="text-end">${count}</td></tr>`)
                    .join("");
                $body.find(".wafd-summary").html(`
                    <div class="mb-2"><strong>${__("Total records")}: ${data.total || 0}</strong></div>
                    ${rows ? `<div class="table-responsive"><table class="table table-bordered table-sm"><thead><tr><th>${__("DocType")}</th><th>${__("Records")}</th></tr></thead><tbody>${rows}</tbody></table></div>` : `<div class="text-muted">${__("No WAFD records found.")}</div>`}
                `);
            },
        });
    };

    $body.on("click", ".btn-refresh-summary", refreshSummary);

    $body.on("click", ".btn-reset", () => {
        const confirmation = $body.find(".wafd-confirmation").val().trim();
        if (confirmation !== "RESET WAFD ONE") {
            frappe.msgprint(__("Type RESET WAFD ONE exactly before continuing."));
            return;
        }
        frappe.confirm(
            __("This will permanently delete all WAFD operational and reference records. Continue?"),
            () => {
                frappe.dom.freeze(__("Resetting WAFD ONE data..."));
                frappe.call({
                    method: "wafd_one.administration.reset_demo_database",
                    type: "POST",
                    args: {
                        confirmation,
                        reload_master_data: $body.find(".wafd-reload-master").is(":checked") ? 1 : 0,
                    },
                    callback: (r) => {
                        const data = r.message || {};
                        frappe.msgprint({
                            title: __("Reset completed"),
                            indicator: "green",
                            message: `${__("Deleted records")}: ${data.deleted_total || 0}<br>${__("Created reference records")}: ${data.created_total || 0}`,
                        });
                        $body.find(".wafd-confirmation").val("");
                        refreshSummary();
                    },
                    always: () => frappe.dom.unfreeze(),
                });
            }
        );
    });

    $body.on("click", ".btn-install-master", () => {
        frappe.confirm(__("Install all missing WAFD ONE master data now?"), () => {
            frappe.dom.freeze(__("Installing master data..."));
            frappe.call({
                method: "wafd_one.administration.install_master_data",
                type: "POST",
                callback: (r) => {
                    const data = r.message || {};
                    frappe.msgprint({
                        title: __("Master data installed"),
                        indicator: "green",
                        message: `${__("Created records")}: ${data.created_total || 0}`,
                    });
                    refreshSummary();
                },
                always: () => frappe.dom.unfreeze(),
            });
        });
    });

    refreshSummary();
};
