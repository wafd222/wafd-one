from __future__ import annotations

import frappe
from frappe.utils import add_to_date, cint, get_datetime, now_datetime, nowdate

from wafd_one.planning import upsert_alert


OPEN_STATUSES = ["مفتوح / Open", "قيد المعالجة / In Progress"]


def _exists(doctype: str) -> bool:
    return bool(frappe.db.exists("DocType", doctype))


def _count(doctype: str, filters=None) -> int:
    if not _exists(doctype):
        return 0
    return cint(frappe.db.count(doctype, filters or {}))


@frappe.whitelist()
def get_food_safety_dashboard(project: str | None = None, service_date=None):
    """Return focused food-safety, quality and traceability KPIs."""
    service_date = service_date or nowdate()
    batch_filters = {"batch_date": service_date}
    if project:
        batch_filters["project"] = project

    batches = frappe.get_all(
        "WAFD Production Batch",
        filters=batch_filters,
        fields=[
            "name", "project", "traceability_code", "quality_status",
            "food_safety_release_status", "service_deadline", "status",
        ],
    ) if _exists("WAFD Production Batch") else []
    batch_names = [row.name for row in batches]
    ccp_filters = {"production_batch": ["in", batch_names]} if batch_names else {"name": ["=", ""]}
    inspections_filters = {"production_batch": ["in", batch_names]} if batch_names else {"name": ["=", ""]}

    ccp_checks = frappe.get_all(
        "WAFD CCP Check", filters=ccp_filters,
        fields=["name", "production_batch", "compliance_status", "verification_status"],
    ) if _exists("WAFD CCP Check") else []
    inspections = frappe.get_all(
        "WAFD Quality Inspection", filters=inspections_filters,
        fields=["name", "production_batch", "result"],
    ) if _exists("WAFD Quality Inspection") else []

    return {
        "service_date": service_date,
        "production_batches": len(batches),
        "released_batches": sum(1 for row in batches if row.food_safety_release_status == "مفرج / Released"),
        "held_batches": sum(1 for row in batches if row.food_safety_release_status == "موقوف / On Hold"),
        "rejected_batches": sum(1 for row in batches if row.food_safety_release_status == "مرفوض / Rejected"),
        "pending_release_batches": sum(1 for row in batches if row.food_safety_release_status == "بانتظار المراجعة / Pending Review"),
        "passed_inspections": sum(1 for row in inspections if row.result == "ناجح / Passed"),
        "conditional_inspections": sum(1 for row in inspections if row.result == "مشروط / Conditional"),
        "rejected_inspections": sum(1 for row in inspections if row.result == "مرفوض / Rejected"),
        "ccp_checks": len(ccp_checks),
        "noncompliant_ccp_checks": sum(1 for row in ccp_checks if row.compliance_status == "غير مطابق / Noncompliant"),
        "unverified_ccp_checks": sum(1 for row in ccp_checks if row.verification_status != "تم التحقق / Verified"),
        "traceability_coverage_percent": (
            sum(1 for row in batches if row.traceability_code) / len(batches) * 100 if batches else 0
        ),
    }


@frappe.whitelist()
def get_batch_traceability(traceability_code: str):
    """Return the full internal chain for one production traceability code."""
    if not traceability_code:
        frappe.throw("أدخل رمز التتبع / Enter a traceability code")
    batch_name = frappe.db.get_value("WAFD Production Batch", {"traceability_code": traceability_code}, "name")
    if not batch_name:
        frappe.throw("رمز التتبع غير موجود / Traceability code was not found")
    batch = frappe.get_doc("WAFD Production Batch", batch_name)
    batch.check_permission("read")

    def rows(doctype, filters, fields):
        return frappe.get_all(doctype, filters=filters, fields=fields, order_by="creation asc") if _exists(doctype) else []

    return {
        "batch": batch.as_dict(no_nulls=True),
        "quality_inspections": rows(
            "WAFD Quality Inspection", {"production_batch": batch.name},
            ["name", "inspection_date", "inspector", "result", "corrective_action"],
        ),
        "ccp_checks": rows(
            "WAFD CCP Check", {"production_batch": batch.name},
            ["name", "ccp_type", "check_time", "measured_value", "unit", "compliance_status", "verification_status"],
        ),
        "packaging_records": rows(
            "WAFD Packaging Record", {"production_batch": batch.name},
            ["name", "packaging_date", "packed_quantity", "rejected_quantity", "status"],
        ),
        "loading_records": rows(
            "WAFD Loading Record", {"production_batch": batch.name},
            ["name", "loading_date", "quantity", "vehicle", "driver", "status"],
        ),
        "delivery_proofs": rows(
            "WAFD Delivery Proof", {"project": batch.project, "meal_plan": batch.meal_plan},
            ["name", "delivery_trip", "delivery_time", "hotel", "received_quantity", "rejected_quantity", "status"],
        ),
    }


def refresh_food_safety_alerts():
    """Create or refresh actionable alerts for unresolved food-safety risks."""
    if not _exists("WAFD Operations Alert"):
        return {"created_or_updated": 0, "alerts": []}
    alerts = []

    if _exists("WAFD CCP Check"):
        checks = frappe.get_all(
            "WAFD CCP Check",
            filters={
                "compliance_status": "غير مطابق / Noncompliant",
                "verification_status": ["!=", "تم التحقق / Verified"],
            },
            fields=["name", "production_batch", "ccp_type"],
        )
        for row in checks:
            project = frappe.db.get_value("WAFD Production Batch", row.production_batch, "project")
            alerts.append(upsert_alert(
                "انحراف سلامة غذاء / Food Safety Deviation", "حرج / Critical",
                f"فحص نقطة التحكم {row.ccp_type} غير مطابق ولم يتم التحقق من الإجراء التصحيحي.",
                project, "WAFD CCP Check", row.name,
                "إيقاف الإفراج عن الدفعة، تنفيذ الإجراء التصحيحي، ثم توثيق التحقق.",
            ))

    if _exists("WAFD Quality Inspection"):
        for row in frappe.get_all(
            "WAFD Quality Inspection",
            filters={"result": ["in", ["مرفوض / Rejected", "مشروط / Conditional"]]},
            fields=["name", "production_batch", "result"],
        ):
            project = frappe.db.get_value("WAFD Production Batch", row.production_batch, "project")
            severity = "حرج / Critical" if row.result == "مرفوض / Rejected" else "مرتفع / High"
            alerts.append(upsert_alert(
                "فشل جودة / Quality Failure", severity,
                f"نتيجة فحص الجودة للدفعة {row.production_batch}: {row.result}.",
                project, "WAFD Quality Inspection", row.name,
                "مراجعة الإجراء التصحيحي وإعادة الفحص قبل الإفراج الغذائي.",
            ))

    if _exists("WAFD Production Batch"):
        threshold = add_to_date(now_datetime(), hours=4)
        pending = frappe.get_all(
            "WAFD Production Batch",
            filters={
                "food_safety_release_status": ["in", ["بانتظار المراجعة / Pending Review", "موقوف / On Hold"]],
                "service_deadline": ["between", [now_datetime(), threshold]],
                "status": ["not in", ["مكتمل / Completed", "موقوف / Stopped"]],
            },
            fields=["name", "project", "service_deadline", "food_safety_release_status"],
        )
        for row in pending:
            alerts.append(upsert_alert(
                "إفراج غذائي معلق / Pending Food Safety Release", "مرتفع / High",
                f"دفعة الإنتاج {row.name} لم تحصل على الإفراج الغذائي وموعد خدمتها خلال أربع ساعات.",
                row.project, "WAFD Production Batch", row.name,
                "استكمال فحوص الجودة ونقاط التحكم ثم إصدار قرار الإفراج فوراً.",
                suffix=str(row.service_deadline),
            ))

    return {"created_or_updated": len(set(alerts)), "alerts": list(dict.fromkeys(alerts))}
