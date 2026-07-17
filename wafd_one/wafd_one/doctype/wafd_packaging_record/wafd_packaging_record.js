frappe.ui.form.on("WAFD Packaging Record", {
    refresh(frm) {
        if (frm.is_new()) return;
        if (frm.doc.status === "مكتمل / Completed") {
            frm.add_custom_button(__("Create Loading Record"), () => {
                frappe.call({
                    method: "wafd_one.operations.create_loading_record",
                    args: { packaging_name: frm.doc.name },
                    freeze: true,
                    callback(r) {
                        const result = r.message || {};
                        if (result.name) {
                            frappe.set_route("Form", "WAFD Loading Record", result.name);
                        } else if (result.values) {
                            frappe.new_doc("WAFD Loading Record", result.values);
                        }
                    }
                });
            }, __("Operations"));
        }
    }
});
