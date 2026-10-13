"""RC157: final permission/UI hardening and confirmed remaining fixes.

- Reapply the consolidated role matrix from the current JSON metadata.
- Restrict the executive dashboard to management/finance roles.
- Rebuild the shared workspace without privileged/financial shortcuts.
- Re-publish operational print templates, including delivery photo support.

Business logic fixes (closed-plan locking, undertaking auto-fill and trip timing)
are shipped in the DocType controllers and therefore apply immediately after
this migration without rewriting historical project records.
"""
import frappe


def execute():
    # RC156 is deliberately reused: it deletes stale Custom DocPerm rows before
    # reloading every WAFD DocType, so the RC157 JSON matrix becomes authoritative.
    from wafd_one.patches.v10_0_0_rc156.execute import execute as apply_permissions
    from wafd_one.patches.v10_0_0_rc72.execute import execute as publish_operational_templates
    from wafd_one.setup import rebuild_workspace_from_source

    apply_permissions()
    publish_operational_templates()
    rebuild_workspace_from_source()
    frappe.clear_cache()
