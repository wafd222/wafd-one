# WAFD ONE 10.0.0 RC324

## Iftar Site/Supervisor page load fix

- Fixed a JavaScript scope error that prevented the dedicated Iftar Site Manager page from rendering after navigation.
- Fixed the same scope error on the dedicated Iftar Supervisor page.
- Added visible retry/error states instead of leaving a blank page if a portal API call fails.
- No workflow or permission changes outside the two dedicated Iftar pages.
- Preserves RC320 dedicated Iftar driver screen and RC317 offline-first driver capture.
