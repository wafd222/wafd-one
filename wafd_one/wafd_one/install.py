import frappe

WAREHOUSES = [
    ("المطبخ المركزي", 1, None),
    ("مستودع المواد الجافة", 0, "المطبخ المركزي"),
    ("مستودع مواد التغليف", 0, "المطبخ المركزي"),
    ("مستودع المشروبات", 0, "المطبخ المركزي"),
    ("مستودع المنظفات", 0, "المطبخ المركزي"),
    ("مستودع الأدوات والمعدات", 0, "المطبخ المركزي"),
    ("مستودع الطوارئ", 0, "المطبخ المركزي"),
    ("ثلاجة الدجاج", 0, "المطبخ المركزي"),
    ("ثلاجة اللحوم", 0, "المطبخ المركزي"),
    ("ثلاجة الألبان", 0, "المطبخ المركزي"),
    ("ثلاجة الخضار والفواكه", 0, "المطبخ المركزي"),
]

def after_install():
    company = frappe.db.get_value("Company", {"company_name": "Wafd Almadinah"})
    if not company:
        return
    created = {}
    for name, is_group, parent_name in WAREHOUSES:
        existing = frappe.db.get_value("Warehouse", {"warehouse_name": name, "company": company})
        if existing:
            created[name] = existing
            continue
        parent = created.get(parent_name) if parent_name else frappe.db.get_value(
            "Warehouse", {"warehouse_name": "All Warehouses", "company": company}
        )
        doc = frappe.get_doc({
            "doctype": "Warehouse",
            "warehouse_name": name,
            "company": company,
            "is_group": is_group,
            "parent_warehouse": parent,
        })
        doc.insert(ignore_permissions=True)
        created[name] = doc.name
    frappe.db.commit()
