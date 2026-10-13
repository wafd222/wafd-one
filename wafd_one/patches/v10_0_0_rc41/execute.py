import json
import frappe
from wafd_one.document_studio import compile_template
from wafd_one.patches.v10_0_0_rc38.execute import invoice_canvas, undertaking_canvas, LOGO, LEGACY_UNDERTAKING_HTML

def execute():
    if frappe.db.exists('DocType','WAFD Document Template'):
        for category, canvas in [('Invoice',invoice_canvas()),('Hotel Undertaking',undertaking_canvas())]:
            for name in frappe.get_all('WAFD Document Template',filters={'document_category':category},pluck='name'):
                doc=frappe.get_doc('WAFD Document Template',name)
                doc.logo=LOGO; doc.page_size='A4'; doc.orientation='Portrait'; doc.direction='RTL'
                doc.margin_top_mm=doc.margin_right_mm=doc.margin_bottom_mm=doc.margin_left_mm=0
                doc.canvas_json=json.dumps(canvas,ensure_ascii=False)
                doc.compiled_html=compile_template(doc)
                doc.enabled=1; doc.is_default=1
                doc.save(ignore_permissions=True)
        frappe.clear_cache(doctype='WAFD Document Template')
    if frappe.db.exists('DocType','Custom Field'):
        pass
    if frappe.db.exists('DocType','Print Format'):
        for name in frappe.get_all('Print Format',filters={'doc_type':'WAFD Hotel Undertaking'},pluck='name'):
            frappe.db.set_value('Print Format',name,{'html':LEGACY_UNDERTAKING_HTML,'custom_format':1,'print_format_type':'Jinja','disabled':0},update_modified=False)
        frappe.clear_cache(doctype='Print Format')
