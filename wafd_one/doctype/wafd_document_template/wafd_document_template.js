frappe.ui.form.on('WAFD Document Template', {
  refresh(frm) {
    if (!frm.is_new()) {
      frm.add_custom_button(__('Open Designer'), () => {
        frappe.route_options = { template: frm.doc.name };
        frappe.set_route('wafd-document-studio');
      }, __('Design'));
      frm.add_custom_button(__('Preview'), () => {
        const url = `/api/method/wafd_one.document_studio.preview_html?template_name=${encodeURIComponent(frm.doc.name)}`;
        window.open(url, '_blank');
      }, __('Design'));
    }
  }
});
