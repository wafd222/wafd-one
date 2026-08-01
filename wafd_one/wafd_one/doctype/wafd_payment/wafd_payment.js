frappe.ui.form.on("WAFD Payment", {
    refresh(frm) {
        toggle_reference_requirement(frm);
        if (frm.doc.docstatus === 0 && !frm.is_new()) {
            frm.page.set_primary_action(__("اعتماد التحصيل وإغلاق الدورة / Submit Payment & Finish"), async () => {
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

    payment_method(frm) {
        toggle_reference_requirement(frm);
        if (frm.doc.payment_method === "نقدي / Cash" && frm.doc.reference_number) {
            frm.set_value("reference_number", "");
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
    },

    on_submit(frm) {
        frappe.show_alert({ message: __("تم اعتماد التحصيل وإغلاق الدورة بنجاح"), indicator: "green" }, 7);
        const project = frm.doc.project;
        if (project) setTimeout(() => frappe.set_route("Form", "WAFD Catering Project", project), 500);
        else setTimeout(() => frappe.set_route("wafd-one-dashboard"), 500);
    }
});

function toggle_reference_requirement(frm) {
    const required = !!frm.doc.payment_method && frm.doc.payment_method !== "نقدي / Cash";
    frm.toggle_reqd("reference_number", required);
    frm.toggle_display("reference_number", required || !!frm.doc.reference_number);
}
