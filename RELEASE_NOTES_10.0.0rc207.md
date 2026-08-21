# WAFD ONE 10.0.0 RC207

## Final Mobile Entry & Undertaking Preview Hardening

- Keep the Undertaking Officer entry-route guard active until Frappe finishes restoring its initial route, preventing Safari from reopening the last undertaking after login/app launch.
- Release the entry guard only after the dedicated role home remains stable, avoiding redirect loops during normal in-app navigation.
- Preserve the fixed A4 transform-based undertaking preview introduced in RC206.
- Add explicit zoom out, zoom in, and fit-to-screen controls as a reliable iPhone fallback when browser pinch gestures are intercepted.
- Keep two-finger pinch and pan handling inside the preview while preserving the approved page layout.
- Preserve working approval, PDF save/share, signature, stamp, terms, and undertaking officer permissions.
- No schema/database migration changes.
