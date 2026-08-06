frappe.ui.form.on("WAFD Iftar Daily Operation", {
  refresh(frm) {
    if (frm.is_new()) return;
    const planned = Number(frm.doc.planned_meals || 0);
    const received = Number(frm.doc.received_meals || 0);
    frm.dashboard.add_indicator(__(`المخطط: ${planned}`), "blue");
    frm.dashboard.add_indicator(__(`المستلم: ${received}`), received >= planned && planned ? "green" : "orange");

    frm.add_custom_button(__("نموذج التسليم والاستلام"), () => {
      frappe.set_route("print", frm.doctype, frm.doc.name, { print_format: "إفطار صائم — تسليم واستلام يومي" });
    }, __("الطباعة / Print"));

    const advance = async (stage, success, extra = {}) => {
      await frappe.call({
        method: "wafd_one.wafd_one.iftar_pro.update_daily_stage",
        args: { operation_name: frm.doc.name, stage, ...extra },
        freeze: true,
        freeze_message: __("جاري اعتماد المرحلة...")
      });
      frappe.show_alert({ message: success, indicator: "green" }, 4);
      await frm.reload_doc();
      if (stage === "received") {
        frappe.msgprint({
          title: __("اكتمل التشغيل اليومي"),
          indicator: "green",
          message: __("تم اعتماد الاستلام وإغلاق اليوم بنجاح. ستبقى في هذه الشاشة ويمكنك الطباعة أو المراجعة.")
        });
      }
    };

    if (frm.doc.docstatus !== 2) {
      if (!frm.doc.produced_meals) {
        frm.add_custom_button(__("اعتماد الإنتاج"), () => advance("produced", __("تم اعتماد الإنتاج"))).addClass("btn-primary");
      } else if (!frm.doc.packaged_meals) {
        frm.add_custom_button(__("اعتماد التغليف"), () => advance("packaged", __("تم اعتماد التغليف"))).addClass("btn-primary");
      } else if (!frm.doc.loaded_meals) {
        frm.add_custom_button(__("اعتماد التحميل"), () => advance("loaded", __("تم اعتماد التحميل"))).addClass("btn-primary");
      } else if (!frm.doc.delivered_meals) {
        frm.add_custom_button(__("اعتماد التسليم"), () => advance("delivered", __("تم اعتماد التسليم"))).addClass("btn-primary");
      } else if (!frm.doc.received_meals) {
        frm.add_custom_button(__("اعتماد الاستلام"), () => {
          const dialog = new frappe.ui.Dialog({
            title: __("بيانات الاستلام"),
            fields: [
              { fieldname: "recipient_name", fieldtype: "Data", label: __("اسم المستلم"), reqd: 1, default: frm.doc.recipient_name },
              { fieldname: "recipient_id", fieldtype: "Data", label: __("رقم الهوية"), default: frm.doc.recipient_id }
            ],
            primary_action_label: __("اعتماد الاستلام"),
            primary_action(values) {
              dialog.hide();
              advance("received", __("تم اعتماد الاستلام وإغلاق اليوم"), values);
            }
          });
          dialog.show();
        }).addClass("btn-primary");
      }
    }
  }
});
