# WAFD ONE 10.0.0rc386 — External Iftar Viewer Mobile Layout

Based on RC385 (route-guard re-entry fix retained).

- Fixes mobile Desk shell layout where the viewer occupied only the right half of the iPhone screen.
- Scopes sidebar hiding and 100%-width layout overrides exclusively to the `wafd-iftar-authority-viewer` Page at mobile widths.
- Keeps wide summary table scrolling inside its own container, without widening the entire page.
- Removes only the redundant external `مشاركة التقرير` button below completed stages.
- Retains the clickable `التقرير النهائي` stage and report-preview toolbar including its share/print actions.
- No changes to route guards, roles, server data, or other workflows.

QA: syntax, static regression, local responsive browser fixture, automated tests, and ZIP integrity. Live Safari deployment verification required.
