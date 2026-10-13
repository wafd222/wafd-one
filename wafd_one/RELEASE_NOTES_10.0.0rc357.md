# WAFD ONE RC357

## Scope
Delivery Viewer language switching only.

## Change
- Selecting any supported language inside **Delivery Data** now updates the viewer in-place without reloading the Frappe page.
- No call to `set_user_language`.
- No database write for language selection.
- No global `wafd_lang` update.
- No change to roles, permissions, assignments, workflows, Iftar access, driver, delivery supervisor, undertakings, or any other application function.
- Preserves the RC356 Delivery Viewer translations and project-scoped permissions.

## Supported languages
Arabic, English, Indonesian, Urdu, Hindi, Bengali, French, Hausa, Swahili, Uzbek.
