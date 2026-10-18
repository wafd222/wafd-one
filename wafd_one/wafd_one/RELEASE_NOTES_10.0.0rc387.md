# WAFD ONE RC387 — External viewer full-width shell correction

- Repairs the Frappe Desk mobile page **outer shell** (including an empty sidebar column), not only the cards inside it.
- Viewer-only, reversible DOM layout overrides on first load and every subsequent show. Frappe can mount responsive columns after page initialization.
- Retains RC385 route-guard fix and RC386 removal of the duplicate share-report button.
- No change to server-side permissions, operational stages, final-report action, or other roles.
- Live iPhone/Safari verification is still required after deployment.
