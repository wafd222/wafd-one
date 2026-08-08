from __future__ import annotations

import frappe


# Arabic short names used by older master-data loaders -> canonical WAFD
# Nationality document names. Values are resolved from the nationality master,
# not hard-coded, so the patch remains safe if bilingual names are adjusted.
def _canonical_nationality(short_arabic_name: str) -> str | None:
    if not frappe.db.exists("DocType", "WAFD Nationality"):
        return None
    value = frappe.db.get_value(
        "WAFD Nationality", {"country_name_ar": short_arabic_name}, "name"
    )
    if value:
        return value
    if frappe.db.exists("WAFD Nationality", short_arabic_name):
        return short_arabic_name
    return None


def execute():
    """Repair incomplete mission nationality links after the RC89 migrate fix.

    The patch is intentionally idempotent and does not overwrite a valid link.
    """
    if not frappe.db.exists("DocType", "WAFD Mission"):
        return

    meta = frappe.get_meta("WAFD Mission")
    country_field = meta.get_field("country")
    if not country_field or country_field.options != "WAFD Nationality":
        return

    for mission in frappe.get_all("WAFD Mission", fields=["name", "country"]):
        country = (mission.country or "").strip()
        if not country or frappe.db.exists("WAFD Nationality", country):
            continue
        canonical = _canonical_nationality(country)
        if canonical:
            frappe.db.set_value(
                "WAFD Mission", mission.name, "country", canonical,
                update_modified=False,
            )

    frappe.clear_cache()
