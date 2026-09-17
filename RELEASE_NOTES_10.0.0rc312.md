# WAFD ONE 10.0.0 RC312

## Remove legacy Iftar employee shortcut cards only

This release keeps RC311 intact and removes only the old Iftar shortcut cards that were still visible inside employee role homes after the RC144 Iftar restoration.

### Removed from employee role homes
- Delivery Supervisor: `توصيل إفطار الصائم` shortcut.
- Production Supervisor: `مطبخ إفطار الصائم` shortcut.
- Iftar Kitchen Supervisor: `تشغيل المطبخ اليومي` shortcut.
- Iftar Site Manager: `إدارة موقع الإفطار` shortcut.
- Iftar Supervisor: `تكليفي اليومي` shortcut.

### Preserved
- Main management Iftar entry and the restored RC144 Iftar program.
- Delivery Management, delivery schedules, locations, reports, drivers and offline sync.
- The existing delivery/Iftar backend integration and data fields; only the shortcut card is removed.
- Undertaking, Quotation, Inventory, Cleaning, Finance, users, languages and all unrelated modules.

### Migration scope
The RC312 patch reloads only `wafd_role_home` metadata and clears cache. It does not reload or mutate operational DocTypes.
