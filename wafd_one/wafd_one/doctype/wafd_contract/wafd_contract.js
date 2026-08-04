frappe.ui.form.on("WAFD Contract", {
    setup(frm) {
        frm.set_df_property("project", "read_only", 1);
        install_meal_queries(frm);
    },

    before_save(frm) {
        frm.__wafd_was_new = frm.is_new();
        set_automatic_contract_title(frm);
    },

    after_save(frm) {
        if (frm.__wafd_auto_start_running || frm.doc.project) return;
        frm.__wafd_was_new = false;
        const missing = ["mission", "hotel", "start_date", "end_date", "beneficiary_count"]
            .filter((fieldname) => !frm.doc[fieldname]);
        if (!(frm.doc.services || []).length) missing.push("services");
        if (missing.length) {
            frappe.show_alert({
                message: __("تم حفظ العقد. أكمل البعثة والفندق والتواريخ وعدد المستفيدين وبنود الخدمة لبدء الدورة تلقائيًا."),
                indicator: "orange"
            }, 7);
            return;
        }
        frm.__wafd_auto_start_running = true;
        frappe.call({
            method: "wafd_one.wafd_one.doctype.wafd_contract.wafd_contract.activate_and_generate_operations",
            args: { contract_name: frm.doc.name },
            freeze: true,
            freeze_message: __("جارٍ إنشاء المشروع وخطة التشغيل تلقائيًا..."),
            callback(r) {
                const data = r.message || {};
                const projectName = data.project?.name;
                frappe.show_alert({
                    message: __("تم إنشاء المشروع وخطة التشغيل — جارٍ فتح التخطيط اليومي"),
                    indicator: "green"
                }, 6);
                if (projectName) setTimeout(() => open_next_project_step(projectName), 300);
                else frm.reload_doc();
            },
            always() { frm.__wafd_auto_start_running = false; }
        });
    },

    refresh(frm) {
        normalize_advance_percent(frm);
        calculate_contract(frm);
        if (frm.is_new()) return;

        frm.set_df_property("project", "read_only", 1);
        if (frm.doc.project) {
            frm.add_custom_button(__("فتح المشروع / Open Project"), () => {
                frappe.set_route("Form", "WAFD Catering Project", frm.doc.project);
            }, __("المشروع / Project"));
        }

        frm.add_custom_button(__("إعادة تهيئة بيانات الاختبار / Reset Test Data"), () => {
            open_contract_cleanup_dialog(frm, {
                mode: "reset",
                title: __("إعادة تهيئة بيانات العقد التجريبية"),
                phrase: "RESET",
                warning: __("سيتم حذف المشروع وجميع البيانات التشغيلية والمالية المرتبطة، مع الإبقاء على العقد وإعادته إلى مسودة."),
                action_label: __("إعادة تهيئة / Reset"),
                method: "wafd_one.wafd_one.doctype.wafd_contract.wafd_contract.reset_contract_test_data",
                freeze_message: __("جارٍ إعادة تهيئة بيانات العقد بأمان...")
            });
        }, __("إدارة / Administration"));

        frm.add_custom_button(__("حذف العقد وبياناته التجريبية / Delete Contract & Test Data"), () => {
            open_contract_cleanup_dialog(frm, {
                mode: "delete",
                title: __("حذف نهائي للعقد وجميع بياناته"),
                phrase: "DELETE",
                warning: __("تحذير: لا يمكن التراجع. سيتم حذف العقد والمشروع وكل السجلات التشغيلية والمالية المرتبطة به فقط."),
                action_label: __("حذف نهائي / Permanently Delete"),
                method: "wafd_one.wafd_one.doctype.wafd_contract.wafd_contract.purge_contract_and_operations",
                freeze_message: __("جارٍ حذف العقد وسلسلته المرتبطة بأمان...")
            });
        }, __("إدارة / Administration"));
        frm.change_custom_button_type(
            __("حذف العقد وبياناته التجريبية / Delete Contract & Test Data"),
            __("إدارة / Administration"),
            "danger"
        );

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
                        const projectName = data.project?.name || frm.doc.project;
                        frappe.show_alert({
                            message: __("تم إنشاء دورة التشغيل بنجاح — جارٍ فتح المشروع / Operations created — opening project"),
                            indicator: (op.warnings || []).length ? "orange" : "green"
                        }, 6);
                        if (projectName) {
                            setTimeout(() => open_next_project_step(projectName), 350);
                        } else {
                            frm.reload_doc();
                        }
                    }
                })
            );
        }, __("التشغيل / Operations"));
    },

    start_date(frm) { calculate_contract(frm); set_automatic_contract_title(frm); },
    end_date: calculate_contract,
    beneficiary_count: calculate_contract,
    contract_value: calculate_contract,
    discount_amount: calculate_contract,
    tax_rate: calculate_contract,
    advance_percent: calculate_contract,
    advance_amount: calculate_contract,

    mission(frm) {
        set_automatic_contract_title(frm);
        if (!frm.doc.mission) return;
        frappe.db.get_value("WAFD Mission", frm.doc.mission, ["contact_person", "mobile"], (r) => {
            if (!frm.doc.contact_person && r?.contact_person) frm.set_value("contact_person", r.contact_person);
            if (!frm.doc.contact_phone && r?.mobile) frm.set_value("contact_phone", r.mobile);
        });
    },

    hotel(frm) {
        set_automatic_contract_title(frm);
        if (!frm.doc.hotel) return;
        frappe.db.get_value("WAFD Hotel", frm.doc.hotel, ["address", "contact_person", "mobile"], (r) => {
            if (!frm.doc.delivery_location && r?.address) frm.set_value("delivery_location", r.address);
            if (!frm.doc.contact_person && r?.contact_person) frm.set_value("contact_person", r.contact_person);
            if (!frm.doc.contact_phone && r?.mobile) frm.set_value("contact_phone", r.mobile);
        });
    }
});


function set_automatic_contract_title(frm) {
    if (!frm.is_new() && frm.doc.contract_title && !frm.__wafd_title_generated) return;
    const parts = [frm.doc.mission, frm.doc.hotel].filter(Boolean);
    if (frm.doc.start_date) parts.push(frappe.datetime.str_to_user(frm.doc.start_date));
    if (!parts.length) return;
    const value = parts.join(" - ");
    if (frm.doc.contract_title !== value) {
        frm.__wafd_title_generated = true;
        frm.set_value("contract_title", value);
    }
}

function open_contract_cleanup_dialog(frm, options) {
    frappe.call({
        method: "wafd_one.wafd_one.doctype.wafd_contract.wafd_contract.preview_contract_purge",
        args: { contract_name: frm.doc.name },
        freeze: true,
        callback(r) {
            const data = r.message || {};
            const counts = data.counts || {};
            const rows = Object.entries(counts)
                .filter(([doctype]) => options.mode === "delete" || doctype !== "WAFD Contract")
                .map(([doctype, count]) => `<tr><td>${frappe.utils.escape_html(doctype)}</td><td>${count}</td></tr>`)
                .join("");
            const total = Object.entries(counts)
                .filter(([doctype]) => options.mode === "delete" || doctype !== "WAFD Contract")
                .reduce((sum, [, count]) => sum + flt(count), 0);
            const phrase = options.phrase;
            const settlement = data.stock_settlement || {};
            const stockItems = settlement.items || [];
            const stockRows = stockItems.map((item) => `<tr>
                <td>${frappe.utils.escape_html(item.ingredient || "-")}</td>
                <td>${frappe.utils.escape_html(item.warehouse || "-")}</td>
                <td>${flt(item.received_quantity || 0)}</td>
                <td>${flt(item.consumed_from_received || 0)}</td>
                <td>${flt(item.unused_quantity_retained || 0)}</td>
                <td>${frappe.utils.escape_html(item.uom || "")}</td>
            </tr>`).join("");
            const stockPreview = stockRows ? `<div class="alert alert-info mt-3">
                <b>${__("تسوية المخزون عند التنفيذ:")}</b>
                <div class="mt-1">${__("سيبقى الرصيد الفعلي كما هو: المصروف يظل مستهلكًا، وغير المستخدم يبقى في مستودعه أو ثلاجته دون إضافة مكررة.")}</div>
                <table class="table table-bordered mt-2">
                    <thead><tr><th>${__("الصنف")}</th><th>${__("المستودع/الثلاجة")}</th><th>${__("المستلم")}</th><th>${__("المصروف")}</th><th>${__("غير المستخدم")}</th><th>${__("الوحدة")}</th></tr></thead>
                    <tbody>${stockRows}</tbody>
                </table>
            </div>` : `<div class="alert alert-info mt-3">${__("لا توجد حركات مخزون مرتبطة بهذا العقد.")}</div>`;

            const dialog = new frappe.ui.Dialog({
                title: options.title,
                fields: [
                    {
                        fieldtype: "HTML",
                        options: `<div class="alert alert-danger">
                            <b>${options.warning}</b>
                            <table class="table table-bordered mt-3"><tbody>${rows}</tbody></table>
                            <b>${__("إجمالي السجلات")}: ${total}</b>
                            ${stockPreview}
                            <div class="mt-3">${__("اكتب {0} للتأكيد", [phrase])}</div>
                        </div>`
                    },
                    {
                        fieldname: "confirmation",
                        fieldtype: "Data",
                        label: __("عبارة التأكيد"),
                        reqd: 1
                    }
                ],
                primary_action_label: options.action_label,
                primary_action(values) {
                    if ((values.confirmation || "").trim().toUpperCase() !== phrase) {
                        frappe.msgprint(__("عبارة التأكيد غير صحيحة. اكتب {0}", [phrase]));
                        return;
                    }
                    frappe.call({
                        method: options.method,
                        type: "POST",
                        args: { contract_name: frm.doc.name, confirmation: values.confirmation },
                        freeze: true,
                        freeze_message: options.freeze_message,
                        callback(res) {
                            dialog.hide();
                            const result = res.message || {};
                            const finalSettlement = result.stock_settlement || {};
                            const lines = (finalSettlement.items || []).map((item) => {
                                return `• ${frappe.utils.escape_html(item.ingredient || "-")} — ${frappe.utils.escape_html(item.warehouse || "-")}: ` +
                                    `${__("المستلم")} ${flt(item.received_quantity || 0)}، ` +
                                    `${__("المصروف")} ${flt(item.consumed_from_received || 0)}، ` +
                                    `${__("غير المستخدم والمتبقي في المخزون")} ${flt(item.unused_quantity_retained || 0)} ${frappe.utils.escape_html(item.uom || "")}`;
                            }).join("<br>");
                            frappe.msgprint({
                                title: options.mode === "delete" ? __("تم حذف العقد بنجاح") : __("اكتملت إعادة التهيئة"),
                                indicator: "green",
                                message: __("تمت معالجة {0} سجل مرتبط.<br><br><b>بيان المخزون:</b><br>{1}", [
                                    result.total || 0,
                                    lines || __("لا توجد حركات مخزون مرتبطة.")
                                ])
                            });
                            if (options.mode === "delete") {
                                frappe.set_route("List", "WAFD Contract");
                            } else {
                                frm.reload_doc();
                            }
                        }
                    });
                },
                secondary_action_label: __("إلغاء / Cancel"),
                secondary_action() { dialog.hide(); }
            });
            dialog.show();
        }
    });
}

frappe.ui.form.on("WAFD Project Service", {
    form_render(frm, cdt, cdn) { configure_meal_selector(frm, cdt, cdn); },
    service_type(frm, cdt, cdn) { configure_meal_selector(frm, cdt, cdn); },
    meal_name(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.meal_name) frappe.model.set_value(cdt, cdn, "recipe", row.meal_name);
    },
    recipe(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.recipe && !row.meal_name) frappe.model.set_value(cdt, cdn, "meal_name", row.recipe);
    },
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

function normalize_advance_percent(frm) {
    const value = flt(frm.doc.advance_percent);
    // A stale Custom Field/Property Setter from older releases could place the
    // contract grand total in this Percent field on a new form. Never allow an
    // impossible percentage to poison the financial calculation.
    if (frm.is_new() && value > 100) {
        frm.set_value("advance_percent", 0);
    }
}

function calculate_contract(frm) {
    // The child table can also be embedded in other forms. Only run contract
    // totals when the current parent is actually WAFD Contract and the target
    // fields exist, otherwise Frappe raises "field does not exist" errors.
    if (frm.doctype !== "WAFD Contract" || !frm.fields_dict.services_subtotal) return;

    if (frm.doc.start_date && frm.doc.end_date) {
        frm.set_value("duration_days", frappe.datetime.get_day_diff(frm.doc.end_date, frm.doc.start_date) + 1);
    }
    normalize_advance_percent(frm);
    const subtotal = (frm.doc.services || []).reduce((sum, row) => sum + flt(row.estimated_revenue), 0);
    // Contract Value means the agreed amount before VAT. Services subtotal is
    // used only when no manual contract value has been entered.
    const baseValue = flt(frm.doc.contract_value || subtotal);
    const taxable = Math.max(baseValue - flt(frm.doc.discount_amount), 0);
    const tax = taxable * flt(frm.doc.tax_rate) / 100;
    const grandTotal = taxable + tax;
    let advance = Math.max(flt(frm.doc.advance_amount), 0);
    if (advance > grandTotal) advance = grandTotal;
    const advancePercent = grandTotal > 0 ? (advance / grandTotal * 100) : 0;
    frm.set_value("services_subtotal", subtotal);
    if (!flt(frm.doc.contract_value) && subtotal) frm.set_value("contract_value", subtotal);
    frm.set_value("tax_amount", tax);
    frm.set_value("grand_total", grandTotal);
    if (flt(frm.doc.advance_amount) !== advance) frm.set_value("advance_amount", advance);
    frm.set_value("advance_percent", advancePercent);
    frm.set_value("outstanding_contract_amount", Math.max(grandTotal - advance, 0));
}


const WAFD_RECIPE_CATEGORY_MAP = {
    "إفطار / Breakfast": "إفطار / Breakfast",
    "غداء / Lunch": "غداء / Lunch",
    "عشاء / Dinner": "عشاء / Dinner",
    "سحور / Suhoor": "إفطار / Breakfast",
    "إفطار صائم / Iftar Saem": "إفطار صائم / Iftar",
    "كوفي بريك / Coffee Break": "كوفي بريك / Coffee Break",
    "بوفيه / Buffet": "بوفيه / Buffet",
    "وجبة خفيفة / Snack": "وجبة خفيفة / Snack"
};

function recipe_query_for_row(cdt, cdn) {
    const row = locals[cdt] && locals[cdt][cdn];
    const filters = { status: "نشطة / Active" };
    const category = row && WAFD_RECIPE_CATEGORY_MAP[row.service_type];
    if (category) filters.meal_category = category;
    return { filters };
}

function install_meal_queries(frm) {
    const grid = frm.fields_dict.services && frm.fields_dict.services.grid;
    if (!grid) return;
    grid.get_field("meal_name").get_query = (doc, cdt, cdn) => recipe_query_for_row(cdt, cdn);
    grid.get_field("recipe").get_query = (doc, cdt, cdn) => recipe_query_for_row(cdt, cdn);
}

function configure_meal_selector(frm, cdt, cdn) {
    install_meal_queries(frm);
    const row = locals[cdt][cdn];
    if (row.meal_name) frappe.model.set_value(cdt, cdn, "meal_name", null);
    if (row.recipe) frappe.model.set_value(cdt, cdn, "recipe", null);
    if (frm.fields_dict.services && frm.fields_dict.services.grid) frm.fields_dict.services.grid.refresh();
}

function open_next_project_step(projectName) {
    frappe.call({
        method: "wafd_one.operations.get_next_operational_action",
        args: { project_name: projectName },
        freeze: true,
        freeze_message: __("جارٍ فتح الخطوة التشغيلية التالية..."),
        callback(r) {
            const action = r.message || {};
            if (action.route) frappe.set_route(...action.route);
            else frappe.set_route("Form", "WAFD Catering Project", projectName);
        }
    });
}
