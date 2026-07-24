frappe.ui.form.on("WAFD Hotel", {
    refresh(frm) {
        if (frm.is_new()) return;
        if (frm.doc.requires_catering_undertaking) {
            frm.add_custom_button(__("إنشاء تعهد إعاشة"), () => {
                frappe.new_doc("WAFD Hotel Undertaking", {
                    hotel: frm.doc.name,
                    supply_location: frm.doc.hotel_name || frm.doc.name,
                    undertaking_date: frappe.datetime.get_today()
                });
            }, __("المستندات"));
            frm.add_custom_button(__("عرض تعهدات الفندق"), () => {
                frappe.set_route("List", "WAFD Hotel Undertaking", {hotel: frm.doc.name});
            }, __("المستندات"));
        }
    }
});
