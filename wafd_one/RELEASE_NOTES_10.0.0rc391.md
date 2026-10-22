# WAFD ONE 10.0.0 RC391 — Unlimited Iftar Project Viewers

Base: RC390 official signatures. Scope: Iftar external viewer assignment only.

- Employee Management now supports selecting multiple external viewers per Iftar project, without a per-project limit.
- A dedicated WAFD Iftar Viewer Assignment DocType stores additional viewers; the original single viewer field remains for backwards compatibility and existing assignments are preserved.
- Project access, external viewer home-card visibility, monitoring data and final report access all check explicit membership in the project, not the viewer role alone.
- Saving a team with the original API and no multi-viewer parameter preserves the original behavior. Removed viewers lose project access; other roles, reports, signatures and workflows remain unchanged.
- Run the normal Frappe Cloud deployment/migration so the new DocType is installed before using the multi-viewer selector.

Verification: syntax checks, automated tests, archive integrity. Live Frappe Cloud and iPhone testing remain required.
