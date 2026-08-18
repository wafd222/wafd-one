app_name = "wafd_one"
app_title = "WAFD ONE"
app_publisher = "Wafd Almadinah"
app_description = "Integrated catering operations, projects, production, quality, fleet, delivery and finance management"
app_email = "wafd.almadinah@gmail.com"
app_license = "proprietary"
app_logo_url = "/assets/wafd_one/images/wafd-one-logo.svg"
app_color = "#B38A3E"
app_home = "/desk/wafd-role-home"

# RC169 external client portal. Website users never receive Desk access.
website_route_rules = [
    # RC182 compatibility: rescue RC181-installed shortcuts that still open the deprecated /app route.
    {"from_route": "/app/wafd-role-home", "to_route": "wafd_mobile"},
    {"from_route": "/wafd-client", "to_route": "wafd_client"},
    # Keep old installed PWA shortcuts valid; wafd_mobile performs the role-aware redirect.
    {"from_route": "/wafd-mobile", "to_route": "wafd_mobile"},
]

portal_menu_items = [
    {"title": "WAFD Client Portal", "route": "/wafd-client", "role": "WAFD Client Portal User"},
]

add_to_apps_screen = [
    {
        "name": "wafd_one",
        "logo": "/assets/wafd_one/images/wafd-one-logo.svg",
        "title": "WAFD ONE",
        "route": "/desk/wafd-role-home",
        "has_permission": "wafd_one.api.check_app_permission",
    }
]

after_install = "wafd_one.setup.after_install"
before_migrate = "wafd_one.setup.before_migrate"
after_migrate = "wafd_one.setup.after_migrate"

page_js = {
    # Dashboard page JS is loaded automatically from the standard Page path.
    # Do not inject the public copy as well, otherwise handlers and API calls run twice.
    "wafd-launch-center": "public/js/wafd_launch_center.js",
}

page_css = {
    "wafd-document-studio": "wafd_one/page/wafd_document_studio/wafd_document_studio.css",
    "wafd-launch-center": "public/css/wafd_launch_center.css",
}
app_include_js = [
    "/assets/wafd_one/js/wafd_hub.js",
    "/assets/wafd_one/js/wafd_pwa.js",
    "/assets/wafd_one/js/wafd_mobile_navigation.js",
]

app_include_css = [
    "/assets/wafd_one/css/wafd_mobile_navigation.css",
    "/assets/wafd_one/css/wafd_hub.css",
    "/assets/wafd_one/css/wafd_one_dashboard.css",
    "/assets/wafd_one/css/wafd_one_enterprise.css",
    "/assets/wafd_one/css/wafd_launch_center.css",
]


doctype_js = {
    "WAFD Hotel Undertaking": "public/js/document_studio_form.js",
    "WAFD Contract": "public/js/document_studio_form.js",
    "WAFD Invoice": "public/js/document_studio_form.js",
    "WAFD Catering Project": "public/js/document_studio_form.js",
    "WAFD Production Batch": "public/js/document_studio_form.js",
    "WAFD Meal Plan": "public/js/document_studio_form.js",
    "WAFD Daily Meal Plan": "public/js/document_studio_form.js",
    "WAFD Packaging Record": "public/js/document_studio_form.js",
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
        "WAFD Project Revenue", "WAFD Approval Request", "WAFD Procurement Plan", "WAFD Daily Meal Plan", "WAFD Kitchen",
    )
}


scheduler_events = {
    "daily": [
        "wafd_one.finance.refresh_overdue_invoices",
        "wafd_one.costing.daily_costing_refresh",
        "wafd_one.executive.refresh_executive_alerts",
    ],
    "hourly": [
        "wafd_one.operations.refresh_operational_statuses",
        "wafd_one.quality.refresh_food_safety_alerts",
    ]
}

# Row-level security for driver-facing delivery records.
permission_query_conditions = {
    "WAFD Delivery Trip": "wafd_one.driver_security.delivery_trip_query",
    "WAFD Delivery Proof": "wafd_one.driver_security.delivery_proof_query",
    "WAFD Warehouse": "wafd_one.cleaning_security.warehouse_query",
    "WAFD Stock Balance": "wafd_one.cleaning_security.stock_balance_query",
    "WAFD Stock Movement": "wafd_one.cleaning_security.stock_movement_query",
}

has_permission = {
    "WAFD Delivery Trip": "wafd_one.driver_security.delivery_trip_has_permission",
    "WAFD Delivery Proof": "wafd_one.driver_security.delivery_proof_has_permission",
    "WAFD Warehouse": "wafd_one.cleaning_security.warehouse_has_permission",
    "WAFD Stock Balance": "wafd_one.cleaning_security.stock_balance_has_permission",
    "WAFD Stock Movement": "wafd_one.cleaning_security.stock_movement_has_permission",
}
