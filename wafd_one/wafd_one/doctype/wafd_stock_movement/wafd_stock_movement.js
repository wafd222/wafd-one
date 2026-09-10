function wafd_is_storekeeper_view() {
    const roles = new Set(frappe.user_roles || []);
    return roles.has("WAFD Storekeeper")
        && !roles.has("System Manager")
        && !roles.has("WAFD Operations Manager");
}

function wafd_simplify_stock_movement(frm) {
    if (!wafd_is_storekeeper_view()) return;

    const type = frm.doc.movement_type;
    const receipt = type === "استلام / Receipt";
    const issue = type === "صرف / Issue";
    const transfer = type === "تحويل / Transfer";

    frm.set_df_property("movement_type", "label", "العملية");
    frm.set_df_property("posting_date", "label", "التاريخ");
    frm.set_df_property("source_warehouse", "label", transfer ? "من مستودع" : "المستودع");
    frm.set_df_property("target_warehouse", "label", transfer ? "إلى مستودع" : "المستودع");
    frm.set_df_property("reference_name", "label", "أمر الشراء");
    frm.set_df_property("items", "label", "المواد والكميات");

    frm.toggle_display("source_warehouse", issue || transfer);
    frm.toggle_display("target_warehouse", receipt || transfer || type === "تسوية / Adjustment");
    frm.toggle_display("reference_type", false);
    frm.toggle_display("reference_name", receipt);
    frm.toggle_display("issue_purpose", issue);
    frm.toggle_display("issued_to_user", issue);
    frm.toggle_display("project", !!frm.doc.project);
    frm.toggle_display("production_batch", !!frm.doc.production_batch);
    ["total_amount", "status", "posted_by", "posted_on", "is_pre_go_live_test"].forEach((field) => frm.toggle_display(field, false));

    const grid = frm.fields_dict.items && frm.fields_dict.items.grid;
    if (grid) {
        ["lot_number", "supplier_batch_number", "production_date", "traceability_notes"].forEach((field) => {
            grid.update_docfield_property(field, "hidden", 1);
        });
        ["ingredient", "quantity", "uom", "unit_cost", "expiry_date", "receiving_temperature"].forEach((field) => {
            grid.update_docfield_property(field, "hidden", 0);
        });
    }

    if (receipt && !frm.doc.reference_type) {
        frm.set_value("reference_type", "WAFD Purchase Order");
    }
}

frappe.ui.form.on("WAFD Stock Movement", {
    setup(frm) {
        if (!wafd_is_storekeeper_view()) return;
        frm.set_query("reference_name", () => ({
            filters: {
                status: ["in", ["معتمد / Approved", "مرسل / Sent", "مستلم جزئياً / Partially Received"]],
            },
        }));
    },
    refresh(frm) {
        wafd_simplify_stock_movement(frm);
        if (frm.is_new() || frm.doc.status !== "مسودة / Draft") return;
        frm.add_custom_button(__("ترحيل وتحديث الرصيد"), () => {
            frappe.confirm(__("هل تريد اعتماد الحركة وتحديث رصيد المخزون؟"), () => {
                frappe.call({
                    method: "wafd_one.wafd_one.doctype.wafd_stock_movement.wafd_stock_movement.post_movement",
                    args: { movement_name: frm.doc.name },
                    freeze: true,
                    freeze_message: __("جارٍ تحديث رصيد المخزون..."),
                    callback(r) {
                        if (r.message) {
                            frappe.show_alert({ message: __("تم تحديث رصيد المخزون"), indicator: "green" });
                            frm.reload_doc();
                        }
                    }
                });
            });
        }, __("المخزون"));
    },
    movement_type(frm) {
        if (frm.doc.movement_type !== "صرف / Issue") {
            frm.set_value("issue_purpose", "");
            frm.set_value("issued_to_user", "");
        }
        wafd_simplify_stock_movement(frm);
    },
    reference_name(frm) {
        if (!wafd_is_storekeeper_view()
            || frm.doc.movement_type !== "استلام / Receipt"
            || frm.doc.reference_type !== "WAFD Purchase Order"
            || !frm.doc.reference_name
            || !frm.is_new()) return;
        frappe.call({
            method: "wafd_one.wafd_one.doctype.wafd_purchase_order.wafd_purchase_order.create_goods_receipt",
            args: { purchase_order_name: frm.doc.reference_name },
            freeze: true,
            freeze_message: __("جارٍ تحميل مواد أمر الشراء..."),
            callback(r) {
                if (!r.message || !r.message.name) return;
                frappe.set_route("Form", "WAFD Stock Movement", r.message.name);
                frappe.show_alert({ message: __("تم تحميل المستودع والمواد والكميات تلقائيًا"), indicator: "green" });
            },
        });
    },
});

frappe.ui.form.on("WAFD Stock Movement Item", {
    ingredient(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.ingredient) {
            frappe.model.set_value(cdt, cdn, "uom", "");
            return;
        }
        frappe.db.get_value("WAFD Ingredient", row.ingredient, "uom").then((r) => {
            if (r.message && r.message.uom) {
                frappe.model.set_value(cdt, cdn, "uom", r.message.uom);
            }
        });
    },
});

frappe.ui.form.on("WAFD Stock Movement", {
  source_warehouse(frm) {
    if (!frm.doc.source_warehouse || frm.doc.movement_type !== "صرف / Issue") return;
    frappe.db.get_value("WAFD Warehouse", frm.doc.source_warehouse, "warehouse_type").then(r => {
      if (r.message && r.message.warehouse_type === "نظافة / Cleaning") {
        frm.set_value("issue_purpose", "نظافة / Cleaning");
      }
    });
  },
});
