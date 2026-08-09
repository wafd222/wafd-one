frappe.ui.form.on("WAFD Production Batch", {
    setup(frm) {
        frm.set_query("warehouse", "source_warehouses", () => ({ filters: { status: "نشط / Active" } }));
    },

    onload(frm) {
        if (frm.is_new() && frm.doc.meal_plan) populate_from_meal_plan(frm);
    },

    refresh(frm) {
        if (frm.is_new()) {
            if (frm.doc.meal_plan) populate_from_meal_plan(frm);
            return;
        }

        frm.add_custom_button(__("New CCP Check"), () => {
            frappe.call({
                method: "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.prepare_ccp_check",
                args: { batch_name: frm.doc.name },
                freeze: true,
                callback(r) {
                    const result = r.message || {};
                    if (result.name) frappe.set_route("Form", "WAFD CCP Check", result.name);
                    else if (result.values) frappe.new_doc("WAFD CCP Check", result.values);
                }
            });
        }, __("Food Safety"));

        if (frm.doc.food_safety_release_status !== "مفرج / Released") {
            frm.add_custom_button(__("Release Food Safety Batch"), () => {
                frappe.call({
                    method: "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.release_food_safety_batch",
                    args: { batch_name: frm.doc.name },
                    freeze: true,
                    callback() { frm.reload_doc(); }
                });
            }, __("Food Safety"));
        }

        add_action(frm, __("Refresh Material Requirements"),
            "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.refresh_material_requirements",
            { batch_name: frm.doc.name }, () => frm.reload_doc());

        frm.add_custom_button(__("Stock Diagnostics"), () => {
            frappe.call({
                method: "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.get_stock_diagnostics",
                args: { batch_name: frm.doc.name }, freeze: true,
                callback(r) {
                    if (!r.message) return;
                    const d = r.message;
                    const sources = (d.sources || []).join("<br>") || __("No source warehouse configured");
                    const missing = (d.missing_balance_rows || []).join("<br>") || __("None");
                    const zero = (d.zero_balance_items || []).join("<br>") || __("None");
                    frappe.msgprint({
                        title: __("Stock Diagnostics"),
                        indicator: d.available ? "green" : "orange",
                        message: `<b>${__("Source Warehouses")}</b><br>${sources}<hr><b>${__("Items without stock balance rows")}</b><br>${missing}<hr><b>${__("Items with zero available balance")}</b><br>${zero}`
                    });
                }
            });
        }, __("Operations"));

        if (frm.doc.status === "مخطط / Planned") {
            frm.add_custom_button(__("Prepare UAT Test Stock"), () => {
                frappe.confirm(
                    __("This will create and post clearly labelled TEST stock receipts only for this batch shortages. Continue?"),
                    () => {
                        const dialog = new frappe.ui.Dialog({
                            title: __("Prepare UAT Test Stock"),
                            fields: [
                                { fieldname: "buffer_percent", fieldtype: "Percent", label: __("Test Buffer %"), default: 25 }
                            ],
                            primary_action_label: __("Create Test Stock"),
                            primary_action(values) {
                                dialog.hide();
                                frappe.call({
                                    method: "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.prepare_uat_test_stock",
                                    args: { batch_name: frm.doc.name, buffer_percent: values.buffer_percent || 0 },
                                    freeze: true,
                                    freeze_message: __("Creating and posting UAT test stock..."),
                                    callback(r) {
                                        if (!r.message) return;
                                        const message = r.message.already_available
                                            ? __("Materials are already available; no test receipt was needed.")
                                            : `${__("Posted test receipt movements")}: ${r.message.count || 0}`;
                                        frappe.msgprint({ title: __("UAT Stock Ready"), indicator: "green", message });
                                        frm.reload_doc();
                                    }
                                });
                            }
                        });
                        dialog.show();
                    }
                );
            }, __("Operations"));
        }

        frm.add_custom_button(__("Check Materials"), () => {
            frappe.call({
                method: "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.check_material_availability",
                args: { batch_name: frm.doc.name }, freeze: true,
                callback(r) {
                    if (!r.message) return;
                    if (r.message.available) {
                        frappe.msgprint({ title: __("Materials Available"), indicator: "green", message: __("All recipe materials are available.") });
                    } else {
                        const rows = r.message.shortages.map(x => `<tr><td>${frappe.utils.escape_html(x.ingredient)}</td><td>${x.quantity}</td><td>${x.available_quantity}</td><td>${x.shortage_quantity}</td></tr>`).join("");
                        frappe.msgprint({ title: __("Material Shortage"), indicator: "red", message: `<table class="table table-bordered"><thead><tr><th>${__("Ingredient")}</th><th>${__("Required")}</th><th>${__("Available")}</th><th>${__("Shortage")}</th></tr></thead><tbody>${rows}</tbody></table>` });
                    }
                }
            });
        }, __("Operations"));

        add_action(frm, __("Create Material Issue"),
            "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.create_material_issue",
            { batch_name: frm.doc.name }, result => {
                const names = [...(result.created || []), ...(result.existing || [])];
                frappe.msgprint(`${__("Material issue documents")}: ${result.count || names.length}`);
                if (result.primary) frappe.set_route("Form", "WAFD Stock Movement", result.primary);
            });

        add_action(frm, __("Quality Inspection"),
            "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.create_quality_inspection",
            { batch_name: frm.doc.name }, result => {
                if (result.name) {
                    frappe.set_route("Form", "WAFD Quality Inspection", result.name);
                } else if (result.values) {
                    frappe.new_doc("WAFD Quality Inspection", result.values);
                }
            });

        if (frm.doc.status === "مخطط / Planned") {
            add_action(frm, __("Issue Materials & Start Production"),
                "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.start_production",
                { batch_name: frm.doc.name }, () => frm.reload_doc());
        }

        if (["تحضير / Preparing", "طبخ / Cooking"].includes(frm.doc.status)) {
            frm.add_custom_button(__("Complete Production"), () => {
                const dialog = new frappe.ui.Dialog({
                    title: __("Complete Production"),
                    fields: [
                        { fieldname: "produced_quantity", fieldtype: "Int", label: __("Produced Qty"), reqd: 1, default: frm.doc.produced_quantity || frm.doc.planned_quantity },
                        { fieldname: "rejected_quantity", fieldtype: "Int", label: __("Rejected Qty"), default: frm.doc.rejected_quantity || 0 }
                    ],
                    primary_action_label: __("Complete"),
                    primary_action(values) {
                        dialog.hide();
                        frappe.call({
                            method: "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.complete_production",
                            args: { batch_name: frm.doc.name, produced_quantity: values.produced_quantity, rejected_quantity: values.rejected_quantity },
                            freeze: true,
                            callback(r) {
                                const result = r.message || {};
                                if (result.delayed && result.warning) {
                                    frappe.msgprint({
                                        title: __("Production Completed — Delayed"),
                                        indicator: "orange",
                                        message: result.warning
                                    });
                                } else {
                                    frappe.show_alert({ message: __("Production completed"), indicator: "green" });
                                }
                                const quality = result.quality_inspection || {};
                                if (quality.name) {
                                    frappe.set_route("Form", "WAFD Quality Inspection", quality.name);
                                } else if (quality.values) {
                                    frappe.new_doc("WAFD Quality Inspection", quality.values);
                                } else {
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                });
                dialog.show();
            }, __("Operations"));
        }

        // The primary workflow action is derived from persisted downstream documents.
        // This prevents old completed projects from exposing creation buttons again.
        add_contextual_workflow_action(frm);
    },

    meal_plan(frm) {
        populate_from_meal_plan(frm, true);
    },

    status(frm) {
        const now = frappe.datetime.now_datetime();
        if (frm.doc.status === "تحضير / Preparing" && !frm.doc.start_time) frm.set_value("start_time", now);
        if (frm.doc.status === "طبخ / Cooking" && !frm.doc.cooking_start_time) frm.set_value("cooking_start_time", now);
        if (frm.doc.status === "تغليف / Packaging" && !frm.doc.packaging_start_time) frm.set_value("packaging_start_time", now);
        if (["جاهز / Ready", "مكتمل / Completed"].includes(frm.doc.status) && !frm.doc.packaging_end_time) frm.set_value("packaging_end_time", now);
        if (frm.doc.status === "مكتمل / Completed" && !frm.doc.end_time) frm.set_value("end_time", now);
    }
});

function add_contextual_workflow_action(frm) {
    frappe.call({
        method: "wafd_one.operations.get_batch_workflow_state",
        args: { batch_name: frm.doc.name },
        callback(r) {
            const state = r.message || {stage: "production"};
            if (state.stage === "delivered" && state.trip) {
                frm.page.set_primary_action(__("فتح التسليم المكتمل / Open Delivered Trip"), () =>
                    frappe.set_route("Form", "WAFD Delivery Trip", state.trip.name));
                return;
            }
            if (state.stage === "delivery" && state.trip) {
                frm.page.set_primary_action(__("فتح رحلة التوصيل / Open Delivery Trip"), () =>
                    frappe.set_route("Form", "WAFD Delivery Trip", state.trip.name));
                return;
            }
            if (state.stage === "loading" && state.loading) {
                frm.page.set_primary_action(__("فتح التحميل الموجود / Open Existing Loading"), () =>
                    frappe.set_route("Form", "WAFD Loading Record", state.loading.name));
                return;
            }
            if (state.stage === "packaging" && state.packaging) {
                frm.page.set_primary_action(__("فتح التغليف الموجود / Open Existing Packaging"), () =>
                    frappe.set_route("Form", "WAFD Packaging Record", state.packaging.name));
                return;
            }
            add_guided_production_action(frm);
        }
    });
}

function populate_from_meal_plan(frm, force = false) {
    if (!frm.doc.meal_plan || frm.__wafd_loading_plan) return;
    if (!force && frm.doc.recipe && frm.doc.batch_date && (frm.doc.material_requirements || []).length) return;
    frm.__wafd_loading_plan = true;
    frappe.call({
        method: "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.get_meal_plan_defaults",
        args: { meal_plan: frm.doc.meal_plan },
        freeze: true,
        freeze_message: __("Loading production requirements..."),
        callback(r) {
            const d = r.message || {};
            ["project", "daily_plan", "recipe", "batch_date", "planned_quantity", "kitchen", "source_warehouse", "materials_status", "total_material_cost"].forEach(field => {
                if (d[field] !== undefined) frm.set_value(field, d[field]);
            });
            set_child_rows(frm, "source_warehouses", d.source_warehouses || []);
            set_child_rows(frm, "material_requirements", d.material_requirements || []);
            set_child_rows(frm, "material_allocations", d.material_allocations || []);
            frm.refresh_fields();
            const shortages = (d.material_requirements || []).filter(row => Number(row.shortage_quantity || 0) > 0).length;
            frappe.show_alert({
                message: shortages ? `${__("Requirements loaded; shortages")}: ${shortages}` : __("Production requirements loaded"),
                indicator: shortages ? "orange" : "green"
            });
        },
        always() { frm.__wafd_loading_plan = false; }
    });
}

function set_child_rows(frm, fieldname, rows) {
    frm.clear_table(fieldname);
    rows.forEach(values => {
        const row = frm.add_child(fieldname);
        Object.keys(values).forEach(key => { row[key] = values[key]; });
    });
    frm.refresh_field(fieldname);
}

function route_to_packaging(result) {
    if (result.name) {
        frappe.set_route("Form", "WAFD Packaging Record", result.name);
    } else if (result.values) {
        frappe.new_doc("WAFD Packaging Record", result.values);
    }
}

function add_action(frm, label, method, args, on_success) {
    frm.add_custom_button(label, () => {
        frappe.call({
            method,
            args,
            freeze: true,
            callback(r) {
                if (r.message && on_success) on_success(r.message);
            }
        });
    }, __("Operations"));
}


function add_guided_production_action(frm) {
    frm.page.clear_primary_action();
    if (frm.is_new()) return;

    if (frm.doc.status === "مخطط / Planned") {
        frm.page.set_primary_action(__("صرف المواد وبدء الإنتاج / Issue Materials & Start Production"), () => {
            frappe.call({
                method: "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.check_material_availability",
                args: { batch_name: frm.doc.name },
                freeze: true,
                callback(check) {
                    const availability = check.message || {};
                    if (!availability.available) { show_shortage_resolution_dialog(frm, availability.shortages || []); return; }
                    frappe.call({
                method: "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.start_production",
                args: { batch_name: frm.doc.name },
                freeze: true,
                freeze_message: __("Checking stock, posting material issues and starting production..."),
                callback(r) {
                    const result = r.message || {};
                    if (result.started) {
                        frappe.show_alert({
                            message: `${__("Production started")}: ${result.movement_count || 0} ${__("material issue movement(s) posted")}`,
                            indicator: "green"
                        }, 6);
                    }
                    frm.reload_doc();
                }
            });
                }
            });
        });
        return;
    }

    if (["تحضير / Preparing", "طبخ / Cooking"].includes(frm.doc.status)) {
        frm.page.set_primary_action(__("إنهاء الإنتاج / Complete Production"), () => {
            const dialog = new frappe.ui.Dialog({
                title: __("Complete Production"),
                fields: [
                    { fieldname: "produced_quantity", fieldtype: "Int", label: __("Produced Qty"), reqd: 1, default: frm.doc.produced_quantity || frm.doc.planned_quantity },
                    { fieldname: "rejected_quantity", fieldtype: "Int", label: __("Rejected Qty"), default: frm.doc.rejected_quantity || 0 }
                ],
                primary_action_label: __("Complete"),
                primary_action(values) {
                    dialog.hide();
                    frappe.call({
                        method: "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.complete_production",
                        args: { batch_name: frm.doc.name, produced_quantity: values.produced_quantity, rejected_quantity: values.rejected_quantity },
                        freeze: true,
                        callback() { frm.reload_doc(); }
                    });
                }
            });
            dialog.show();
        });
        return;
    }

    if (frm.doc.quality_status !== "ناجح / Passed") {
        frm.page.set_primary_action(__("فحص الجودة / Quality Inspection"), () => {
            frappe.call({
                method: "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.create_quality_inspection",
                args: { batch_name: frm.doc.name },
                freeze: true,
                callback(r) {
                    const result = r.message || {};
                    if (result.name) frappe.set_route("Form", "WAFD Quality Inspection", result.name);
                    else if (result.values) frappe.new_doc("WAFD Quality Inspection", result.values);
                }
            });
        });
        return;
    }

    if (frm.doc.food_safety_release_status !== "مفرج / Released") {
        frm.page.set_primary_action(__("تسجيل قياس سلامة الغذاء / Record Food Safety Measurement"), () => {
            frappe.call({
                method: "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.prepare_ccp_check",
                args: { batch_name: frm.doc.name },
                freeze: true,
                callback(r) {
                    const result = r.message || {};
                    if (result.name) frappe.set_route("Form", "WAFD CCP Check", result.name);
                    else if (result.values) frappe.new_doc("WAFD CCP Check", result.values);
                }
            });
        });
        return;
    }

    frm.page.set_primary_action(__("اعتماد الإنتاج والانتقال للتغليف / Approve & Continue to Packaging"), () => {
        if (frm.__wafd_transition_busy) return;
        frm.__wafd_transition_busy = true;
        frappe.call({
            method: "wafd_one.operations.create_packaging_record",
            args: { batch_name: frm.doc.name },
            freeze: true,
            callback(r) { route_to_packaging(r.message || {}); },
            always() { frm.__wafd_transition_busy = false; }
        });
    });
}


function show_shortage_resolution_dialog(frm, shortages) {
    const rows = shortages.map((x, i) => ({
        ingredient: x.ingredient,
        warehouse: x.warehouse || "",
        required: flt(x.quantity || x.required_quantity),
        available: flt(x.available_quantity),
        shortage: flt(x.shortage_quantity),
        quantity: flt(x.shortage_quantity),
        uom: x.uom || "",
        unit_cost: 0
    }));
    const dialog = new frappe.ui.Dialog({
        title: __("معالجة عجز المخزون / Resolve Stock Shortage"),
        size: "extra-large",
        fields: [
            { fieldname:"notice", fieldtype:"HTML", options:`<div class="alert alert-warning">${__("يمكن لمسؤول المخزون إضافة العجز فورًا بحركة استلام موثقة، أو فتح الأصناف لمعالجتها يدويًا.")}</div>` },
            { fieldname:"items", fieldtype:"Table", label:__("الأصناف الناقصة"), cannot_add_rows:1, cannot_delete_rows:1,
              fields:[
                {fieldname:"ingredient",fieldtype:"Link",options:"WAFD Ingredient",label:__("الصنف"),in_list_view:1,read_only:1},
                {fieldname:"required",fieldtype:"Float",label:__("المطلوب"),in_list_view:1,read_only:1},
                {fieldname:"available",fieldtype:"Float",label:__("المتاح"),in_list_view:1,read_only:1},
                {fieldname:"shortage",fieldtype:"Float",label:__("العجز"),in_list_view:1,read_only:1},
                {fieldname:"quantity",fieldtype:"Float",label:__("الكمية المضافة"),in_list_view:1,reqd:1},
                {fieldname:"unit_cost",fieldtype:"Currency",label:__("تكلفة الوحدة"),in_list_view:1},
                {fieldname:"uom",fieldtype:"Data",label:__("الوحدة"),in_list_view:1,read_only:1}
              ]},
            { fieldname:"reason", fieldtype:"Small Text", label:__("سبب الإضافة"), default:__("إضافة فورية لمعالجة عجز دفعة الإنتاج") }
        ],
        primary_action_label: __("إضافة للمخزون وإعادة الفحص"),
        primary_action(values) {
            dialog.hide();
            frappe.call({
                method:"wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.add_shortage_stock",
                args:{batch_name:frm.doc.name, additions:values.items, reason:values.reason},
                freeze:true, freeze_message:__("جارٍ تسجيل الاستلام وإعادة فحص المخزون..."),
                callback(r){
                    const result=r.message||{};
                    if(result.available){
                        frappe.show_alert({message:__("تمت إضافة الكميات وأصبح المخزون كافيًا"),indicator:"green"},6);
                        frm.reload_doc();
                    } else {
                        frappe.msgprint({title:__("ما زال هناك عجز"),indicator:"orange",message:__("تم تسجيل الإضافة، لكن بقي عجز في بعض الأصناف. أعد المحاولة بعد مراجعة الكميات.")});
                        frm.reload_doc();
                    }
                }
            });
        },
        secondary_action_label: __("فتح حركات المخزون"),
        secondary_action(){ frappe.set_route("List","WAFD Stock Movement"); }
    });
    dialog.fields_dict.items.df.data=rows;
    dialog.fields_dict.items.grid.refresh();
    dialog.show();
}
