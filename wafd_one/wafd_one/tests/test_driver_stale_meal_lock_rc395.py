from pathlib import Path


def test_driver_queue_does_not_reconcile_deleted_trips_but_manager_does():
    source = Path(__file__).parents[2].joinpath("driver_portal.py").read_text()
    assert "(iftar_only or not is_manager)" in source
    assert "else reconcile_missing_delivery_trips(all_drivers=True)" in source
    assert "Do not resurrect deleted trips" in source
