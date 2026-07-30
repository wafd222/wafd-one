# WAFD ONE 2.4.1

## Phase 1 database synchronization repair

- Force-reloads the Phase 1 DocTypes during post-model-sync migration.
- Loads child tables and independent master records before linked documents.
- Re-loads the mutually linked Project and Contract DocTypes after both exist.
- Rebuilds the WAFD ONE workspace only after the DocTypes are available.
- Refreshes permissions and clears cache so the DocTypes appear in Desk search.
