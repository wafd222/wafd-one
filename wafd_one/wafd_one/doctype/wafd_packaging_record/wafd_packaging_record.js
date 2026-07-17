frappe.ui.form.on("WAFD Packaging Record", {
    onload(frm) {
        populate_from_batch(frm);
    },

    production_batch(frm) {
        populate_from_batch(frm, true);
    },

    refresh(frm) {
        if (frm.is_new()) {
            populate_from_batch(frm);
            return;
        }
        if (frm.doc.status === "مكتمل / Completed") {
            frm.add_custom_button(__("Create Loading Record"), () => {
                frappe.call({
                    method: "wafd_one.operations.create_loading_record",
                    args: { packaging_name: frm.doc.name },
                    freeze: true,
                    callback(r) {
                        const result = r.message || {};
                        if (result.name) {
                            frappe.set_route("Form", "WAFD Loading Record", result.name);
                        } else if (result.values) {
                            frappe.new_doc("WAFD Loading Record", result.values);
                        }
                    }
                });
            }, __("Operations"));
        }
    }
});

function populate_from_batch(frm, force = false) {
    if (!frm.doc.production_batch) return;
    if (!force && frm.doc.planned_quantity) return;

    frappe.db.get_value(
        "WAFD Production Batch",
        frm.doc.production_batch,
        ["project", "meal_plan", "batch_date", "planned_quantity", "produced_quantity", "packed_quantity", "box_count", "units_per_box", "packaging_supervisor"]
    ).then(r => {
        const d = r.message || {};
        const quantity = cint(d.produced_quantity) || cint(d.planned_quantity);
        frm.set_value("project", d.project);
        frm.set_value("meal_plan", d.meal_plan);
        frm.set_value("packaging_date", frm.doc.packaging_date || d.batch_date || frappe.datetime.get_today());
        frm.set_value("planned_quantity", quantity);
        if (!frm.doc.packed_quantity) frm.set_value("packed_quantity", cint(d.packed_quantity) || quantity);
        if (!frm.doc.box_count && d.box_count) frm.set_value("box_count", d.box_count);
        if (!frm.doc.units_per_box && d.units_per_box) frm.set_value("units_per_box", d.units_per_box);
        if (!frm.doc.supervisor && d.packaging_supervisor) frm.set_value("supervisor", d.packaging_supervisor);
    });
}

function cint(value) {
    return parseInt(value || 0, 10) || 0;
}
