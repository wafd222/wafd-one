from __future__ import annotations

import frappe
from frappe.utils import add_days, cint, flt, get_datetime, getdate, nowdate

from wafd_one.finance import get_dashboard_data
from wafd_one.planning import upsert_alert
from wafd_one.quality import get_food_safety_dashboard


def _has_doctype(name: str) -> bool:
    return bool(frappe.db.exists("DocType", name))


def _safe_count(doctype: str, filters=None) -> int:
    if not _has_doctype(doctype):
        return 0
    return cint(frappe.db.count(doctype, filters or {}))


def _expiry_count(doctype: str, fieldname: str, days: int = 30) -> int:
    if not _has_doctype(doctype) or not frappe.db.has_column(doctype, fieldname):
        return 0
    return _safe_count(
        doctype,
        {
            fieldname: ["between", [nowdate(), add_days(nowdate(), days)]],
            "status": ["not in", ["غير نشط / Inactive", "غير نشطة / Inactive"]],
        },
    )


def _open_alert_rows(limit: int = 12):
    if not _has_doctype("WAFD Operations Alert"):
        return []
    rows = frappe.get_all(
        "WAFD Operations Alert",
        filters={"status": ["!=", "مغلق / Closed"]},
        fields=[
            "name", "alert_type", "severity", "alert_date", "project",
            "reference_doctype", "reference_name", "message", "recommended_action",
        ],
        order_by="alert_date desc",
        limit=max(cint(limit) * 3, cint(limit)),
    )
    severity_order = {"حرج / Critical": 0, "مرتفع / High": 1, "متوسط / Medium": 2, "منخفض / Low": 3}
    rows.sort(key=lambda row: (severity_order.get(row.severity, 9), -(get_datetime(row.alert_date).timestamp() if row.alert_date else 0)))
    return rows[:cint(limit)]


def _project_rankings(limit: int = 8):
    if not _has_doctype("WAFD Catering Project"):
        return []
    return frappe.get_all(
        "WAFD Catering Project",
        filters={"status": ["!=", "ملغي / Cancelled"]},
        fields=[
            "name", "project_name", "primary_hotel", "progress_percent",
            "profit", "profit_margin_percent", "outstanding_amount",
            "delivered_meals", "total_meals",
        ],
        order_by="profit desc",
        limit=limit,
    )


def _driver_performance(limit: int = 8):
    if not _has_doctype("WAFD Delivery Trip"):
        return []
    return frappe.db.sql(
        """
        select driver,
               count(*) trips,
               sum(case when status='تم التسليم / Delivered' then 1 else 0 end) delivered_trips,
               sum(case when on_time_status='في الوقت / On Time' then 1 else 0 end) on_time_trips,
               sum(case when status='متأخرة / Delayed' or on_time_status='متأخر / Delayed' then 1 else 0 end) delayed_trips,
               coalesce(avg(nullif(delay_minutes, 0)), 0) average_delay_minutes
        from `tabWAFD Delivery Trip`
        where ifnull(driver, '')!=''
        group by driver
        order by on_time_trips desc, delayed_trips asc, trips desc
        limit %s
        """,
        (cint(limit),),
        as_dict=True,
    )


def _hotel_performance(limit: int = 8):
    if not _has_doctype("WAFD Delivery Proof"):
        return []
    return frappe.db.sql(
        """
        select hotel,
               count(*) deliveries,
               coalesce(sum(received_quantity), 0) accepted_quantity,
               coalesce(sum(rejected_quantity), 0) rejected_quantity,
               case when coalesce(sum(received_quantity),0)+coalesce(sum(rejected_quantity),0)>0
                    then coalesce(sum(received_quantity),0) /
                         (coalesce(sum(received_quantity),0)+coalesce(sum(rejected_quantity),0)) * 100
                    else 0 end acceptance_percent
        from `tabWAFD Delivery Proof`
        where ifnull(hotel, '')!=''
        group by hotel
        order by acceptance_percent desc, deliveries desc
        limit %s
        """,
        (cint(limit),),
        as_dict=True,
    )


@frappe.whitelist()
def get_executive_dashboard_data(from_date=None, to_date=None):
    """Return the existing dashboard plus executive risks and performance rankings."""
    data = get_dashboard_data(from_date=from_date, to_date=to_date) or {}
    low_margin = 0
    if _has_doctype("WAFD Catering Project"):
        low_margin = _safe_count(
            "WAFD Catering Project",
            {
                "status": ["!=", "ملغي / Cancelled"],
                "revenue": [">", 0],
                "profit_margin_percent": ["<", 10],
            },
        )
    expiring_contracts = _expiry_count("WAFD Contract", "end_date", 30)
    vehicle_expiry = _expiry_count("WAFD Vehicle", "registration_expiry", 30) + _expiry_count(
        "WAFD Vehicle", "insurance_expiry", 30
    )
    driver_license_expiry = _expiry_count("WAFD Driver", "license_expiry", 30)
    open_alerts = _open_alert_rows()
    critical_alerts = _safe_count(
        "WAFD Operations Alert",
        {"status": ["!=", "مغلق / Closed"], "severity": "حرج / Critical"},
    )

    data.update(
        {
            "active_contracts": _safe_count("WAFD Contract", {"status": ["not in", ["ملغي / Cancelled", "مغلق / Closed"]]}),
            "executive_risks": {
                "open_alerts": _safe_count("WAFD Operations Alert", {"status": ["!=", "مغلق / Closed"]}),
                "critical_alerts": critical_alerts,
                "low_margin_projects": low_margin,
                "expiring_contracts": expiring_contracts,
                "vehicle_documents_expiring": vehicle_expiry,
                "driver_licenses_expiring": driver_license_expiry,
            },
            "open_alert_rows": open_alerts,
            "project_rankings": _project_rankings(),
            "driver_performance": _driver_performance(),
            "hotel_performance": _hotel_performance(),
            "food_safety": get_food_safety_dashboard(service_date=to_date or nowdate()),
            "inventory_snapshot": _inventory_snapshot(),
            "today_operations": _today_operations(),
        }
    )
    return data


@frappe.whitelist()
def refresh_executive_alerts():
    """Create or refresh management alerts for risks not covered by operations checks."""
    if not _has_doctype("WAFD Operations Alert"):
        return {"created_or_updated": 0}
    created = []
    today = getdate(nowdate())
    cutoff = getdate(add_days(today, 30))

    if _has_doctype("WAFD Contract"):
        for row in frappe.get_all(
            "WAFD Contract",
            filters={"end_date": ["between", [today, cutoff]], "status": ["!=", "ملغي / Cancelled"]},
            fields=["name", "project", "end_date"],
        ):
            created.append(
                upsert_alert(
                    "قرب انتهاء عقد / Contract Expiry",
                    "مرتفع / High",
                    f"العقد ينتهي بتاريخ {row.end_date}.",
                    row.project,
                    "WAFD Contract",
                    row.name,
                    "مراجعة التجديد أو الإقفال وخطة التسليم النهائية.",
                    suffix=str(row.end_date),
                )
            )

    if _has_doctype("WAFD Vehicle"):
        for fieldname, label in (("registration_expiry", "الاستمارة"), ("insurance_expiry", "التأمين")):
            for row in frappe.get_all(
                "WAFD Vehicle",
                filters={fieldname: ["between", [today, cutoff]], "status": ["!=", "غير نشطة / Inactive"]},
                fields=["name", fieldname],
            ):
                expiry = row.get(fieldname)
                created.append(
                    upsert_alert(
                        "انتهاء وثائق مركبة / Vehicle Document Expiry",
                        "مرتفع / High",
                        f"{label} للمركبة {row.name} تنتهي بتاريخ {expiry}.",
                        reference_doctype="WAFD Vehicle",
                        reference_name=row.name,
                        recommended_action="تجديد الوثيقة قبل إسناد رحلات جديدة للمركبة.",
                        suffix=f"{fieldname}:{expiry}",
                    )
                )

    if _has_doctype("WAFD Driver"):
        for row in frappe.get_all(
            "WAFD Driver",
            filters={"license_expiry": ["between", [today, cutoff]], "status": ["!=", "غير نشط / Inactive"]},
            fields=["name", "license_expiry"],
        ):
            created.append(
                upsert_alert(
                    "انتهاء رخصة سائق / Driver License Expiry",
                    "مرتفع / High",
                    f"رخصة السائق {row.name} تنتهي بتاريخ {row.license_expiry}.",
                    reference_doctype="WAFD Driver",
                    reference_name=row.name,
                    recommended_action="تجديد الرخصة قبل إسناد رحلة جديدة.",
                    suffix=str(row.license_expiry),
                )
            )

    if _has_doctype("WAFD Catering Project"):
        for row in frappe.get_all(
            "WAFD Catering Project",
            filters={
                "status": ["!=", "ملغي / Cancelled"],
                "revenue": [">", 0],
                "profit_margin_percent": ["<", 10],
            },
            fields=["name", "profit_margin_percent"],
        ):
            created.append(
                upsert_alert(
                    "هامش ربح منخفض / Low Margin",
                    "حرج / Critical" if flt(row.profit_margin_percent) < 0 else "مرتفع / High",
                    f"هامش ربح المشروع {flt(row.profit_margin_percent):.1f}%.",
                    row.name,
                    "WAFD Catering Project",
                    row.name,
                    "مراجعة تكلفة الوجبات والهدر وسعر البيع والمصروفات المباشرة.",
                    suffix="margin-below-10",
                )
            )

    return {"created_or_updated": len(set(created)), "alerts": list(dict.fromkeys(created))}


def _low_stock_condition(alias: str = "sb") -> str:
    """Return the canonical low-stock condition using the ingredient minimum level."""
    return f"coalesce({alias}.available_quantity, 0) <= coalesce(i.minimum_stock, 0)"


def _inventory_snapshot(limit: int = 8):
    if not _has_doctype("WAFD Stock Balance"):
        return {"total_value": 0, "low_items": 0, "warehouses": [], "top_consumed": []}

    total_value = frappe.db.sql("select coalesce(sum(stock_value),0) from `tabWAFD Stock Balance`")[0][0] or 0
    low_condition = _low_stock_condition("sb")
    low_items = frappe.db.sql(
        f"""select count(*)
              from `tabWAFD Stock Balance` sb
              left join `tabWAFD Ingredient` i on i.name = sb.ingredient
             where {low_condition}"""
    )[0][0] or 0
    warehouses = frappe.db.sql(
        f"""select sb.warehouse,
                   coalesce(sum(sb.stock_value),0) stock_value,
                   sum(case when {low_condition} then 1 else 0 end) low_items,
                   count(*) item_count
              from `tabWAFD Stock Balance` sb
              left join `tabWAFD Ingredient` i on i.name = sb.ingredient
             group by sb.warehouse
             order by stock_value desc
             limit %s""",
        (cint(limit),), as_dict=True,
    )
    top_consumed = []
    if _has_doctype("WAFD Stock Movement") and _has_doctype("WAFD Stock Movement Item"):
        # The live DocType status is "مرحلة / Posted". Keep legacy values for old records.
        top_consumed = frappe.db.sql(
            """select smi.ingredient,
                      coalesce(sum(abs(smi.quantity)),0) quantity,
                      max(smi.uom) uom,
                      count(distinct sm.name) movement_count,
                      coalesce(sum(abs(smi.amount)),0) consumption_value
                 from `tabWAFD Stock Movement Item` smi
                 inner join `tabWAFD Stock Movement` sm on sm.name=smi.parent
                where sm.status in ('مرحلة / Posted','مرحّل / Posted','معتمد / Confirmed')
                  and sm.movement_type in ('صرف / Issue','استهلاك / Consumption','هالك / Waste')
                group by smi.ingredient
                order by quantity desc
                limit %s""",
            (cint(limit),), as_dict=True,
        )
    return {
        "total_value": flt(total_value),
        "low_items": cint(low_items),
        "warehouses": warehouses,
        "top_consumed": top_consumed,
    }


@frappe.whitelist()
def get_low_stock_details(warehouse: str | None = None):
    """Return current low/empty stock rows for the dashboard drill-down."""
    if not _has_doctype("WAFD Stock Balance"):
        return []
    filters = [warehouse] if warehouse else []
    warehouse_clause = "and sb.warehouse = %s" if warehouse else ""
    return frappe.db.sql(
        f"""select sb.name,
                   sb.warehouse,
                   sb.ingredient,
                   coalesce(sb.actual_quantity, 0) actual_quantity,
                   coalesce(sb.reserved_quantity, 0) reserved_quantity,
                   coalesce(sb.available_quantity, 0) available_quantity,
                   coalesce(i.minimum_stock, 0) minimum_stock,
                   coalesce(sb.uom, i.uom, '') uom,
                   coalesce(sb.stock_value, 0) stock_value,
                   sb.last_movement_date
              from `tabWAFD Stock Balance` sb
              left join `tabWAFD Ingredient` i on i.name = sb.ingredient
             where {_low_stock_condition('sb')}
                   {warehouse_clause}
             order by sb.available_quantity asc, sb.ingredient asc""",
        tuple(filters), as_dict=True,
    )


def _today_operations():
    today = nowdate()
    return {
        "planned": _safe_count("WAFD Meal Plan", {"service_date": today, "status": ["!=", "ملغي / Cancelled"]}),
        "production": _safe_count("WAFD Production Batch", {"batch_date": today, "status": ["!=", "موقوف / Stopped"]}),
        "trips": _safe_count("WAFD Delivery Trip", {"trip_date": today, "status": ["!=", "ملغية / Cancelled"]}),
        "delivered": _safe_count("WAFD Delivery Trip", {"trip_date": today, "status": "تم التسليم / Delivered"}),
    }
