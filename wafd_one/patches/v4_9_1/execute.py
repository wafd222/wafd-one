import csv
from pathlib import Path
import frappe

def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_ingredient_price_observation", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_ingredient", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_recipe", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_hotel", force=True)
    path = Path(frappe.get_app_path("wafd_one")) / "reference_data" / "ingredient_price_observations_2026-07-19.csv"
    if path.exists():
        with path.open(encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                if not frappe.db.exists("WAFD Ingredient", {"ingredient_name": row["ingredient"]}):
                    continue
                ingredient = frappe.db.get_value("WAFD Ingredient", {"ingredient_name": row["ingredient"]}, "name")
                key = {"ingredient": ingredient, "retailer": row["retailer"], "brand_product": row["brand_product"], "observed_on": row["observed_on"]}
                if not frappe.db.exists("WAFD Ingredient Price Observation", key):
                    doc = frappe.new_doc("WAFD Ingredient Price Observation")
                    doc.update(key)
                    for field in ("package_quantity","package_uom","package_price","source_url","availability","price_type","verification_status"):
                        doc.set(field, row[field])
                    doc.insert(ignore_permissions=True)
    # Use median only where at least two verified observations exist; otherwise preserve existing operational cost.
    for ingredient in frappe.get_all("WAFD Ingredient", pluck="name"):
        prices = frappe.get_all("WAFD Ingredient Price Observation", filters={"ingredient": ingredient, "verification_status": "موثق من المصدر / Source Verified"}, fields=["normalized_unit_cost"], order_by="observed_on desc", limit=10)
        vals = sorted(float(p.normalized_unit_cost or 0) for p in prices if float(p.normalized_unit_cost or 0)>0)
        if len(vals) >= 2:
            n=len(vals); median=vals[n//2] if n%2 else (vals[n//2-1]+vals[n//2])/2
            frappe.db.set_value("WAFD Ingredient", ingredient, {"standard_cost": median,"cost_basis":"متوسط أسعار موثقة / Verified Price Average","cost_confidence":"متوسطة / Medium","cost_last_updated":frappe.utils.now_datetime()}, update_modified=False)
