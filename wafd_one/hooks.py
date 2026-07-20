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
app_include_css = ["/assets/wafd_one/css/wafd_one_dashboard.css"]


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
