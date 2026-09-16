frappe.ui.form.on("WAFD Administration Console", {
  refresh(frm) {
    frm.disable_save();
    frm.trigger("load_summary");
    frm.trigger("load_go_live_status");
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

  load_go_live_status(frm) {
    const field = frm.get_field("go_live_inventory_status");
    frappe.call({
      method: "wafd_one.administration.preview_go_live_inventory_reset",
      callback(r) {
        const d = r.message || {};
        const prepared = Number(d.already_prepared || 0) === 1;
        const html = prepared
          ? `<div class="alert alert-success mb-2">${__("تمت تهيئة مخزون الاختبار للتشغيل الفعلي. لا يمكن تشغيل العملية مرة ثانية.")}</div>`
          : `<div class="alert alert-warning mb-2"><b>${__("قبل التشغيل الفعلي فقط")}</b><br>${__("سيتم تصفير الكميات الحالية وأرشفة حركات الاختبار مع الاحتفاظ بالمواد والوصفات والمستودعات والثلاجات والمشاريع.")}<br>${__("أرصدة غير صفرية")}: ${Number(d.nonzero_balance_count||0)} — ${__("حركات اختبار")}: ${Number(d.movement_count||0)}</div>`;
        if (field && field.$wrapper) field.$wrapper.html(html);
        frm.toggle_enable("prepare_go_live_inventory", !prepared);
      }
    });
  },

  preview_go_live_inventory(frm) {
    frappe.call({
      method: "wafd_one.administration.preview_go_live_inventory_reset",
      callback(r) {
        const d = r.message || {};
        frappe.msgprint({
          title: __("معاينة تهيئة المخزون"),
          indicator: d.already_prepared ? "green" : "orange",
          message: `${__("أرصدة المخزون")}: ${Number(d.balance_count||0)}<br>${__("أرصدة غير صفرية")}: ${Number(d.nonzero_balance_count||0)}<br>${__("حركات المخزون")}: ${Number(d.movement_count||0)}<br>${__("قيمة المخزون الحالية")}: ${format_currency(Number(d.stock_value||0))}`
        });
      }
    });
  },

  prepare_go_live_inventory(frm) {
    frappe.call({ method: "wafd_one.administration.preview_go_live_inventory_reset", callback(r) {
      const d = r.message || {};
      if (d.already_prepared) { frm.trigger("load_go_live_status"); return; }
      frappe.prompt([
        {fieldname:"confirmation", fieldtype:"Data", label:__("اكتب عبارة التأكيد"), reqd:1, description:d.confirmation_phrase}
      ], values => {
        frappe.call({
          method:"wafd_one.administration.prepare_inventory_for_go_live",
          type:"POST",
          args:{confirmation:values.confirmation},
          freeze:true,
          freeze_message:__("تهيئة المخزون للتشغيل الفعلي..."),
          callback(res){
            const out=res.message||{};
            frappe.msgprint({title:__("تمت تهيئة المخزون"),indicator:"green",message:`${__("تم حفظ لقطة مراجعة")}: ${frappe.utils.escape_html(out.snapshot||"")}<br>${__("تم تصفير الأرصدة")}: ${Number(out.balances_reset||0)}<br>${__("تم أرشفة حركات الاختبار")}: ${Number(out.movements_archived||0)}`});
            frm.reload_doc();
          }
        });
      }, __("تأكيد التشغيل الفعلي"), __("تنفيذ"));
    }});
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
