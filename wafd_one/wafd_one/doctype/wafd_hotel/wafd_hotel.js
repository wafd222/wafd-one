function wafd_focus_new_hotel_identity(frm) {
    if (!frm.is_new()) return;
    // Native Link creation on mobile can preserve the previous page scroll.
    // Always return the new Hotel form to its bilingual identity fields.
    setTimeout(() => {
        try {
            frm.scroll_to_field("hotel_name_ar");
            frm.fields_dict.hotel_name_ar?.$input?.trigger("focus");
        } catch (e) {}
    }, 120);
}

frappe.ui.form.on("WAFD Hotel", {
    onload(frm) {
        wafd_focus_new_hotel_identity(frm);
    },
    refresh(frm) {
        wafd_focus_new_hotel_identity(frm);
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
