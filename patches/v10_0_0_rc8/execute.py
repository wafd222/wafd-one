import frappe


def execute():
    """Repair linked project dates/services from their authoritative contracts."""
    projects = frappe.get_all("WAFD Catering Project", filters={"contract": ["is", "set"]}, pluck="name")
    for name in projects:
        project = frappe.get_doc("WAFD Catering Project", name)
        if not frappe.db.exists("WAFD Contract", project.contract):
            continue
        contract = frappe.get_doc("WAFD Contract", project.contract)
        changed = False
        for field in ("start_date", "end_date", "primary_hotel", "beneficiary_count"):
            source = "hotel" if field == "primary_hotel" else field
            value = contract.get(source)
            if value not in (None, "") and project.get(field) != value:
                project.set(field, value)
                changed = True
        # Repair only projects that have not entered production.
        has_production = frappe.db.exists("WAFD Production Batch", {"project": project.name})
        if contract.services and not has_production:
            project.set("services", [])
            for row in contract.services:
                project.append("services", {
                    "service_type": row.service_type,
                    "meal_name": row.meal_name,
                    "service_time": row.service_time,
                    "delivery_lead_minutes": row.delivery_lead_minutes,
                    "packaging_type": row.packaging_type,
                    "recipe": row.recipe,
                    "service_start_date": row.service_start_date,
                    "service_end_date": row.service_end_date,
                    "service_days": row.service_days,
                    "beneficiaries": row.beneficiaries,
                    "meals_per_person_per_day": row.meals_per_person_per_day,
                    "total_meals": row.total_meals,
                    "unit_price": row.unit_price,
                    "estimated_revenue": row.estimated_revenue,
                    "notes": row.notes,
                })
            changed = True
        if changed:
            project.flags.ignore_validate_update_after_submit = True
            project.save(ignore_permissions=True)
    frappe.clear_cache(doctype="WAFD Catering Project")
    frappe.clear_cache(doctype="WAFD Daily Meal Plan")
