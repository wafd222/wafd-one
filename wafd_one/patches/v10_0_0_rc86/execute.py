"""Repair the Hotel Undertaking Document Studio template binding.

The approved undertaking design was accidentally saved against ``API Request Log``.
This patch reuses that exact template document, binds it to the correct DocType,
marks it as the sole default, and removes only duplicate Hotel Undertaking
Document Studio templates.
"""

from __future__ import annotations

import json
import re

import frappe


TARGET_DOCTYPE = "WAFD Hotel Undertaking"
WRONG_DOCTYPE = "API Request Log"
CANONICAL_TITLE = "تعهد فندق"

# Titles observed during the undertaking design iterations.  Deletion is further
# restricted by reference DocType/content checks so unrelated templates are safe.
UNDERTAKING_TITLE_MARKERS = (
    "تعهد فندق",
    "تعهد الفندق",
    "تعهد الفندق المستقل",
    "تعهد فندق 2",
    "تعهد فندق 3",
    "hotel undertaking",
)


def _normalise(value: str | None) -> str:
    value = (value or "").strip().lower()
    return re.sub(r"\s+", " ", value)


def _looks_like_hotel_undertaking(row) -> bool:
    title = _normalise(row.template_title)
    title_match = any(marker in title for marker in UNDERTAKING_TITLE_MARKERS)
    if not title_match:
        return False

    if row.reference_doctype == TARGET_DOCTYPE:
        return True

    # The one broken template is attached to API Request Log but contains Hotel
    # Undertaking Jinja fields.  Check the designer payload before touching it.
    if row.reference_doctype != WRONG_DOCTYPE:
        return False

    payload = " ".join(
        str(value or "")
        for value in (row.canvas_json, row.compiled_html, row.custom_css)
    ).lower()
    return any(
        token in payload
        for token in (
            "doc.hotel",
            "doc.beneficiary_count",
            "doc.undertaking_date",
            "doc.nationality",
            "catering services undertaking",
        )
    )


def _candidate_score(row) -> tuple[int, int, str]:
    """Rank the exact broken design first, then the best existing target template."""
    title = _normalise(row.template_title)
    exact_title = int(title == _normalise(CANONICAL_TITLE))
    wrong_binding = int(row.reference_doctype == WRONG_DOCTYPE)
    return (wrong_binding, exact_title, str(row.modified or ""))


def execute():
    if not frappe.db.exists("DocType", "WAFD Document Template"):
        return
    if not frappe.db.exists("DocType", TARGET_DOCTYPE):
        frappe.throw(f"Required DocType is missing: {TARGET_DOCTYPE}")

    rows = frappe.get_all(
        "WAFD Document Template",
        fields=[
            "name",
            "template_title",
            "reference_doctype",
            "document_category",
            "enabled",
            "is_default",
            "canvas_json",
            "compiled_html",
            "custom_css",
            "modified",
        ],
        order_by="modified desc",
    )
    candidates = [row for row in rows if _looks_like_hotel_undertaking(row)]

    if not candidates:
        frappe.throw(
            "RC86 could not find the approved Hotel Undertaking template. "
            "No templates were changed or deleted."
        )

    keeper = sorted(candidates, key=_candidate_score, reverse=True)[0]
    keeper_doc = frappe.get_doc("WAFD Document Template", keeper.name)

    # Preserve a compact audit snapshot in the migration log before cleanup.
    snapshot = {
        "keeper": keeper.name,
        "original_title": keeper_doc.template_title,
        "original_reference_doctype": keeper_doc.reference_doctype,
        "duplicates": [row.name for row in candidates if row.name != keeper.name],
    }
    frappe.logger("wafd_one").info("RC86 undertaking template repair: %s", json.dumps(snapshot, ensure_ascii=False))

    # Keep the exact approved canvas/assets; change only metadata and default state.
    keeper_doc.template_title = CANONICAL_TITLE
    keeper_doc.reference_doctype = TARGET_DOCTYPE
    keeper_doc.document_category = "Hotel Undertaking"
    keeper_doc.enabled = 1
    keeper_doc.is_default = 1
    keeper_doc.save(ignore_permissions=True)

    # Delete only duplicate undertaking templates. No invoice/operation/other
    # Document Studio templates are touched.
    for row in candidates:
        if row.name == keeper_doc.name:
            continue
        frappe.delete_doc(
            "WAFD Document Template",
            row.name,
            ignore_permissions=True,
            force=True,
        )

    # Defensive cleanup: ensure there is exactly one enabled/default undertaking
    # template even if another migration inserted a duplicate concurrently.
    remaining = frappe.get_all(
        "WAFD Document Template",
        filters={"reference_doctype": TARGET_DOCTYPE},
        pluck="name",
    )
    for name in remaining:
        if name == keeper_doc.name:
            continue
        frappe.delete_doc(
            "WAFD Document Template",
            name,
            ignore_permissions=True,
            force=True,
        )

    frappe.db.set_value(
        "WAFD Document Template",
        keeper_doc.name,
        {"enabled": 1, "is_default": 1, "reference_doctype": TARGET_DOCTYPE},
        update_modified=False,
    )
    frappe.clear_cache(doctype="WAFD Document Template")
    frappe.clear_cache(doctype=TARGET_DOCTYPE)
