import frappe

@frappe.whitelist()
def get_batch_traceability(batch_name):
    batch = frappe.get_doc("WAFD Production Batch", batch_name)
    batch.check_permission("read")
    material_issue = None
    if batch.material_issue and frappe.db.exists("WAFD Stock Movement", batch.material_issue):
        movement = frappe.get_doc("WAFD Stock Movement", batch.material_issue)
        material_issue = {
            "name": movement.name,
            "posting_date": movement.posting_date,
            "source_warehouse": movement.source_warehouse,
            "items": [
                {
                    "ingredient": row.ingredient,
                    "quantity": row.quantity,
                    "uom": row.uom,
                    "lot_number": row.lot_number,
                    "supplier_batch_number": row.supplier_batch_number,
                    "production_date": row.production_date,
                    "expiry_date": row.expiry_date,
                }
                for row in movement.items
            ],
        }
    return {
        "batch": {
            "name": batch.name,
            "traceability_code": batch.traceability_code,
            "project": batch.project,
            "meal_plan": batch.meal_plan,
            "recipe": batch.recipe,
            "batch_date": batch.batch_date,
            "planned_quantity": batch.planned_quantity,
            "produced_quantity": batch.produced_quantity,
            "quality_status": batch.quality_status,
            "food_safety_release_status": batch.food_safety_release_status,
            "released_by": batch.released_by,
            "released_on": batch.released_on,
        },
        "material_issue": material_issue,
        "ccp_checks": frappe.get_all("WAFD CCP Check", filters={"production_batch": batch.name}, fields=["name", "ccp_type", "check_time", "measured_value", "unit", "minimum_limit", "maximum_limit", "compliance_status", "verification_status", "verified_by", "verified_on"]),
        "quality_inspections": frappe.get_all("WAFD Quality Inspection", filters={"production_batch": batch.name}, fields=["name", "inspection_date", "inspector", "result", "decision_time"]),
        "packaging_records": frappe.get_all("WAFD Packaging Record", filters={"production_batch": batch.name}, fields=["name", "packaging_date", "packed_quantity", "box_count"]),
        "delivery_trips": frappe.get_all("WAFD Delivery Trip", filters={"meal_plan": batch.meal_plan}, fields=["name", "hotel", "vehicle", "driver", "status", "actual_departure", "actual_arrival"]),
    }
