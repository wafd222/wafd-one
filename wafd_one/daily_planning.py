from collections import defaultdict

import frappe
from frappe.utils import cint, flt


@frappe.whitelist()
def generate_daily_plans(project_name):
    project = frappe.get_doc("WAFD Catering Project", project_name)
    project.check_permission("write")
    if project.status in ("مكتمل / Completed", "ملغي / Cancelled"):
        frappe.throw("لا يمكن التخطيط لمشروع مكتمل أو ملغي / Cannot plan a completed or cancelled project")

    # Reuse the verified v8.2 scheduling engine first, then consolidate its
    # operational meal records into one daily plan per hotel and date.
    from wafd_one.wafd_one.doctype.wafd_catering_project.wafd_catering_project import generate_meal_plans
    generation = generate_meal_plans(project_name)

    meal_plans = frappe.get_all(
        "WAFD Meal Plan",
        filters={"project": project_name, "status": ["!=", "ملغي / Cancelled"]},
        fields=[
            "name", "hotel", "service_date", "meal_type", "quantity", "service_time",
            "menu_name", "recipe", "unit_price", "estimated_unit_cost",
        ],
        order_by="service_date asc, hotel asc, service_time asc",
    )
    if not meal_plans:
        frappe.throw("لا توجد خطط وجبات لتجميعها / No meal plans are available to consolidate")

    groups = defaultdict(list)
    for row in meal_plans:
        groups[(row.hotel, str(row.service_date))].append(row)

    created = updated = skipped = 0
    for (hotel, service_date), rows in groups.items():
        existing = frappe.db.get_value(
            "WAFD Daily Meal Plan",
            {"project": project_name, "hotel": hotel, "service_date": service_date},
            "name",
        )
        if existing:
            daily = frappe.get_doc("WAFD Daily Meal Plan", existing)
            # Never overwrite a plan that has entered production.
            if daily.status in ("قيد الإنتاج / In Production", "جاهزة / Ready", "تم التسليم / Delivered"):
                skipped += 1
                continue
            daily.set("meals", [])
            updated += 1
        else:
            daily = frappe.new_doc("WAFD Daily Meal Plan")
            daily.project = project_name
            daily.hotel = hotel
            daily.service_date = service_date
            daily.kitchen = project.default_kitchen
            daily.source_warehouse = project.default_source_warehouse
            daily.plan_title = f"{project.project_name} - {hotel} - {service_date}"
            created += 1

        for row in rows:
            daily.append("meals", {
                "meal_type": row.meal_type,
                "quantity": cint(row.quantity),
                "service_time": row.service_time,
                "menu_name": row.menu_name,
                "recipe": row.recipe,
                "unit_price": flt(row.unit_price),
                "estimated_unit_cost": flt(row.estimated_unit_cost),
                "meal_plan": row.name,
            })
        daily.save(ignore_permissions=True)

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "daily_plans": frappe.db.count("WAFD Daily Meal Plan", {"project": project_name}),
        "meal_plan_generation": generation,
    }


@frappe.whitelist()
def get_daily_plan_summary(project_name):
    project = frappe.get_doc("WAFD Catering Project", project_name)
    project.check_permission("read")
    rows = frappe.get_all(
        "WAFD Daily Meal Plan",
        filters={"project": project_name},
        fields=["status", "total_quantity", "total_value", "estimated_cost", "missing_recipe_count", "production_batch_count"],
    )
    return {
        "plans": len(rows),
        "total_quantity": sum(cint(x.total_quantity) for x in rows),
        "total_value": sum(flt(x.total_value) for x in rows),
        "estimated_cost": sum(flt(x.estimated_cost) for x in rows),
        "missing_recipes": sum(cint(x.missing_recipe_count) for x in rows),
        "production_batches": sum(cint(x.production_batch_count) for x in rows),
        "by_status": {status: sum(1 for x in rows if x.status == status) for status in sorted({x.status for x in rows})},
    }
