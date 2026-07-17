frappe.ui.form.on("WAFD Production Batch", {
    refresh(frm) {
        if (frm.is_new()) return;

        frm.add_custom_button(__("Refresh Material Requirements"), () => {
            frappe.call({
                method: "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.refresh_material_requirements",
                args: { batch_name: frm.doc.name }, freeze: true,
                callback(r) { if (r.message) { frappe.show_alert({ message: __("Material requirements refreshed"), indicator: "green" }); frm.reload_doc(); } }
            });
        }, __("Operations"));

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

        frm.add_custom_button(__("Create Material Issue"), () => {
            frappe.call({
                method: "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.create_material_issue",
                args: { batch_name: frm.doc.name }, freeze: true, freeze_message: __("Preparing material issue..."),
                callback(r) { if (r.message) { frm.reload_doc(); frappe.set_route("Form", "WAFD Stock Movement", r.message.name); } }
            });
        }, __("Operations"));

        frm.add_custom_button(__("Quality Inspection"), () => {
            frappe.call({
                method: "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.create_quality_inspection",
                args: { batch_name: frm.doc.name },
                callback(r) { if (r.message) frappe.set_route("Form", "WAFD Quality Inspection", r.message.name); }
            });
        }, __("Operations"));
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
        if ((frm.doc.status === "جاهز / Ready" || frm.doc.status === "مكتمل / Completed") && !frm.doc.packaging_end_time) frm.set_value("packaging_end_time", now);
        if (frm.doc.status === "مكتمل / Completed" && !frm.doc.end_time) frm.set_value("end_time", now);
    }
});
