# RC382 – External Iftar viewer card return navigation

- Added a native capture-phase click fallback limited to the authorized external Iftar viewer card on the role home page.
- The fallback routes to the existing read-only authority viewer and does not alter the viewer's permissions, reports, backend, or other role cards.
- Retained the existing delegated card handler for all other actions.
- Validation: JavaScript syntax and 46 automated tests passed. Live Frappe Cloud/iOS verification is still required.
