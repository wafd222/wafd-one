"""Force synchronization of WAFD ONE Phase 1 DocTypes.

This patch is intentionally executed in the post-model-sync section. It repairs
sites where the app code was deployed but the DocType metadata was not loaded
into the database, then rebuilds the workspace only after every target exists.
"""

import frappe

from wafd_one.setup import apply_setup


# Child tables and independent masters first, then documents that link to them.
PHASE_ONE_DOCTYPE_FILES = (
    "wafd_mission",
    "wafd_hotel",
    "wafd_supplier",
    "wafd_ingredient",
    "wafd_recipe_item",
    "wafd_recipe",
    "wafd_meal_plan_item",
    "wafd_project_hotel",
    "wafd_project_service",
    "wafd_catering_project",
    "wafd_contract",
    "wafd_meal_plan",
)


def execute():
    for doctype_file in PHASE_ONE_DOCTYPE_FILES:
        frappe.reload_doc(
            "wafd_one",
            "doctype",
            doctype_file,
            force=True,
            reset_permissions=True,
        )

    # Reload the two mutually-linked documents once more after both exist.
    frappe.reload_doc(
        "wafd_one", "doctype", "wafd_catering_project", force=True, reset_permissions=True
    )
    frappe.reload_doc(
        "wafd_one", "doctype", "wafd_contract", force=True, reset_permissions=True
    )

    apply_setup(force_rebuild=True, assign_manager_access=True)
    frappe.clear_cache()
