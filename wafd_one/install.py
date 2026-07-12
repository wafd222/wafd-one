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
    for warehouse_name, is_group, parent_label in WAREHOUSES:
        existing = frappe.db.get_value(
            "Warehouse", {"warehouse_name": warehouse_name, "company": company}
        )
        if existing:
            created[warehouse_name] = existing
            continue

        if parent_label:
            parent_warehouse = created.get(parent_label) or frappe.db.get_value(
                "Warehouse", {"warehouse_name": parent_label, "company": company}
            )
        else:
            parent_warehouse = frappe.db.get_value(
                "Warehouse", {"warehouse_name": "All Warehouses", "company": company}
            )

        doc = frappe.get_doc({
            "doctype": "Warehouse",
            "warehouse_name": warehouse_name,
            "company": company,
            "is_group": is_group,
            "parent_warehouse": parent_warehouse,
        })
        doc.insert(ignore_permissions=True)
        created[warehouse_name] = doc.name

    frappe.db.commit()
