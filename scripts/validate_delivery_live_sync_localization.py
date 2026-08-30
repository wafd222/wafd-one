"""Regression checks for RC248 delivery synchronization and driver localization."""

from __future__ import annotations

import ast
import importlib.util
import re
import sys
import types
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = {"ar", "en", "id", "ur", "hi", "bn", "fr", "ha", "sw", "uz"}


class Row(dict):
    __getattr__ = dict.get


def validate_existing_proof_is_idempotent() -> None:
    source_path = ROOT / "wafd_one/operations.py"
    module_tree = ast.parse(source_path.read_text(encoding="utf-8"))
    function = next(
        node for node in module_tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "create_delivery_proof"
    )

    class Trip:
        name = "TRIP-1"
        status = "تم التسليم / Delivered"

        @staticmethod
        def check_permission(permission):
            assert permission == "write"

    class DB:
        @staticmethod
        def get_value(doctype, filters, field):
            assert doctype == "WAFD Delivery Proof"
            assert filters == {"delivery_trip": "TRIP-1"}
            assert field == "name"
            return "PROOF-1"

    fake = types.SimpleNamespace(
        db=DB(),
        get_doc=lambda doctype, name: Trip(),
        throw=lambda message: (_ for _ in ()).throw(AssertionError(message)),
        whitelist=lambda: (lambda value: value),
    )
    namespace = {"frappe": fake, "now_datetime": lambda: "2026-08-30 12:00:00"}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(source_path), "exec"), namespace)
    result = namespace["create_delivery_proof"]("TRIP-1")
    assert result == {"name": "PROOF-1", "created": False}


def validate_proof_updates_and_notifies_trip() -> None:
    updates = []
    notifications = []

    class DB:
        @staticmethod
        def set_value(doctype, name, values, value=None, update_modified=False):
            updates.append((doctype, name, values, value, update_modified))

        @staticmethod
        def get_value(doctype, name, fields, as_dict=False):
            return None

    class TripDocument:
        @staticmethod
        def notify_update():
            notifications.append("TRIP-1")

    fake_frappe = types.ModuleType("frappe")
    fake_frappe.db = DB()
    fake_frappe.get_doc = lambda doctype, name: TripDocument()
    fake_document = types.ModuleType("frappe.model.document")
    fake_document.Document = object
    fake_utils = types.ModuleType("frappe.utils")
    fake_utils.cint = lambda value: int(value or 0)
    fake_utils.flt = lambda value: float(value or 0)
    fake_utils.get_datetime = lambda value: value
    fake_utils.now_datetime = lambda: "2026-08-30 12:00:00"

    saved = {name: sys.modules.get(name) for name in ("frappe", "frappe.model.document", "frappe.utils")}
    try:
        sys.modules["frappe"] = fake_frappe
        sys.modules["frappe.model.document"] = fake_document
        sys.modules["frappe.utils"] = fake_utils
        path = ROOT / "wafd_one/wafd_one/doctype/wafd_delivery_proof/wafd_delivery_proof.py"
        spec = importlib.util.spec_from_file_location("rc248_proof", path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        proof = module.WAFDDeliveryProof()
        proof.delivery_trip = "TRIP-1"
        proof.delivery_time = "2026-08-30 11:59:00"
        proof.meal_plan = None
        proof.on_update()
    finally:
        for name, previous in saved.items():
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous

    assert updates[0] == (
        "WAFD Delivery Trip",
        "TRIP-1",
        {"status": "تم التسليم / Delivered", "actual_arrival": "2026-08-30 11:59:00"},
        None,
        True,
    )
    assert notifications == ["TRIP-1"]


def validate_migration_repairs_legacy_trip() -> None:
    trip = Row(status="وصلت / Arrived", actual_arrival=None)
    writes = []
    fake = types.ModuleType("frappe")
    fake.get_all = lambda *args, **kwargs: [Row(delivery_trip="TRIP-OLD", delivery_time="2026-08-30 10:00:00")]

    class DB:
        @staticmethod
        def get_value(*args, **kwargs):
            return trip

        @staticmethod
        def set_value(doctype, name, values, update_modified=False):
            writes.append((doctype, name, values, update_modified))

    fake.db = DB()
    fake.clear_cache = lambda: None
    previous = sys.modules.get("frappe")
    try:
        sys.modules["frappe"] = fake
        path = ROOT / "wafd_one/wafd_one/patches/v10_0_0_rc248/execute.py"
        spec = importlib.util.spec_from_file_location("rc248_patch", path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        module.execute()
    finally:
        if previous is None:
            sys.modules.pop("frappe", None)
        else:
            sys.modules["frappe"] = previous

    assert writes == [(
        "WAFD Delivery Trip",
        "TRIP-OLD",
        {"status": "تم التسليم / Delivered", "actual_arrival": "2026-08-30 10:00:00"},
        True,
    )]


def validate_all_driver_languages() -> None:
    path = ROOT / "wafd_one/wafd_one/page/wafd_driver_trips/wafd_driver_trips.js"
    text = path.read_text(encoding="utf-8")
    required_keys = {
        "my_trips", "field_delivery", "back", "refresh", "no_trips",
        "no_trips_manager", "no_approved_loading", "trip_creation_blocked",
        "assignment_incomplete", "hotel", "vehicle", "driver", "quantity",
        "arrival", "loading_photo", "uploaded_by", "seal", "start",
        "mark_arrived", "proof", "delivered", "receiver", "mobile",
        "received", "rejected", "acceptance", "full", "partial", "refused",
        "quick_note", "choose", "notes", "photo", "signature", "clear",
        "submit", "close", "saving", "open_map", "required",
    }
    dictionary_lines = {
        match.group(1): match.group(2)
        for match in re.finditer(r'^\s{4}([a-z_]+):\{([^\n]+)\},$', text, re.MULTILINE)
    }
    for key in required_keys:
        assert key in dictionary_lines, f"Missing driver translation key: {key}"
        found = set(re.findall(r'(ar|en|id|ur|hi|bn|fr|ha|sw|uz):', dictionary_lines[key]))
        assert found == LANGUAGES, f"Incomplete languages for {key}: {sorted(LANGUAGES - found)}"

    assert 'let lang = activeLanguage();' in text
    assert 'const lang = localStorage.getItem("wafd_lang")' not in text
    assert 'wrapper.wafdApplyTripLanguage' in text
    show_block = text[text.index('frappe.pages["wafd-driver-trips"].on_page_show'):]
    assert show_block.index("wafdApplyTripLanguage") < show_block.index("wafdRefreshTrips")
    assert 'const displayStatus = proof ? "تم التسليم / Delivered" : trip.status;' in text
    assert 'frappe.realtime.doc_subscribe("WAFD Delivery Trip", trip.name);' in text
    assert 'frappe.realtime.on("doc_update"' in text


if __name__ == "__main__":
    validate_existing_proof_is_idempotent()
    validate_proof_updates_and_notifies_trip()
    validate_migration_repairs_legacy_trip()
    validate_all_driver_languages()
    print("RC248 live delivery synchronization and 10-language validation passed")
