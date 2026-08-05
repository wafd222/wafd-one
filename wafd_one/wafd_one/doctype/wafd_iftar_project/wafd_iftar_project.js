frappe.ui.form.on("WAFD Iftar Project", {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.docstatus === 0) {
            frm.add_custom_button(__("تحميل المكونات الأساسية / Load Standard Components"), async () => {
                if (frm.is_dirty()) await frm.save();
                await frappe.call({
                    method: "wafd_one.wafd_one.doctype.wafd_iftar_project.wafd_iftar_project.load_standard_components",
                    args: { project_name: frm.doc.name }, freeze: true
                });
                await frm.reload_doc();
            }, __("إفطار الصائم / Iftar"));

            frm.add_custom_button(__("تحميل تكاليف التشغيل / Load Operating Costs"), async () => {
                if (frm.is_dirty()) await frm.save();
                await frappe.call({
                    method: "wafd_one.wafd_one.doctype.wafd_iftar_project.wafd_iftar_project.load_standard_operating_costs",
                    args: { project_name: frm.doc.name }, freeze: true
                });
                await frm.reload_doc();
            }, __("إفطار الصائم / Iftar"));

            frm.add_custom_button(__("إنشاء خطة الكراتين / Generate Cartons"), async () => {
                if (frm.is_dirty()) await frm.save();
                const r = await frappe.call({
                    method: "wafd_one.wafd_one.doctype.wafd_iftar_project.wafd_iftar_project.generate_cartons",
                    args: { project_name: frm.doc.name }, freeze: true
                });
                frappe.show_alert({message: __(`تم إنشاء ${r.message.carton_count} كرتون`), indicator: "green"}, 6);
                await frm.reload_doc();
            }, __("إفطار الصائم / Iftar"));
        }
        if (!frm.is_new()) {
            frm.dashboard.add_indicator(__(`إجمالي الوجبات: ${frm.doc.total_meals || 0}`), "blue");
            frm.dashboard.add_indicator(__(`خطة التوزيع: ${frm.doc.planned_distribution_meals || 0}`), "blue");
            frm.dashboard.add_indicator(__(`التكلفة/وجبة: ${format_currency(frm.doc.actual_cost_per_meal || 0)}`), "orange");
            frm.dashboard.add_indicator(__(`الربح المتوقع: ${format_currency(frm.doc.expected_profit || 0)}`), (frm.doc.expected_profit || 0) >= 0 ? "green" : "red");
            if (frm.doc.distribution_variance) {
                frm.dashboard.add_indicator(__(`فرق التوزيع: ${frm.doc.distribution_variance}`), "red");
            }
        }
    },
    include_zamzam(frm) {
        frappe.show_alert({
            message: __("بعد الحفظ استخدم تحميل المكونات الأساسية لتحديث زمزم"),
            indicator: "blue"
        }, 5);
    },
    distribution_plan_basis(frm) {
        frm.set_value("cartons", []);
    },
    max_carton_capacity(frm) {
        frm.set_value("cartons", []);
    }
});
