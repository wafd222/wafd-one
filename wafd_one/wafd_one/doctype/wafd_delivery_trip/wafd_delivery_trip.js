frappe.ui.form.on("WAFD Delivery Trip", {    refresh(frm) {
        if (frm.is_new()) return;
        add_guided_trip_action(frm);
        frm.add_custom_button(__("Create / Open Delivery Receipt"), () => {
            const createProof = () => frappe.call({
                method: "wafd_one.operations.create_delivery_proof",
                args: { trip_name: frm.doc.name },
                freeze: true,
                callback(r) {
                    const result = r.message || {};
                    if (result.name) frappe.set_route("Form", "WAFD Delivery Proof", result.name);
                    else if (result.values) frappe.new_doc("WAFD Delivery Proof", result.values);
                }
            });
            if (["مخططة / Planned", "تم التحميل / Loaded"].includes(frm.doc.status)) {
                frappe.call({
                    method: "wafd_one.operations.set_trip_status",
                    args: { trip_name: frm.doc.name, status: "في الطريق / In Transit" },
                    freeze: true,
                    callback: createProof
                });
            } else {
                createProof();
            }
        }, __("Operations"));
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


function add_guided_trip_action(frm) {
    frm.page.clear_primary_action();
    if (["مخططة / Planned", "تم التحميل / Loaded"].includes(frm.doc.status)) {
        frm.page.set_primary_action(__("بدء رحلة التوصيل / Start Delivery Trip"), () => update_status(frm, "في الطريق / In Transit"));
        return;
    }
    if (["في الطريق / In Transit", "متأخرة / Delayed"].includes(frm.doc.status)) {
        frm.page.set_primary_action(__("تسجيل الوصول وإنشاء إثبات التسليم / Arrive & Create Delivery Proof"), () => {
            frappe.call({
                method: "wafd_one.operations.set_trip_status",
                args: { trip_name: frm.doc.name, status: "وصلت / Arrived" },
                freeze: true,
                callback() {
                    frappe.call({
                        method: "wafd_one.operations.create_delivery_proof",
                        args: { trip_name: frm.doc.name },
                        freeze: true,
                        callback(r) {
                            const result = r.message || {};
                            if (result.name) frappe.set_route("Form", "WAFD Delivery Proof", result.name);
                            else if (result.values) frappe.new_doc("WAFD Delivery Proof", result.values);
                        }
                    });
                }
            });
        });
        return;
    }
    if (frm.doc.status === "وصلت / Arrived") {
        frm.page.set_primary_action(__("إنشاء إثبات التسليم / Create Delivery Proof"), () => {
            frappe.call({
                method: "wafd_one.operations.create_delivery_proof",
                args: { trip_name: frm.doc.name },
                freeze: true,
                callback(r) {
                    const result = r.message || {};
                    if (result.name) frappe.set_route("Form", "WAFD Delivery Proof", result.name);
                    else if (result.values) frappe.new_doc("WAFD Delivery Proof", result.values);
                }
            });
        });
    }
}
