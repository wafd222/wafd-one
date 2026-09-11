from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def main():
    location = json.loads(read("wafd_one/wafd_one/doctype/wafd_delivery_location/wafd_delivery_location.json"))
    assert location["name"] == "WAFD Delivery Location"
    assert {"WAFD Delivery Supervisor", "WAFD Driver"} <= {row["role"] for row in location["permissions"]}

    trip = json.loads(read("wafd_one/wafd_one/doctype/wafd_delivery_trip/wafd_delivery_trip.json"))
    fields = {row["fieldname"]: row for row in trip["fields"]}
    for field in ("trip_source", "delivery_location", "destination_name", "destination_name_en", "destination_map_url", "meal_type"):
        assert field in fields
    for optional in ("vehicle", "hotel", "quantity", "meal_plan"):
        assert not fields[optional].get("reqd")

    api = read("wafd_one/delivery_supervisor.py")
    for value in ('"إفطار / Breakfast": "04:00"', '"غداء / Lunch": "10:00"', '"عشاء / Dinner": "17:00"', '"إفطار صائم / Iftar Saim": "12:00"'):
        assert value in api
    for method in ("get_delivery_board", "create_delivery_tasks", "add_delivery_destination", "cancel_planned_trip"):
        assert f"def {method}" in api

    role_home = read("wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js")
    block = role_home[role_home.index('role: "WAFD Delivery Supervisor"'):role_home.index('role: "WAFD Driver"')]
    assert block.count('page: "wafd-delivery-supervisor"') == 4
    assert "المواقع والفنادق" in block and "سجل التسليم" in block

    driver_api = read("wafd_one/driver_portal.py")
    driver_ui = read("wafd_one/wafd_one/page/wafd_driver_trips/wafd_driver_trips.js")
    for token in ("simple_delivery", "destination_name", "destination_map_url", "latitude", "longitude"):
        assert token in driver_api
    assert "navigator.geolocation.getCurrentPosition" in driver_ui
    assert "capture=\"environment\"" in driver_ui
    for language in ("ar", "en", "id", "ur", "hi", "bn", "fr", "ha", "sw", "uz"):
        assert f'{language}:"' in driver_ui
    for meal in ("breakfast", "lunch", "dinner", "iftar_saim"):
        assert f"{meal}:" in driver_ui

    patch = read("wafd_one/wafd_one/patches/v10_0_0_rc271/execute.py")
    for site in ("المسجد النبوي", "مسجد قباء", "مسجد القبلتين", "مسجد الميقات"):
        assert site in patch
    assert "wafd_one.wafd_one.patches.v10_0_0_rc271.execute" in read("wafd_one/patches.txt")
    print("RC271 simple Delivery Supervisor validation passed")


if __name__ == "__main__":
    main()
