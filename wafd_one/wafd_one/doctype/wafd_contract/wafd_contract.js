frappe.ui.form.on("WAFD Contract", {
    refresh(frm) {
        calculate_contract(frm);
        if (frm.is_new()) return;

        if (!frm.doc.project) {
            frm.add_custom_button(__("إنشاء المشروع / Create Project"), () => {
                frappe.call({
                    method: "wafd_one.wafd_one.doctype.wafd_contract.wafd_contract.create_project_from_contract",
                    args: { contract_name: frm.doc.name },
                    freeze: true,
                    freeze_message: __("جارٍ إنشاء المشروع..."),
                    callback(r) {
                        if (r.message?.name) frappe.set_route("Form", "WAFD Catering Project", r.message.name);
                    }
                });
            });
        }

        frm.add_custom_button(__("تفعيل وبناء خطة التشغيل / Activate & Build Operations"), () => {
            frappe.confirm(
                __("سيتم تفعيل العقد وإنشاء المشروع وخطط الوجبات ودفعات الإنتاج بدون تكرار السجلات. متابعة؟"),
                () => frappe.call({
                    method: "wafd_one.wafd_one.doctype.wafd_contract.wafd_contract.activate_and_generate_operations",
                    args: { contract_name: frm.doc.name },
                    freeze: true,
                    freeze_message: __("جارٍ بناء دورة التشغيل..."),
                    callback(r) {
                        const data = r.message || {};
                        const op = data.operations || {};
                        frappe.msgprint({
                            title: __("تم إنشاء دورة التشغيل"),
                            indicator: (op.warnings || []).length ? "orange" : "green",
                            message: __("المشروع: {0}<br>خطط الوجبات الجديدة: {1}<br>دفعات الإنتاج الجديدة: {2}", [
                                data.project?.name || frm.doc.project || "-",
                                op.meal_plans_created || 0,
                                op.batches_created || 0
                            ])
                        });
                        frm.reload_doc();
                    }
                })
            );
        }, __("التشغيل / Operations"));
    },

    start_date: calculate_contract,
    end_date: calculate_contract,
    beneficiary_count: calculate_contract,
    contract_value: calculate_contract,
    discount_amount: calculate_contract,
    tax_rate: calculate_contract,
    advance_percent: calculate_contract,

    mission(frm) {
        if (!frm.doc.mission) return;
        frappe.db.get_value("WAFD Mission", frm.doc.mission, ["contact_person", "mobile"], (r) => {
            if (!frm.doc.contact_person && r?.contact_person) frm.set_value("contact_person", r.contact_person);
            if (!frm.doc.contact_phone && r?.mobile) frm.set_value("contact_phone", r.mobile);
        });
    },

    hotel(frm) {
        if (!frm.doc.hotel) return;
        frappe.db.get_value("WAFD Hotel", frm.doc.hotel, ["address", "contact_person", "mobile"], (r) => {
            if (!frm.doc.delivery_location && r?.address) frm.set_value("delivery_location", r.address);
            if (!frm.doc.contact_person && r?.contact_person) frm.set_value("contact_person", r.contact_person);
            if (!frm.doc.contact_phone && r?.mobile) frm.set_value("contact_phone", r.mobile);
        });
    }
});

frappe.ui.form.on("WAFD Project Service", {
    service_start_date: calculate_service,
    service_end_date: calculate_service,
    service_days: calculate_service,
    beneficiaries: calculate_service,
    meals_per_person_per_day: calculate_service,
    unit_price: calculate_service,
    services_remove: calculate_contract
});

function calculate_service(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    let days = flt(row.service_days || 0);
    if (!days && row.service_start_date && row.service_end_date) {
        days = frappe.datetime.get_day_diff(row.service_end_date, row.service_start_date) + 1;
        frappe.model.set_value(cdt, cdn, "service_days", days);
    }
    const beneficiaries = flt(row.beneficiaries || frm.doc.beneficiary_count || 0);
    const multiplier = flt(row.meals_per_person_per_day || 1);
    const total = Math.round(days * beneficiaries * multiplier);
    frappe.model.set_value(cdt, cdn, "total_meals", total);
    frappe.model.set_value(cdt, cdn, "estimated_revenue", total * flt(row.unit_price));
    calculate_contract(frm);
}

function calculate_contract(frm) {
    if (frm.doc.start_date && frm.doc.end_date) {
        frm.set_value("duration_days", frappe.datetime.get_day_diff(frm.doc.end_date, frm.doc.start_date) + 1);
    }
    const subtotal = (frm.doc.services || []).reduce((sum, row) => sum + flt(row.estimated_revenue), 0);
    // Contract Value means the agreed amount before VAT. Services subtotal is
    // used only when no manual contract value has been entered.
    const baseValue = flt(frm.doc.contract_value || subtotal);
    const taxable = Math.max(baseValue - flt(frm.doc.discount_amount), 0);
    const tax = taxable * flt(frm.doc.tax_rate) / 100;
    const grandTotal = taxable + tax;
    const advance = grandTotal * flt(frm.doc.advance_percent) / 100;
    frm.set_value("services_subtotal", subtotal);
    if (!flt(frm.doc.contract_value) && subtotal) frm.set_value("contract_value", subtotal);
    frm.set_value("tax_amount", tax);
    frm.set_value("grand_total", grandTotal);
    frm.set_value("advance_amount", advance);
    frm.set_value("outstanding_contract_amount", Math.max(grandTotal - advance, 0));
}
