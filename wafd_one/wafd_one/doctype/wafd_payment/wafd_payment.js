frappe.ui.form.on("WAFD Payment", {
    refresh(frm) {
        if (frm.doc.docstatus === 0 && !frm.is_new()) {
            frm.page.set_primary_action(__("اعتماد التحصيل / Submit Payment"), async () => {
                await frm.save();
                await frm.savesubmit();
            });
        }
        if (frm.doc.docstatus === 1 && frm.doc.invoice) {
            frm.add_custom_button(__("فتح الفاتورة / Open Invoice"), () => {
                frappe.set_route("Form", "WAFD Invoice", frm.doc.invoice);
            });
        }
    },

    invoice(frm) {
        if (!frm.doc.invoice) return;
        frappe.call({
            method: "wafd_one.finance.get_invoice_totals",
            args: { invoice_name: frm.doc.invoice },
            callback(r) {
                if (!r.message) return;
                frm.set_value("project", r.message.project);
                frm.set_value("invoice_total", r.message.invoice_total);
                frm.set_value("previously_paid", r.message.paid_amount);
                frm.set_value("outstanding_before", r.message.balance);
                frm.set_value("amount", r.message.balance > 0 ? r.message.balance : 0);
                if (r.message.balance <= 0) {
                    frappe.msgprint({
                        title: __("الفاتورة مدفوعة بالكامل"),
                        indicator: "red",
                        message: __("لا يمكن تسجيل تحصيل إضافي لهذه الفاتورة / This invoice has no outstanding balance.")
                    });
                }
            }
        });
    }
});
