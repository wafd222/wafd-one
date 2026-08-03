frappe.ui.form.on("WAFD Receiving Note", {
    refresh(frm) {
        if (frm.is_new()) return;
        frm.add_custom_button(__("معاينة المستند"),()=>open_pdf(frm),__("Print & Documents"));
        frm.add_custom_button(__("طباعة PDF"),()=>open_pdf(frm),__("Print & Documents"));
        if (frm.doc.status !== "تم الاستلام / Received") {
            frm.page.set_primary_action(__("اعتماد الاستلام والانتقال للفاتورة / Confirm Receipt & Continue"), async () => {
                if (!frm.doc.receiver_name || !frm.doc.receiver_signature) {
                    frappe.msgprint(__("اسم المستلم وتوقيعه مطلوبان قبل اعتماد سند الاستلام.")); return;
                }
                await frm.set_value("status", "تم الاستلام / Received");
                await frm.save();
                open_invoice(frm);
            });
        } else {
            frm.page.set_primary_action(__("فتح / إنشاء الفاتورة / Open Invoice"), () => open_invoice(frm));
        }
    }
});
function open_invoice(frm){
    frappe.call({method:"wafd_one.finance.create_invoice_from_deliveries",args:{project_name:frm.doc.project},freeze:true,freeze_message:__("جارٍ إنشاء أو فتح الفاتورة..."),callback(r){if(r.message) frappe.set_route("Form","WAFD Invoice",r.message);}});
}
function open_pdf(frm){window.open(`/api/method/wafd_one.document_studio.download_pdf?template_name=WDT-00502&doctype=${encodeURIComponent(frm.doctype)}&docname=${encodeURIComponent(frm.doc.name)}`);}
