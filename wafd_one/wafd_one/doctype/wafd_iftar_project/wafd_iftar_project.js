const IFTAR_PROJECT_SETUP = {
    "المسجد النبوي الشريف / Prophet’s Mosque": {
        site: "المسجد النبوي / Prophet Mosque",
        entity_type: "جهة حكومية / Government Entity",
        entity: "الهيئة العامة للعناية بشؤون المسجد الحرام والمسجد النبوي"
    },
    "مسجد قباء / Quba Mosque": {
        site: "مسجد قباء / Quba Mosque",
        entity_type: "جهة حكومية / Government Entity",
        entity: "هيئة تطوير منطقة المدينة المنورة"
    },
    "مسجد القبلتين / Qiblatain Mosque": {
        site: "مسجد القبلتين / Qiblatain Mosque",
        entity_type: "جهة حكومية / Government Entity",
        entity: "هيئة تطوير منطقة المدينة المنورة"
    },
    "مسجد الميقات (ذي الحليفة) / Miqat Mosque (Dhul Hulayfah)": {
        site: "الميقات / Miqat",
        entity_type: "جهة حكومية / Government Entity",
        entity: "هيئة تطوير منطقة المدينة المنورة"
    },
    "مشروع أو موقع آخر / Other Project or Site": {
        site: "موقع آخر / Other",
        entity_type: "أخرى / Other",
        entity: ""
    }
};

const STANDARD_IFTAR_COMPONENTS = [
    ["زبادي", 1, "أساسي / Core", 1],
    ["تمر", 5, "أساسي / Core", 1],
    ["ماء 330 مل", 1, "أساسي / Core", 1],
    ["دقة مدينية", 1, "أساسي / Core", 1],
    ["ملعقة", 1, "أساسي / Core", 1],
    ["منديل معطر", 1, "أساسي / Core", 1],
    ["خبز فتوت", 1, "أساسي / Core", 1],
    ["غلاف إفطار صائم", 1, "تغليف / Packaging", 1],
    ["غلاف شركة وفد المدينة", 1, "تغليف / Packaging", 1]
];

async function apply_project_setup(frm) {
    const setup = IFTAR_PROJECT_SETUP[frm.doc.project_title];
    if (!setup) return;
    await frm.set_value("distribution_site", setup.site);
    await frm.set_value("contracting_entity_type", setup.entity_type);
    if (setup.entity || frm.doc.project_title !== "مشروع أو موقع آخر / Other Project or Site") {
        await frm.set_value("contracting_entity", setup.entity);
    }
    frm.toggle_enable("contracting_entity", frm.doc.project_title === "مشروع أو موقع آخر / Other Project or Site");
    frm.toggle_enable("contracting_entity_type", frm.doc.project_title === "مشروع أو موقع آخر / Other Project or Site");
}

async function load_standard_components_client(frm) {
    if ((frm.doc.components || []).length) return;
    const rows = [...STANDARD_IFTAR_COMPONENTS];
    if (frm.doc.include_zamzam) rows.push(["ماء زمزم 330 مل", 1, "إضافة / Add-on", 1]);
    for (const [ingredient_name, qty, group, mandatory] of rows) {
        const r = await frappe.db.get_value("WAFD Ingredient", {ingredient_name}, ["name", "uom", "latest_market_cost", "standard_cost", "latest_price_source", "cost_basis"]);
        const value = r && r.message;
        if (!value || !value.name) continue;
        const row = frm.add_child("components");
        row.ingredient = value.name;
        row.quantity_per_meal = qty;
        row.component_group = group;
        row.is_mandatory = mandatory;
        row.uom = value.uom;
        row.unit_cost = value.latest_market_cost || value.standard_cost || (ingredient_name === "ماء زمزم 330 مل" ? (frm.doc.zamzam_reference_price || 1.5) : 0);
        row.cost_per_meal = flt(row.quantity_per_meal) * flt(row.unit_cost);
        row.price_source = value.latest_price_source || value.cost_basis || __("المخزون / Inventory");
    }
    frm.refresh_field("components");
}


function render_iftar_summary(frm) {
    const days = cint(frm.doc.number_of_days || 0);
    const total = cint(frm.doc.total_meals || 0);
    const cartons = Math.ceil(cint(frm.doc.daily_meals || 0) / Math.max(cint(frm.doc.max_carton_capacity || 25), 1));
    const allocated = (frm.doc.distribution_recipients || []).reduce((s, r) => s + cint(r.meal_quantity), 0);
    const completed = (frm.doc.daily_executions || []).filter(r => cint(r.received_meals) > 0).length;
    const html = `<div class="wafd-iftar-summary">
      <div><b>${__("الوجبات اليومية")}</b><strong>${format_number(frm.doc.daily_meals || 0)}</strong></div>
      <div><b>${__("أيام المشروع")}</b><strong>${days}</strong></div>
      <div><b>${__("إجمالي الوجبات")}</b><strong>${format_number(total)}</strong></div>
      <div><b>${__("كراتين يومية")}</b><strong>${cartons}</strong></div>
      <div><b>${__("الموزع من الخطة")}</b><strong>${format_number(allocated)}</strong></div>
      <div><b>${__("أيام مكتملة")}</b><strong>${completed}/${days}</strong></div>
    </div>`;
    frm.get_field("quick_summary")?.$wrapper.html(html);
}

function add_print_button(frm, label, format) {
    frm.add_custom_button(__(label), () => {
        const url = `/printview?doctype=${encodeURIComponent(frm.doctype)}&name=${encodeURIComponent(frm.doc.name)}&format=${encodeURIComponent(format)}&no_letterhead=1`;
        window.open(url, "_blank");
    }, __("النماذج والتقارير / Forms & Reports"));
}

function apply_simple_mode(frm) {
    ["components", "operating_costs", "cartons"].forEach(field => frm.toggle_display(field, !frm.is_new()));
    frm.toggle_display("daily_executions", !frm.is_new());
}

frappe.ui.form.on("WAFD Iftar Project", {
    async onload(frm) {
        if (frm.is_new()) {
            if (!frm.doc.project_title) await frm.set_value("project_title", "المسجد النبوي الشريف / Prophet’s Mosque");
            await apply_project_setup(frm);
            await load_standard_components_client(frm);
        }
    },
    async refresh(frm) {
        await apply_project_setup(frm);
        apply_simple_mode(frm);
        render_iftar_summary(frm);
        frm.set_query("vehicle", "cartons", () => ({ filters: { status: "متاحة / Available" } }));
        const missing_costs = (frm.doc.components || []).filter(row => flt(row.unit_cost) <= 0).map(row => row.ingredient);
        if (missing_costs.length) {
            frm.dashboard.set_headline_alert(__("توجد مواد بدون تكلفة. أدخل التكلفة الفعلية قبل اعتماد المشروع."), "orange");
        }
        if (!frm.is_new() && frm.doc.docstatus === 0) {
            frm.add_custom_button(__("تحديث المكونات والتكاليف / Refresh Components & Costs"), async () => {
                if (frm.is_dirty()) await frm.save();
                await frappe.call({
                    method: "wafd_one.wafd_one.doctype.wafd_iftar_project.wafd_iftar_project.load_standard_components",
                    args: { project_name: frm.doc.name }, freeze: true
                });
                await frm.reload_doc();
            }, __("إفطار الصائم / Iftar"));
            frm.add_custom_button(__("تحميل تكاليف التشغيل / Load Operating Costs"), async () => {
                if (frm.is_dirty()) await frm.save();
                await frappe.call({method: "wafd_one.wafd_one.doctype.wafd_iftar_project.wafd_iftar_project.load_standard_operating_costs", args: {project_name: frm.doc.name}, freeze: true});
                await frm.reload_doc();
            }, __("إفطار الصائم / Iftar"));
            frm.add_custom_button(__("إنشاء خطة الكراتين / Generate Cartons"), async () => {
                if (frm.is_dirty()) await frm.save();
                const r = await frappe.call({method: "wafd_one.wafd_one.doctype.wafd_iftar_project.wafd_iftar_project.generate_cartons", args: {project_name: frm.doc.name}, freeze: true});
                frappe.show_alert({message: __(`تم إنشاء ${r.message.carton_count} كرتون`), indicator: "green"}, 6);
                await frm.reload_doc();
            }, __("إفطار الصائم / Iftar"));
        }
        if (!frm.is_new()) {
            frm.dashboard.add_indicator(__(`إجمالي الوجبات: ${frm.doc.total_meals || 0}`), "blue");
            frm.dashboard.add_indicator(__(`خطة التوزيع: ${frm.doc.planned_distribution_meals || 0}`), "blue");
            frm.dashboard.add_indicator(__(`التكلفة/وجبة: ${format_currency(frm.doc.actual_cost_per_meal || 0)}`), "orange");
            frm.dashboard.add_indicator(__(`الربح المتوقع: ${format_currency(frm.doc.expected_profit || 0)}`), (frm.doc.expected_profit || 0) >= 0 ? "green" : "red");
        }
        if (!frm.is_new()) {
            add_print_button(frm, "ملخص المشروع / Project Summary", "WAFD Iftar Project Summary");
            add_print_button(frm, "التقرير اليومي / Daily Report", "WAFD Iftar Daily Report");
            add_print_button(frm, "نموذج التسليم / Delivery Note", "WAFD Iftar Delivery Note");
            add_print_button(frm, "نموذج الاستلام / Receipt Note", "WAFD Iftar Receipt Note");
        }
    },
    daily_meals(frm) { render_iftar_summary(frm); },
    start_date(frm) { render_iftar_summary(frm); },
    end_date(frm) { render_iftar_summary(frm); },
    async project_title(frm) { await apply_project_setup(frm); },
    async include_zamzam(frm) {
        if (frm.is_new()) {
            frm.clear_table("components");
            await load_standard_components_client(frm);
        } else {
            frappe.show_alert({message: __("احفظ ثم استخدم تحديث المكونات والتكاليف"), indicator: "blue"}, 5);
        }
    },
    distribution_plan_basis(frm) { frm.set_value("cartons", []); },
    max_carton_capacity(frm) { frm.set_value("cartons", []); }
});

frappe.ui.form.on("WAFD Iftar Component", {
    ingredient(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.ingredient) return;
        frappe.db.get_value("WAFD Ingredient", row.ingredient, ["uom", "latest_market_cost", "standard_cost", "latest_price_source", "cost_basis"]).then(r => {
            const v = r.message || {};
            frappe.model.set_value(cdt, cdn, "uom", v.uom || "");
            frappe.model.set_value(cdt, cdn, "unit_cost", v.latest_market_cost || v.standard_cost || 0);
            frappe.model.set_value(cdt, cdn, "price_source", v.latest_price_source || v.cost_basis || __("المخزون / Inventory"));
            frappe.model.set_value(cdt, cdn, "cost_per_meal", flt(row.quantity_per_meal) * flt(v.latest_market_cost || v.standard_cost || 0));
        });
    },
    quantity_per_meal(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "cost_per_meal", flt(row.quantity_per_meal) * flt(row.unit_cost));
    },
    unit_cost(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "cost_per_meal", flt(row.quantity_per_meal) * flt(row.unit_cost));
        if (flt(row.unit_cost) > 0 && (!row.price_source || row.price_source === __("المخزون / Inventory"))) {
            frappe.model.set_value(cdt, cdn, "price_source", __("إدخال فعلي / Manual Actual Cost"));
        }
    }
});

frappe.ui.form.on("WAFD Iftar Carton", {
    vehicle(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.vehicle) {
            frappe.model.set_value(cdt, cdn, "vehicle_details", "");
            return;
        }
        frappe.db.get_value("WAFD Vehicle", row.vehicle, ["plate_number", "vehicle_type", "make_model"]).then(r => {
            const v = r.message || {};
            const details = [v.plate_number, v.vehicle_type, v.make_model].filter(Boolean).join(" — ");
            frappe.model.set_value(cdt, cdn, "vehicle_details", details);
        });
    }
});

frappe.ui.form.on("WAFD Iftar Operating Cost", {
    quantity(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "amount", flt(row.quantity) * flt(row.rate));
    },
    rate(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "amount", flt(row.quantity) * flt(row.rate));
    }
});
