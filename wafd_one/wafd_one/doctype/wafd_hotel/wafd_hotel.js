
// RC227: deterministic mobile Quick Entry for WAFD Hotel.
// Frappe v16 builds Quick Entry from metadata, but on iOS the generated dialog
// can collapse/clip later mandatory fields.  Use Frappe's documented custom
// QuickEntry controller hook and explicitly render the three fields needed by
// undertaking officers.
if (frappe?.ui?.form?.QuickEntryForm) {
    frappe.ui.form.WAFDHotelQuickEntryForm = class WAFDHotelQuickEntryForm extends frappe.ui.form.QuickEntryForm {
        set_meta_and_mandatory_fields() {
            this.meta = frappe.get_meta(this.doctype);
            const get_df = (fieldname, fallback) => {
                const source = (this.meta.fields || []).find((df) => df.fieldname === fieldname);
                return Object.assign({}, source || fallback);
            };
            this.docfields = [
                get_df("hotel_name_ar", {
                    fieldname: "hotel_name_ar",
                    fieldtype: "Data",
                    label: __("اسم الفندق بالعربي / Arabic Hotel Name"),
                    reqd: 1,
                }),
                get_df("hotel_name_en", {
                    fieldname: "hotel_name_en",
                    fieldtype: "Data",
                    label: __("اسم الفندق بالإنجليزي / English Hotel Name"),
                    reqd: 1,
                }),
                get_df("district", {
                    fieldname: "district",
                    fieldtype: "Data",
                    label: __("الحي / District"),
                }),
            ];
            this.docfields[0].reqd = 1;
            this.docfields[0].hidden = 0;
            this.docfields[0].read_only = 0;
            this.docfields[1].reqd = 1;
            this.docfields[1].hidden = 0;
            this.docfields[1].read_only = 0;
            this.docfields[2].hidden = 0;
            this.docfields[2].read_only = 0;
        }

        render_dialog() {
            this.hide_full_form_button = true;
            super.render_dialog();
            this.set_title(__("إضافة فندق جديد / New Hotel"));
        }
    };
}

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
