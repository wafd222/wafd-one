function wafd_recalculate_invoice(frm) {
    const subtotal = flt(frm.doc.subtotal || 0);
    const tax_rate = flt(frm.doc.tax_rate || 0);
    const paid_amount = flt(frm.doc.paid_amount || 0);
    const tax_amount = flt(subtotal * tax_rate / 100, precision("tax_amount", frm.doc));
    const grand_total = flt(subtotal + tax_amount, precision("grand_total", frm.doc));
    const balance = Math.max(flt(grand_total - paid_amount, precision("balance", frm.doc)), 0);

    frm.set_value("tax_amount", tax_amount);
    frm.set_value("grand_total", grand_total);
    frm.set_value("balance", balance);

    if (frm.doc.status !== "ملغاة / Cancelled") {
        let status = "مسودة / Draft";
        if (grand_total > 0 && balance <= 0) {
            status = "مدفوعة / Paid";
        } else if (grand_total > 0 && paid_amount > 0) {
            status = "مدفوعة جزئياً / Partially Paid";
        } else if (grand_total > 0 && frm.doc.due_date && frm.doc.due_date < frappe.datetime.get_today()) {
            status = "متأخرة / Overdue";
        } else if (grand_total > 0 && !frm.is_new()) {
            status = "مرسلة / Sent";
        }
        frm.set_value("status", status);
    }
}

frappe.ui.form.on("WAFD Invoice", {
    refresh(frm) {
        wafd_recalculate_invoice(frm);

        if (frm.is_new() || frm.doc.status === "ملغاة / Cancelled") return;

        if (flt(frm.doc.grand_total) <= 0) {
            frm.add_custom_button(__("Recalculate Invoice"), () => {
                frappe.call({
                    method: "wafd_one.finance.rebuild_invoice",
                    args: { invoice_name: frm.doc.name },
                    freeze: true,
                    callback(r) {
                        if (r.message) frm.reload_doc();
                    }
                });
            }, __("Operations"));
            return;
        }

        if (flt(frm.doc.balance) > 0) {
            frm.add_custom_button(__("Register Payment"), () => {
                frappe.new_doc("WAFD Payment", {
                    invoice: frm.doc.name,
                    project: frm.doc.project,
                    invoice_total: frm.doc.grand_total,
                    previously_paid: frm.doc.paid_amount,
                    outstanding_before: frm.doc.balance,
                    payment_date: frappe.datetime.get_today(),
                    amount: frm.doc.balance,
                    status: "مسودة / Draft"
                });
            }, __("Operations"));
        }
    },

    subtotal(frm) {
        wafd_recalculate_invoice(frm);
    },

    tax_rate(frm) {
        wafd_recalculate_invoice(frm);
    },

    paid_amount(frm) {
        wafd_recalculate_invoice(frm);
    },

    due_date(frm) {
        wafd_recalculate_invoice(frm);
    },

    validate(frm) {
        wafd_recalculate_invoice(frm);
    }
});

frappe.ui.form.on("WAFD Invoice Item", {
    delivered_quantity(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "amount", flt(row.delivered_quantity) * flt(row.unit_price));
        wafd_recalculate_item_subtotal(frm);
    },

    unit_price(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "amount", flt(row.delivered_quantity) * flt(row.unit_price));
        wafd_recalculate_item_subtotal(frm);
    },

    items_remove(frm) {
        wafd_recalculate_item_subtotal(frm);
    }
});

function wafd_recalculate_item_subtotal(frm) {
    if (frm.doc.billing_basis !== "الكميات المسلمة / Delivered Quantities") return;
    const subtotal = (frm.doc.items || []).reduce((total, row) => total + flt(row.amount), 0);
    frm.set_value("subtotal", subtotal).then(() => wafd_recalculate_invoice(frm));
}
