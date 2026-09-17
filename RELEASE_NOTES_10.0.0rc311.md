# WAFD ONE 10.0.0 RC311

## RC144 Iftar restoration on the current platform

This release restores the approved RC144 Iftar Saim operating experience while keeping the current RC310 platform and all unrelated modules intact.

### Restored from RC144
- Original Iftar project wizard behavior.
- Original daily operations workflow.
- Original Iftar report center.
- Original project and daily-operation controller behavior.
- Supervisor plans, assistants/owners, attendance and daily evidence flow used by the approved RC144 model.
- RC144 Iftar print formats and official daily report flow.
- RC144 Iftar visual styling for wizard, operations and report center.

### Compatibility safeguards
- Modern RC310 DocType schemas are retained so later delivery/driver integrations do not lose required database fields.
- The newer complex Iftar team UI is retired from navigation and old bookmarks redirect to the restored operations page.
- Post-RC144 Iftar row-level assignment hooks are disabled so they cannot hide records expected by the original workflow.
- Current WAFD ONE dashboard and role-home remain in place; only their Iftar links point to the restored Iftar operations screen.

### Not changed
- Driver offline-first and synchronization.
- Delivery Supervisor and delivery scheduling.
- Hotel Undertaking.
- Quotation.
- Storekeeper, inventory and cleaning workflows.
- Finance, invoicing and collections.
- User/language/mobile infrastructure.
