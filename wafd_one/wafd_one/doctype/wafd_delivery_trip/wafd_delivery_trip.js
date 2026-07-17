frappe.ui.form.on("WAFD Delivery Trip", {
    refresh(frm) {
        if (frm.is_new()) return;
        if (["مخططة / Planned", "تم التحميل / Loaded"].includes(frm.doc.status)) {
            frm.add_custom_button(__("Start Trip"), () => update_status(frm, "في الطريق / In Transit"), __("Operations"));
        }
        if (["في الطريق / In Transit", "متأخرة / Delayed"].includes(frm.doc.status)) {
            frm.add_custom_button(__("Mark Arrived"), () => update_status(frm, "وصلت / Arrived"), __("Operations"));
        }
        if (["في الطريق / In Transit", "وصلت / Arrived", "متأخرة / Delayed"].includes(frm.doc.status)) {
            frm.add_custom_button(__("Create Delivery Proof"), () => {
                frappe.call({
                    method: "wafd_one.operations.create_delivery_proof",
                    args: { trip_name: frm.doc.name },
                    freeze: true,
                    callback(r) {
                        const result = r.message || {};
                        if (result.name) {
                            frappe.set_route("Form", "WAFD Delivery Proof", result.name);
                        } else if (result.values) {
                            frappe.new_doc("WAFD Delivery Proof", result.values);
                        }
                    }
                });
            }, __("Operations"));
        }
    }
});
function update_status(frm, status) {
    frappe.call({
        method: "wafd_one.operations.set_trip_status",
        args: { trip_name: frm.doc.name, status },
        freeze: true,
        callback() { frm.reload_doc(); }
    });
}
