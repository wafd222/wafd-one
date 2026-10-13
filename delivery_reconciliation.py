"""Repair the approved-loading to delivery-trip hand-off.

An approved loading record is the durable operational fact.  Older releases
could save that record and then fail while inserting the delivery trip (for
example while validating legacy timestamps).  The driver portal must not turn
that split state into a silent empty page.

All reconciliation is idempotent and scoped either to one enabled driver login
or to manager/migration use.  Document ``insert`` remains responsible for the
normal business validations.
"""

from __future__ import annotations

import frappe
from frappe.utils import cint, getdate, nowdate

from wafd_one.driver_security import get_drivers_for_user, resolve_linked_driver


APPROVED_LOADING_STATUSES = ("تم التحميل / Loaded", "خرجت / Dispatched")
CANCELLED_TRIP = "ملغية / Cancelled"


def _loading_rows(driver_names=None):
    filters = {"status": ["in", APPROVED_LOADING_STATUSES]}
    if driver_names is not None:
        if not driver_names:
            return []
        filters["driver"] = ["in", list(driver_names)]
    return frappe.get_all(
        "WAFD Loading Record",
        filters=filters,
        fields=[
            "name", "project", "meal_plan", "loading_date", "quantity",
            "vehicle", "driver", "supervisor", "loading_photo", "hotel",
        ],
        order_by="loading_date asc, creation asc",
    )


def _existing_trip(loading_name):
    return frappe.db.get_value(
        "WAFD Delivery Trip",
        {"loading_record": loading_name, "status": ["!=", CANCELLED_TRIP]},
        ["name", "driver", "assigned_driver_user"],
        as_dict=True,
    )


def _repair_existing_trip(trip, canonical_driver, driver_user):
    values = {}
    if trip.driver != canonical_driver:
        values["driver"] = canonical_driver
    if trip.assigned_driver_user != driver_user:
        values["assigned_driver_user"] = driver_user
    if values:
        # This is an identity repair only.  db.set_value intentionally avoids
        # re-running unrelated legacy time/food-safety validations on a trip
        # that already exists.
        frappe.db.set_value(
            "WAFD Delivery Trip", trip.name, values, update_modified=False
        )
    return bool(values)


def _required_loading_problem(loading):
    if not loading.vehicle or not loading.driver:
        return "missing_vehicle_or_driver"
    if not loading.loading_photo:
        return "missing_loading_photo"
    if not loading.supervisor:
        return "missing_loading_supervisor"
    if cint(loading.quantity) <= 0:
        return "invalid_loading_quantity"
    if not loading.project or not loading.meal_plan or not loading.hotel:
        return "incomplete_loading_links"
    return None


def reconcile_loading_row(loading, expected_user=None):
    """Return an idempotent reconciliation result for one loading row."""
    problem = _required_loading_problem(loading)
    if problem:
        return {"loading": loading.name, "state": "blocked", "reason": problem}

    canonical_driver, driver_user = resolve_linked_driver(loading.driver)
    if not canonical_driver or not driver_user:
        return {
            "loading": loading.name,
            "state": "blocked",
            "reason": "driver_account_not_linked",
        }
    if expected_user and driver_user != expected_user:
        # Never create or expose another driver's trip during a driver request.
        return {"loading": loading.name, "state": "not_owned"}

    if loading.driver != canonical_driver:
        frappe.db.set_value(
            "WAFD Loading Record",
            loading.name,
            "driver",
            canonical_driver,
            update_modified=False,
        )
        loading.driver = canonical_driver

    existing = _existing_trip(loading.name)
    if existing:
        repaired = _repair_existing_trip(existing, canonical_driver, driver_user)
        return {
            "loading": loading.name,
            "trip": existing.name,
            "state": "repaired" if repaired else "existing",
        }

    service_date = frappe.db.get_value("WAFD Meal Plan", loading.meal_plan, "service_date")
    trip = frappe.get_doc(
        {
            "doctype": "WAFD Delivery Trip",
            "project": loading.project,
            "meal_plan": loading.meal_plan,
            "loading_record": loading.name,
            "trip_date": service_date or (
                getdate(loading.loading_date) if loading.loading_date else nowdate()
            ),
            "vehicle": loading.vehicle,
            "driver": canonical_driver,
            "assigned_driver_user": driver_user,
            "hotel": loading.hotel,
            "quantity": cint(loading.quantity),
            "status": "تم التحميل / Loaded",
        }
    )
    trip.insert(ignore_permissions=True)
    return {"loading": loading.name, "trip": trip.name, "state": "created"}


def reconcile_missing_delivery_trips(user=None, all_drivers=False):
    """Reconcile approved loadings and return a non-sensitive summary.

    ``all_drivers`` is reserved for migrations and manager workflows.  A driver
    request is restricted to that login's canonical and legacy driver rows.
    A blocked row is reported without aborting the whole batch so one old
    record cannot hide all other employees' valid trips.
    """
    if all_drivers:
        expected_user = None
        rows = _loading_rows()
    else:
        expected_user = user or frappe.session.user
        rows = _loading_rows(get_drivers_for_user(expected_user))

    results = []
    for loading in rows:
        try:
            result = reconcile_loading_row(loading, expected_user=expected_user)
        except Exception as exc:
            safe_classes = {
                "ValidationError", "PermissionError", "MandatoryError",
                "LinkValidationError", "DuplicateEntryError",
            }
            result = {
                "loading": loading.name,
                "state": "blocked",
                "reason": "trip_validation_failed",
                # Frappe validation messages are safe operational feedback for
                # the assigned driver/manager and are needed to end silent
                # failure loops.  Never include a traceback or SQL details.
                "message": str(exc) if exc.__class__.__name__ in safe_classes else "",
            }
        if result.get("state") != "not_owned":
            results.append(result)

    counts = {
        state: sum(row.get("state") == state for row in results)
        for state in ("created", "repaired", "existing", "blocked")
    }
    return {"counts": counts, "results": results}
