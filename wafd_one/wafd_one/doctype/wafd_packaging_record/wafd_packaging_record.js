frappe.ui.form.on("WAFD Packaging Record", {
    onload(frm) {
        populate_from_batch(frm);
    },

    production_batch(frm) {
        populate_from_batch(frm, true);
    },

    use_hot_cabinets(frm) {
        if (!frm.doc.use_hot_cabinets) {
            frm.clear_table("hot_cabinet_allocations");
            frm.set_value("hot_cabinet_count", 0);
            frm.set_value("hot_cabinet_sandwich_total", 0);
            frm.refresh_field("hot_cabinet_allocations");
        }
    },

    refresh(frm) {
        if (!frm.is_new() && frm.doc.box_manifest) {
            frm.add_custom_button(__("Show Box Manifest"), () => {
                frappe.msgprint({title: __("Box Manifest"), message: `<pre style="white-space:pre-wrap">${frappe.utils.escape_html(frm.doc.box_manifest)}</pre>`});
            }, __("Operations"));
        }
        if (frm.is_new()) {
            populate_from_batch(frm);
            return;
        }
        add_guided_packaging_action(frm);
        if (["مكتمل / Completed", "جاهز للتحميل / Ready for Loading"].includes(frm.doc.status)) {
            frm.add_custom_button(__("Create Loading Record"), () => {
                frappe.call({
                    method: "wafd_one.operations.create_loading_record",
                    args: { packaging_name: frm.doc.name },
                    freeze: true,
                    callback(r) {
                        const result = r.message || {};
                        open_loading_record(result);
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

frappe.ui.form.on("WAFD Hot Cabinet Allocation", {
    hot_cabinet(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.hot_cabinet) return;
        frappe.db.get_value("WAFD Hot Cabinet", row.hot_cabinet, ["capacity", "status"]).then(r => {
            const d = r.message || {};
            frappe.model.set_value(cdt, cdn, "capacity", cint(d.capacity));
            if (["صيانة / Maintenance", "غير نشط / Inactive"].includes(d.status)) {
                frappe.msgprint(__("هذا السخان غير متاح للاستخدام"));
            }
        });
    },
    sandwich_count(frm) { update_hot_cabinet_totals(frm); },
    hot_cabinet_allocations_remove(frm) { update_hot_cabinet_totals(frm); }
});

function update_hot_cabinet_totals(frm) {
    const rows = frm.doc.hot_cabinet_allocations || [];
    frm.set_value("hot_cabinet_count", rows.length);
    frm.set_value("hot_cabinet_sandwich_total", rows.reduce((sum, row) => sum + cint(row.sandwich_count), 0));
}


function add_guided_packaging_action(frm) {
    frm.page.clear_primary_action();
    if (frm.is_new()) return;
    frm.page.set_primary_action(__("اعتماد التغليف والانتقال للتحميل / Approve & Continue to Loading"), async () => {
        if (!frm.doc.label_verified) {
            frappe.msgprint(__("تحقق من ملصقات الصناديق أولاً ثم فعّل حقل التحقق / Verify box labels first."));
            return;
        }
        if (!cint(frm.doc.packed_quantity)) {
            await frm.set_value("packed_quantity", cint(frm.doc.planned_quantity));
        }
        await frm.save();
        const r = await frappe.call({
            method: "wafd_one.operations.create_loading_record",
            args: { packaging_name: frm.doc.name },
            freeze: true,
            freeze_message: __("جارٍ اعتماد التغليف وإنشاء سجل التحميل...")
        });
        const result = r.message || {};
        frappe.show_alert({ message: __("تم اعتماد التغليف — جارٍ فتح التحميل"), indicator: "green" }, 6);
        await open_loading_record(result);
    });
}


async function open_loading_record(result) {
    if (result.name) {
        await frappe.set_route("Form", "WAFD Loading Record", result.name);
        return;
    }
    if (result.values) {
        frappe.route_options = result.values;
        await frappe.new_doc("WAFD Loading Record", result.values);
        return;
    }
    frappe.throw(__("تعذر فتح سجل التحميل. أعد المحاولة أو راجع صلاحية إنشاء سجل التحميل."));
}
