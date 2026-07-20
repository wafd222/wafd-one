frappe.ui.form.on("WAFD Hotel", {
    refresh(frm) {
        if (frm.is_new()) return;
        frm.add_custom_button(__("تعهد جديد"), () => {
            frappe.new_doc("WAFD Hotel Undertaking", {
                hotel: frm.doc.name,
                supply_location: frm.doc.hotel_name
            });
        }, __("المستندات"));
    }
});
