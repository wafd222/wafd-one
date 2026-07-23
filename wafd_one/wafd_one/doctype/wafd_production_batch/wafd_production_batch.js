frappe.ui.form.on("WAFD Production Batch", {
    setup(frm) {
        frm.set_query("warehouse", "source_warehouses", () => ({ filters: { status: "نشط / Active" } }));
    },
    refresh(frm) {
        if (frm.is_new()) return;

        frm.add_custom_button(__("New CCP Check"), () => {
            frappe.new_doc("WAFD CCP Check", {
                production_batch: frm.doc.name,
                check_time: frappe.datetime.now_datetime(),
                inspector: frappe.session.user
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

        if (frm.doc.quality_status === "ناجح / Passed") {
            add_action(frm, __("Create Packaging Record"),
                "wafd_one.operations.create_packaging_record",
                { batch_name: frm.doc.name }, result => {
                    if (result.name) {
                        frappe.set_route("Form", "WAFD Packaging Record", result.name);
                    } else if (result.values) {
                        frappe.new_doc("WAFD Packaging Record", result.values);
                    }
                });
        }
    },

    meal_plan(frm) {
        if (!frm.doc.meal_plan) return;
        frappe.db.get_value("WAFD Meal Plan", frm.doc.meal_plan, ["project", "recipe", "quantity"]).then(r => {
            if (!r.message) return;
            frm.set_value("project", r.message.project);
            frm.set_value("recipe", r.message.recipe);
            frm.set_value("planned_quantity", r.message.quantity);
        });
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
