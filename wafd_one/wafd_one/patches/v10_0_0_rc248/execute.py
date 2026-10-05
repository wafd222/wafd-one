"""RC248: align proof-backed trips with their authoritative Delivered state."""

import frappe


def execute():
    proofs = frappe.get_all(
        "WAFD Delivery Proof",
        fields=["delivery_trip", "delivery_time"],
        filters={"delivery_trip": ["is", "set"]},
        limit_page_length=0,
    )
    for proof in proofs:
        trip = frappe.db.get_value(
            "WAFD Delivery Trip",
            proof.delivery_trip,
            ["status", "actual_arrival"],
            as_dict=True,
        )
        if not trip:
            continue
        values = {"status": "تم التسليم / Delivered"}
        if proof.delivery_time and trip.actual_arrival != proof.delivery_time:
            values["actual_arrival"] = proof.delivery_time
        if trip.status != values["status"] or len(values) > 1:
            frappe.db.set_value(
                "WAFD Delivery Trip",
                proof.delivery_trip,
                values,
                update_modified=True,
            )
    frappe.clear_cache()
