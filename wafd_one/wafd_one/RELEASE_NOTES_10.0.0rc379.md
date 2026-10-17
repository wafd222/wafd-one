# WAFD ONE 10.0.0 RC379

## Scope
Fix only the external contracting-authority Iftar report and its mobile return/navigation behavior.

## Changes
- Resolve report image files by normalized URL path and embed image bytes from the Frappe File storage API when a local path is unavailable. This targets black/missing evidence images in the official report PDF.
- Disable Frappe's global freeze overlay while preparing the report PDF.
- Recover the authority viewer after returning from an iOS PDF/share view, clearing a stale freeze overlay so the Iftar monitoring card remains interactive.
- Replace unsafe `history.back()` fallback in the report toolbar with opener-aware return behavior.

## Validation
- JavaScript syntax check passed.
- Python compilation check passed.
- 30 targeted authority-viewer and Iftar workflow tests passed.
- ZIP integrity check passed.
- Final visual verification of private-file images and iPhone navigation must be confirmed after deploying to Frappe Cloud.

## Explicitly unchanged
No changes to other modules, workflow stages, role permissions, operational records, pricing, or inventory logic.
