frappe.ui.form.on("WAFD Iftar Daily Operation", {
  refresh(frm) {
    if (frm.is_new()) return;
    if (!frm.doc.assigned_meals && frm.doc.planned_meals) frm.set_value('assigned_meals', frm.doc.planned_meals);
    const planned = Number(frm.doc.planned_meals || 0);
    const received = Number(frm.doc.received_meals || 0);
    frm.dashboard.add_indicator(__(`المخطط: ${planned}`), "blue");
    frm.dashboard.add_indicator(__(`المستلم: ${received}`), received >= planned && planned ? "green" : "orange");

    frm.add_custom_button(__("نموذج التسليم والاستلام"), () => {
      frappe.route_options = { print_format: "إفطار صائم — تسليم واستلام يومي" };
      frappe.set_route("print", frm.doctype, frm.doc.name);
    }, __("الطباعة / Print"));

    const advance = async (stage, success, extra = {}) => {
      const result = await frappe.call({
        method: "wafd_one.wafd_one.iftar_pro.update_daily_stage",
        args: { operation_name: frm.doc.name, stage, ...extra },
        freeze: true,
        freeze_message: __("جاري اعتماد المرحلة...")
      });
      frappe.show_alert({ message: success, indicator: "green" }, 4);
      await frm.reload_doc();
      if (stage === "received") {
        const next = result.message && result.message.next_operation;
        const nextBtn = next ? `<button type="button" class="btn btn-default wafd-next-day">فتح يوم التشغيل التالي</button>` : '';
        const d = new frappe.ui.Dialog({title: __("اكتمل التشغيل اليومي"), fields:[{fieldtype:'HTML', options:`<div class="alert alert-success">تم اعتماد الاستلام وإغلاق اليوم. اختر الخطوة التالية.</div><div style="display:flex;gap:8px;flex-wrap:wrap"><button type="button" class="btn btn-primary wafd-report-center">مركز التقارير والطباعة</button>${nextBtn}<button type="button" class="btn btn-default wafd-ops-dashboard">العودة للوحة التشغيل</button></div>`}]});
        d.show();
        d.$wrapper.on('click','.wafd-report-center',()=>{d.hide();frappe.route_options={project:frm.doc.project,operation:frm.doc.name};frappe.set_route('wafd-iftar-report-center');});
        d.$wrapper.on('click','.wafd-next-day',()=>{d.hide();frappe.set_route('Form','WAFD Iftar Daily Operation',next);});
        d.$wrapper.on('click','.wafd-ops-dashboard',()=>{d.hide();frappe.set_route('wafd-iftar-operations');});
      }
    };

    if (frm.doc.received_meals && frm.doc.docstatus !== 2) {
      frm.add_custom_button(__("إغلاق ميداني وتقرير"), () => {
        const d = new frappe.ui.Dialog({title:__('الإغلاق الميداني والتقرير اليومي'),fields:[
          {fieldname:'tables_spread_completed',fieldtype:'Check',label:__('تم فرش السفر'),default:frm.doc.tables_spread_completed||1},
          {fieldname:'cleanup_completed',fieldtype:'Check',label:__('تم رفع السفر والنفايات'),default:frm.doc.cleanup_completed||1},
          {fieldname:'preservation_society_quantity',fieldtype:'Int',label:__('المسلّم لجمعية حفظ النعمة'),default:frm.doc.preservation_society_quantity||0},
          {fieldname:'daily_report_sent',fieldtype:'Check',label:__('تم إرسال التقرير اليومي للجهة'),default:frm.doc.daily_report_sent||0},
          {fieldname:'media_links',fieldtype:'Long Text',label:__('روابط الصور والفيديو'),default:frm.doc.media_links||''}
        ],primary_action_label:__('حفظ الإغلاق'),async primary_action(v){d.hide();await frm.set_value(v);await frm.save();frappe.show_alert({message:__('تم حفظ الإغلاق الميداني'),indicator:'green'},4);}});d.show();
      }, __("التشغيل / Operations"));
    }

    if (frm.doc.docstatus !== 2) {
      if (!frm.doc.produced_meals) {
        frm.add_custom_button(__("اعتماد الإنتاج"), () => advance("produced", __("تم اعتماد الإنتاج"))).addClass("btn-primary");
      } else if (!frm.doc.packaged_meals) {
        frm.add_custom_button(__("اعتماد التغليف"), () => advance("packaged", __("تم اعتماد التغليف"))).addClass("btn-primary");
      } else if (!frm.doc.loaded_meals) {
        frm.add_custom_button(__("اعتماد التحميل"), () => advance("loaded", __("تم اعتماد التحميل"))).addClass("btn-primary");
      } else if (!frm.doc.authority_inspection_approved) {
        frm.add_custom_button(__("فحص مشرف التغذية"), () => {
          const q = new frappe.ui.Dialog({
            title: __("فحص مشرف التغذية من الجهة"),
            fields: [
              {fieldname:'authority_supervisor_name',fieldtype:'Data',label:__('اسم مشرف التغذية'),reqd:1,default:frm.doc.authority_supervisor_name},
              {fieldtype:'Section Break',label:__('العينة العشوائية')},
              {fieldname:'yogurt_checked',fieldtype:'Check',label:__('تم فحص الزبادي'),default:1},
              {fieldname:'bread_checked',fieldtype:'Check',label:__('تم فحص الخبز'),default:1},
              {fieldname:'dates_checked',fieldtype:'Check',label:__('تم فحص التمر'),default:1},
              {fieldname:'expiry_checked',fieldtype:'Check',label:__('تم فحص تواريخ الصلاحية'),default:1},
              {fieldname:'authority_inspection_notes',fieldtype:'Small Text',label:__('ملاحظات الفحص')}
            ],
            primary_action_label: __('اعتماد الفحص'),
            async primary_action(v){
              if(!v.yogurt_checked||!v.bread_checked||!v.dates_checked||!v.expiry_checked) return frappe.msgprint(__('يجب إكمال جميع عناصر الفحص قبل الاعتماد'));
              q.hide();
              await frm.set_value(v);
              await frm.set_value('authority_inspection_approved',1);
              await frm.save();
              frappe.show_alert({message:__('تم اعتماد فحص مشرف التغذية'),indicator:'green'},4);
              await frm.reload_doc();
            }
          }); q.show();
        }).addClass("btn-primary");
      } else if (!frm.doc.delivered_meals) {
        frm.add_custom_button(__("اعتماد التسليم"), () => advance("delivered", __("تم اعتماد التسليم"))).addClass("btn-primary");
      } else if (!frm.doc.received_meals) {
        frm.add_custom_button(__("اعتماد الاستلام"), () => {
          const dialog = new frappe.ui.Dialog({
            title: __("بيانات الاستلام"),
            size: "extra-large",
            fields: [
              { fieldname: "recipient_name", fieldtype: "Data", label: __("اسم المستلم"), reqd: 1, default: frm.doc.recipient_name },
              { fieldname: "recipient_id", fieldtype: "Data", label: __("رقم الهوية"), default: frm.doc.recipient_id },
              { fieldname: "table_owner_name", fieldtype: "Data", label: __("اسم صاحب السفرة"), reqd: 1, default: frm.doc.table_owner_name },
              { fieldname: "supervisor_name", fieldtype: "Data", label: __("اسم المشرف"), reqd: 1, default: frm.doc.supervisor_name },
              { fieldname: "supervisors_manager", fieldtype: "Data", label: __("مدير المشرفين"), default: frm.doc.supervisors_manager },
              { fieldname: "assigned_meals", fieldtype: "Int", label: __("عدد الوجبات المسلمة للمشرف"), reqd: 1, default: frm.doc.assigned_meals || frm.doc.planned_meals },
              { fieldtype: "Section Break", label: __("المساعدون — يمكنك إضافة من 1 إلى 100") },
              { fieldname: "assistants", fieldtype: "Table", label: __("حضور وغياب المساعدين"), in_place_edit: true,
                data: (frm.doc.assistants_attendance || []).map(r => ({assistant_name:r.assistant_name,mobile_no:r.mobile_no,attendance_status:r.attendance_status,check_in_time:r.check_in_time,check_out_time:r.check_out_time,notes:r.notes})),
                fields: [
                  {fieldname:'assistant_name',fieldtype:'Data',label:__('اسم المساعد'),in_list_view:1,reqd:1},
                  {fieldname:'mobile_no',fieldtype:'Data',label:__('الجوال'),in_list_view:1},
                  {fieldname:'attendance_status',fieldtype:'Select',label:__('الحالة'),options:'حاضر / Present\nغائب / Absent',default:'حاضر / Present',in_list_view:1},
                  {fieldname:'check_in_time',fieldtype:'Time',label:__('الحضور'),in_list_view:1},
                  {fieldname:'check_out_time',fieldtype:'Time',label:__('الانصراف'),in_list_view:1},
                  {fieldname:'notes',fieldtype:'Data',label:__('ملاحظات'),in_list_view:1}
                ] }
            ],
            primary_action_label: __("اعتماد الاستلام"),
            primary_action(values) {
              dialog.hide();
              advance("received", __("تم اعتماد الاستلام وإغلاق اليوم"), {...values, assistants: JSON.stringify(values.assistants || [])});
            }
          });
          dialog.show();
        }).addClass("btn-primary");
      }
    }
  }
});
