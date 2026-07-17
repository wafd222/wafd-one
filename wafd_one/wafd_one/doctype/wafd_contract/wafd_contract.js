frappe.ui.form.on("WAFD Contract", {
    refresh(frm) {
        if (frm.is_new()) return;
        if (frm.doc.project) {
            frm.add_custom_button(__("Open Project"), () => {
                frappe.set_route("Form", "WAFD Catering Project", frm.doc.project);
            }, __("Operations"));
        } else {
            frm.add_custom_button(__("Create Project"), () => {
                frappe.call({
                    method: "wafd_one.wafd_one.doctype.wafd_contract.wafd_contract.create_project_from_contract",
                    args: { contract_name: frm.doc.name },
                    freeze: true,
                    freeze_message: __("Creating project..."),
                    callback(r) {
                        if (r.message?.name) {
                            frappe.set_route("Form", "WAFD Catering Project", r.message.name);
                        }
                    }
                });
            }, __("Operations"));
        }
    }
});
