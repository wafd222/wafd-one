frappe.ui.form.on("WAFD Mission", {
    refresh(frm) {
        if (frm.is_new()) return;
        frm.add_custom_button(__("شهادة شكر / Appreciation Certificate"), () => {
            const url = `/api/method/wafd_one.document_studio.download_pdf?template_name=${encodeURIComponent("شهادة شكر")}&doctype=${encodeURIComponent(frm.doctype)}&docname=${encodeURIComponent(frm.doc.name)}`;
            window.open(url, "_blank");
        }, __("الطباعة / Print"));
    }
});
