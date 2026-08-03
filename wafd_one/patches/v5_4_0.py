import frappe


def execute():
    if not frappe.db.table_exists("WAFD Ingredient"):
        return
    ingredients = frappe.get_all("WAFD Ingredient", pluck="name")
    for ingredient in ingredients:
        try:
            from wafd_one.wafd_one.doctype.wafd_ingredient_price.wafd_ingredient_price import refresh_ingredient_cost
            refresh_ingredient_cost(ingredient)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"WAFD v5.4 cost refresh: {ingredient}")
