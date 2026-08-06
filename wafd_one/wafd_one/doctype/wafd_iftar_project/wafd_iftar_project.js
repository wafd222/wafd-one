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
        frm.set_query("vehicle", "cartons", () => ({ filters: { status: "متاحة / Available" } }));
        const missing_costs = (frm.doc.components || []).filter(row => flt(row.unit_cost) <= 0).map(row => row.ingredient);
        if (!frm.is_new() && missing_costs.length) {
            frm.dashboard.set_headline_alert(__("سيتم تحديث الأسعار المرجعية تلقائياً عند الاعتماد. يمكن تعديلها من التفاصيل المتقدمة."), "blue");
        }
        if (!frm.is_new() && frm.doc.docstatus === 0) {
            frm.add_custom_button(__("تجهيز واعتماد المشروع / Prepare & Submit"), async () => {
                if (frm.is_dirty()) await frm.save();
                await frm.save("Submit");
            }).addClass("btn-primary");
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
            frm.add_custom_button(__("حذف التجربة وإرجاع المواد"), () => {
                frappe.confirm(
                    __("سيتم حذف المشروع وكل السجلات اليومية المرتبطة به، وإلغاء أي حركة مخزون مرتبطة لإرجاع المواد. هل أنت متأكد؟"),
                    async () => {
                        const result = await frappe.call({
                            method: "wafd_one.wafd_one.doctype.wafd_iftar_project.wafd_iftar_project.delete_iftar_project_permanently",
                            args: { project_name: frm.doc.name },
                            freeze: true,
                            freeze_message: __("جاري إلغاء السجلات وإرجاع المواد ثم حذف المشروع...")
                        });
                        frappe.show_alert({
                            message: __(`تم حذف المشروع وإلغاء ${result.message.reversed_stock_movements || 0} حركة مخزون`),
                            indicator: "green"
                        }, 7);
                        frappe.set_route("List", "WAFD Iftar Project");
                    }
                );
            }, __("إدارة المشروع")).addClass("btn-danger");

            frm.dashboard.add_indicator(__(`إجمالي الوجبات: ${frm.doc.total_meals || 0}`), "blue");
            frm.dashboard.add_indicator(__(`خطة التوزيع: ${frm.doc.planned_distribution_meals || 0}`), "blue");
            frm.dashboard.add_indicator(__(`التكلفة/وجبة: ${format_currency(frm.doc.actual_cost_per_meal || 0)}`), "orange");
            frm.dashboard.add_indicator(__(`الربح المتوقع: ${format_currency(frm.doc.expected_profit || 0)}`), (frm.doc.expected_profit || 0) >= 0 ? "green" : "red");
        }
    },
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


frappe.ui.form.on("WAFD Iftar Project", {
  async refresh(frm) {
    if (frm.fields_dict.daily_operations_html) {
      const w=frm.fields_dict.daily_operations_html.$wrapper;
      if (frm.is_new()) { w.html('<div class="alert alert-info">احفظ المشروع أولاً ليتم إنشاء الخطة اليومية.</div>'); }
      else {
        const x=(await frappe.call({method:'wafd_one.wafd_one.iftar_pro.get_project_operations',args:{project_name:frm.doc.name}})).message||[];
        w.html(`<div class="iftar-inline-head"><b>الخطة اليومية</b><button class="btn btn-sm btn-primary generate-days">توليد الأيام الناقصة</button></div>${x.length?`<table class="table table-bordered"><thead><tr><th>التاريخ</th><th>الحالة</th><th>المخطط</th><th>الإنتاج</th><th>التغليف</th><th>التحميل</th><th>التسليم</th><th>الاستلام</th><th>الإنجاز</th></tr></thead><tbody>${x.map(r=>`<tr data-day="${r.name}" style="cursor:pointer"><td>${frappe.datetime.str_to_user(r.operation_date)}</td><td>${r.status}</td><td>${r.planned_meals||0}</td><td>${r.produced_meals||0}</td><td>${r.packaged_meals||0}</td><td>${r.loaded_meals||0}</td><td>${r.delivered_meals||0}</td><td>${r.received_meals||0}</td><td>${r.completion_percent||0}%</td></tr>`).join('')}</tbody></table>`:'<div class="alert alert-warning">لم تُنشأ الخطة اليومية بعد.</div>'}`);
        w.off('click').on('click','[data-day]',function(){frappe.set_route('Form','WAFD Iftar Daily Operation',$(this).data('day'))}).on('click','.generate-days',async()=>{await frappe.call({method:'wafd_one.wafd_one.iftar_pro.generate_daily_operations',args:{project_name:frm.doc.name},freeze:true});frm.reload_doc()});
      }
    }
    if (frm.fields_dict.reports_html) {
      const w=frm.fields_dict.reports_html.$wrapper;
      w.html(`<div class="iftar-report-grid"><button data-page="wafd-iftar-operations">لوحة التشغيل اليومية</button><button data-list="WAFD Iftar Daily Operation">السجلات اليومية</button><button data-print="1">ملخص المشروع</button><button data-list="WAFD Iftar Daily Operation">نماذج التسليم والاستلام</button></div>`);
      w.off('click').on('click','[data-page]',function(){frappe.set_route($(this).data('page'))}).on('click','[data-list]',function(){frappe.set_route('List',$(this).data('list'),{project:frm.doc.name})}).on('click','[data-print]',()=>frappe.set_route('print', frm.doctype, frm.doc.name, {print_format:'WAFD Iftar Project Summary'}));
    }
  },
  start_date: update_iftar_totals, end_date: update_iftar_totals, daily_meals: update_iftar_totals,
  meal_template(frm){const z=frm.doc.meal_template==='وجبة مع زمزم / Iftar + Zamzam';frm.set_value('include_zamzam',z?1:0);}
});
function update_iftar_totals(frm){if(frm.doc.start_date&&frm.doc.end_date){const days=frappe.datetime.get_day_diff(frm.doc.end_date,frm.doc.start_date)+1;frm.set_value('number_of_days',Math.max(days,0));frm.set_value('total_meals',Math.max(days,0)*(frm.doc.daily_meals||0));}}
