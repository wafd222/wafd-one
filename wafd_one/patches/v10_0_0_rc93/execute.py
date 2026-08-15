"""RC93 final audit reconciliation.

This patch is deliberately idempotent.  It recalculates project financial
summaries from posted transactions and clears cached dashboard results after
the static QA fixes in this release.
"""

import frappe


def execute():
    if frappe.db.exists("DocType", "WAFD Catering Project"):
        from wafd_one.finance import refresh_project_financials

        for project_name in frappe.get_all(
            "WAFD Catering Project",
            filters={"status": ["!=", "ملغي / Cancelled"]},
            pluck="name",
        ):
            try:
                refresh_project_financials(project_name)
            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"RC93 financial reconciliation: {project_name}",
                )

    frappe.clear_cache()
