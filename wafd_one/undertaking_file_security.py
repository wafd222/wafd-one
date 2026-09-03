"""Narrow File access bridge for WAFD undertaking officers.

Frappe's Attach/Attach Image controls resolve private File documents separately
from the parent document.  An undertaking officer can legitimately read their
own undertaking but, without a File-level bridge, the browser receives repeated
"You do not have permission to access this file" dialogs for the generated PDF
and the management-controlled signature/stamp used by the print template.

This module deliberately does *not* grant general File access.  It only returns
True for files that are either attached to an undertaking the current officer
owns, or are the exact configured company signature/stamp assets used by the
undertaking print settings/template.  All other File permission decisions are
left to Frappe's normal permission engine.
"""

from __future__ import annotations

import frappe

OFFICER_ROLE = "WAFD Undertaking Officer"
PRIVILEGED_ROLES = {"System Manager", "WAFD Operations Manager"}
DELIVERY_MANAGEMENT_ROLES = PRIVILEGED_ROLES | {"WAFD Delivery Supervisor", "WAFD Project Manager"}
UNDERTAKING_DOCTYPE = "WAFD Hotel Undertaking"
QUOTATION_DOCTYPE = "WAFD Quotation"
QUOTATION_FILE_CREATORS = {
    "System Manager",
    "WAFD Operations Manager",
    "WAFD Project Manager",
    "WAFD Quotation Officer",
}


def _roles(user: str) -> set[str]:
    return set(frappe.get_roles(user))


def _is_restricted_officer(user: str) -> bool:
    roles = _roles(user)
    return OFFICER_ROLE in roles and not (roles & PRIVILEGED_ROLES)


def _owns_undertaking(user: str, name: str | None) -> bool:
    if not name:
        return False
    return bool(
        frappe.db.exists(
            UNDERTAKING_DOCTYPE,
            {"name": name, "owner": user},
        )
    )


def _configured_asset_urls() -> set[str]:
    """Return only the exact company approval assets configured for printing."""
    urls: set[str] = set()

    if frappe.db.exists("DocType", "WAFD Print Settings"):
        for fieldname in ("default_signature", "default_stamp"):
            try:
                value = frappe.db.get_single_value("WAFD Print Settings", fieldname)
            except Exception:
                value = None
            if value:
                urls.add(str(value).strip())

    if frappe.db.exists("DocType", "WAFD Document Template"):
        # Restrict the lookup to undertaking templates only.  Do not expose
        # arbitrary assets from other Document Studio templates.
        rows = frappe.get_all(
            "WAFD Document Template",
            filters={"reference_doctype": UNDERTAKING_DOCTYPE, "enabled": 1},
            fields=["signature", "stamp"],
            limit=20,
        )
        for row in rows:
            for fieldname in ("signature", "stamp"):
                value = row.get(fieldname)
                if value:
                    urls.add(str(value).strip())

    return {url for url in urls if url}


def _is_management_approval_attachment(doc) -> bool:
    attached_doctype = getattr(doc, "attached_to_doctype", None)
    attached_field = (getattr(doc, "attached_to_field", None) or "").strip().lower()
    if attached_doctype == "WAFD Print Settings":
        return attached_field in {"default_signature", "default_stamp"}
    if attached_doctype == "WAFD Document Template":
        if attached_field not in {"signature", "stamp"}:
            return False
        template_name = getattr(doc, "attached_to_name", None)
        if not template_name:
            return False
        return bool(
            frappe.db.exists(
                "WAFD Document Template",
                {
                    "name": template_name,
                    "reference_doctype": UNDERTAKING_DOCTYPE,
                    "enabled": 1,
                },
            )
        )
    return False


def _delivery_attachment_is_readable(doc, user: str) -> bool:
    """Allow only the manager or assigned driver to read delivery evidence."""
    attached_doctype = getattr(doc, "attached_to_doctype", None)
    attached_name = getattr(doc, "attached_to_name", None)
    if attached_doctype not in {"WAFD Loading Record", "WAFD Delivery Trip", "WAFD Delivery Proof"}:
        return False
    if not attached_name:
        return False
    if _roles(user) & DELIVERY_MANAGEMENT_ROLES:
        return True

    from wafd_one.driver_security import trip_is_assigned_to_user

    if attached_doctype == "WAFD Delivery Trip":
        trip_name = attached_name
    elif attached_doctype == "WAFD Loading Record":
        trip_name = frappe.db.get_value(
            "WAFD Delivery Trip", {"loading_record": attached_name}, "name"
        )
    else:
        trip_name = frappe.db.get_value("WAFD Delivery Proof", attached_name, "delivery_trip")
    if not trip_name:
        return False
    trip = frappe.db.get_value(
        "WAFD Delivery Trip", trip_name, ["driver", "assigned_driver_user"], as_dict=True
    )
    return bool(
        trip and trip_is_assigned_to_user(trip.driver, trip.assigned_driver_user, user)
    )


def file_has_permission(doc, user=None, permission_type=None, ptype=None, **kwargs):
    """Allow a restricted officer to read only undertaking-required files."""
    user = user or frappe.session.user
    permission_type = permission_type or ptype or "read"

    # Frappe checks File.create before the new File row is inserted. Returning
    # True here makes the standard Attach/Attach Image control reliable even
    # when an existing site's Custom DocPerm cache has not yet been rebuilt.
    # Reading remains narrowly scoped below.
    if permission_type == "create" and (_roles(user) & QUOTATION_FILE_CREATORS):
        return True

    # Never widen write/delete/share permissions on File.
    if permission_type not in {"read", "select"}:
        return None
    if _delivery_attachment_is_readable(doc, user):
        return True

    # Quotation creators receive File *create* permission separately. Reading
    # remains scoped to a file attached to a quotation they may read, avoiding
    # broad access to unrelated private files.
    attached_doctype = getattr(doc, "attached_to_doctype", None)
    attached_name = getattr(doc, "attached_to_name", None)
    attached_field = (getattr(doc, "attached_to_field", None) or "").strip()
    if (
        attached_doctype == QUOTATION_DOCTYPE
        and attached_name
        and attached_field in {"menu_attachment", "generated_pdf"}
        and frappe.has_permission(
            QUOTATION_DOCTYPE, ptype="read", doc=attached_name, user=user
        )
    ):
        return True
    if not _is_restricted_officer(user):
        return None

    file_url = (getattr(doc, "file_url", None) or "").strip()

    # Generated PDF (and any legacy undertaking attachment) is readable only
    # when it belongs to an undertaking owned by the signed-in officer.
    if attached_doctype == UNDERTAKING_DOCTYPE and _owns_undertaking(user, attached_name):
        return True

    # Compatibility for older generated PDFs that lost attachment metadata but
    # are still referenced by the officer's own undertaking.generated_pdf.
    if file_url and frappe.db.exists(
        UNDERTAKING_DOCTYPE,
        {"owner": user, "generated_pdf": file_url},
    ):
        return True

    # The signature/stamp are centrally managed and read-only for officers.
    # Permit only the exact configured assets, never the rest of the File table.
    if _is_management_approval_attachment(doc):
        return True
    if file_url and file_url in _configured_asset_urls():
        return True

    return None
