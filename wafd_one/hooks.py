app_name = "wafd_one"
app_title = "WAFD ONE"
app_publisher = "Wafd Almadinah"
app_description = "Integrated catering operations, projects, production, quality, fleet, delivery and finance management"
app_email = "wafd.almadinah@gmail.com"
app_license = "proprietary"
app_logo_url = "/assets/wafd_one/images/wafd-one-logo.svg"
app_color = "#B38A3E"

add_to_apps_screen = [
    {
        "name": "wafd_one",
        "logo": "/assets/wafd_one/images/wafd-one-logo.svg",
        "title": "WAFD ONE",
        "route": "/app/wafd-one-dashboard",
        "has_permission": "wafd_one.api.check_app_permission",
    }
]

after_install = "wafd_one.setup.after_install"
before_migrate = "wafd_one.setup.before_migrate"
after_migrate = "wafd_one.setup.after_migrate"

page_js = {
    "wafd-one-dashboard": "public/js/wafd_one_dashboard.js",
}

page_css = {
    "wafd-document-studio": "wafd_one/page/wafd_document_studio/wafd_document_studio.css",
}
app_include_css = ["/assets/wafd_one/css/wafd_one_dashboard.css"]


doctype_js = {
    "WAFD Hotel Undertaking": "public/js/document_studio_form.js",
    "WAFD Contract": "public/js/document_studio_form.js",
    "WAFD Invoice": "public/js/document_studio_form.js",
    "WAFD Catering Project": "public/js/document_studio_form.js",
    "WAFD Production Batch": "public/js/document_studio_form.js",
    "WAFD Meal Plan": "public/js/document_studio_form.js",
    "WAFD Loading Record": "public/js/document_studio_form.js",
    "WAFD Delivery Proof": "public/js/document_studio_form.js",
    "WAFD Mission": "public/js/document_studio_form.js",
}


doc_events = {
    doctype: {
        "after_insert": "wafd_one.governance.audit_after_insert",
        "on_update": "wafd_one.governance.audit_on_update",
        "on_trash": "wafd_one.governance.audit_on_trash",
    }
    for doctype in (
        "WAFD Contract", "WAFD Catering Project", "WAFD Meal Plan",
        "WAFD Production Batch", "WAFD Purchase Order", "WAFD Stock Movement",
        "WAFD Delivery Trip", "WAFD Delivery Proof", "WAFD Quality Inspection",
        "WAFD CCP Check", "WAFD Invoice", "WAFD Payment", "WAFD Project Cost",
        "WAFD Project Revenue", "WAFD Approval Request",
    )
}


scheduler_events = {
    "daily": [
        "wafd_one.finance.refresh_overdue_invoices",
        "wafd_one.costing.daily_costing_refresh",
    ]
}
