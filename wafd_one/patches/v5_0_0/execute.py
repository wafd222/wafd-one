import frappe

DEFAULT_MEALS = "إفطار / Breakfast\nغداء / Lunch\nعشاء / Dinner"
DEFAULT_LOGO = "/assets/wafd_one/images/wafd-almadinah-official.png"


def _has_column(doctype, fieldname):
    """Return True only when the physical database column exists."""
    try:
        if hasattr(frappe.db, "has_column"):
            return bool(frappe.db.has_column(doctype, fieldname))
    except Exception:
        pass

    try:
        table = f"tab{doctype}"
        return fieldname in frappe.db.get_table_columns(table)
    except Exception:
        return False


def execute():
    doctype = "WAFD Hotel Undertaking"
    table = f"tab{doctype}"

    # This is a post_model_sync patch. Still guard every operation so a partially
    # installed or previously inconsistent site can complete migration safely.
    if not frappe.db.exists("DocType", doctype):
        frappe.clear_cache()
        return

    has_docstatus = _has_column(doctype, "docstatus")

    if _has_column(doctype, "meal_types"):
        condition = " AND `docstatus` = 0" if has_docstatus else ""
        frappe.db.sql(
            f"""UPDATE `{table}`
                SET `meal_types` = %s
                WHERE COALESCE(`meal_types`, '') = ''{condition}""",
            (DEFAULT_MEALS,),
        )

    if _has_column(doctype, "company_logo"):
        frappe.db.sql(
            f"""UPDATE `{table}`
                SET `company_logo` = %s
                WHERE COALESCE(`company_logo`, '') = ''""",
            (DEFAULT_LOGO,),
        )

    frappe.clear_cache(doctype=doctype)
