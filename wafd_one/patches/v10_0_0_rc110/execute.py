import frappe


def execute():
    """RC110 contains hook-only deployment performance improvements."""
    # Do not leave the emergency full-repair mode enabled after an upgrade.
    if frappe.conf.get("wafd_one_full_post_migrate"):
        frappe.log_error(
            "wafd_one_full_post_migrate remains enabled in site_config.json; "
            "disable it after the repair deployment to retain fast migrations.",
            "WAFD ONE deployment performance",
        )
