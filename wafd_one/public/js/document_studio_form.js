(function () {
  const supported = [
    'WAFD Hotel Undertaking', 'WAFD Contract', 'WAFD Invoice',
    'WAFD Catering Project', 'WAFD Production Batch', 'WAFD Meal Plan',
    'WAFD Loading Record', 'WAFD Delivery Proof', 'WAFD Mission'
  ];

  supported.forEach((doctype) => {
    frappe.ui.form.on(doctype, {
      refresh(frm) {
        if (frm.is_new()) return;
        frm.add_custom_button(__('Document Studio'), async () => {
          const r = await frappe.call('wafd_one.document_studio.get_default_template', {
            reference_doctype: frm.doctype
          });
          if (!r.message) {
            frappe.msgprint(__('No document template is configured for this DocType.'));
            return;
          }
          frappe.route_options = { template: r.message };
          frappe.set_route('wafd-document-studio');
        }, __('Print & Documents'));

        frm.add_custom_button(__('Template Preview'), async () => {
          const r = await frappe.call('wafd_one.document_studio.get_default_template', {
            reference_doctype: frm.doctype
          });
          if (!r.message) {
            frappe.msgprint(__('No document template is configured for this DocType.'));
            return;
          }
          const params = new URLSearchParams({
            template_name: r.message,
            doctype: frm.doctype,
            docname: frm.docname
          });
          window.open(`/api/method/wafd_one.document_studio.preview_html?${params.toString()}`, '_blank');
        }, __('Print & Documents'));

        frm.add_custom_button(__('Template PDF'), async () => {
          const r = await frappe.call('wafd_one.document_studio.get_default_template', {
            reference_doctype: frm.doctype
          });
          if (!r.message) {
            frappe.msgprint(__('No document template is configured for this DocType.'));
            return;
          }
          const params = new URLSearchParams({
            template_name: r.message,
            doctype: frm.doctype,
            docname: frm.docname
          });
          window.open(`/api/method/wafd_one.document_studio.download_pdf?${params.toString()}`, '_blank');
        }, __('Print & Documents'));
      }
    });
  });
})();
