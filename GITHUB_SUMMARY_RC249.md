## WAFD ONE 10.0.0 RC249 — Direct Driver Home

RC249 fixes the post-login navigation sequence for drivers and other WAFD ONE
employees. The application now uses the canonical Frappe v16 Page route
`/app/wafd-role-home`, no longer captures that URL as a website route, redirects
legacy `/desk/wafd-role-home` bookmarks, and migrates persisted WAFD ONE desktop
icons to the corrected link. The role-aware PWA launcher and separate client
portal behavior are preserved. Regression checks cover guest, driver, manager,
mixed-role and client routing plus the complete employee access matrix.
