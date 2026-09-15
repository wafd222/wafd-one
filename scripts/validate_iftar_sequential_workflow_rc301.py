from pathlib import Path
import ast
import json


ROOT = Path(__file__).resolve().parents[1]


def main():
    backend_path = ROOT / "wafd_one/wafd_one/iftar_team.py"
    backend = backend_path.read_text(encoding="utf-8")
    ast.parse(backend)
    page = (ROOT / "wafd_one/wafd_one/page/wafd_iftar_team/wafd_iftar_team.js").read_text(encoding="utf-8")
    apis = (
        "approve_project_plan", "start_kitchen", "update_kitchen",
        "update_delivery_allocation", "approve_delivery_dispatch", "approve_site_receipt",
        "approve_authority_inspection", "ensure_supervisor_reports", "receive_for_supervisor",
        "mark_assistant_attendance", "confirm_owner_handover", "submit_supervisor_report",
        "approve_supervisor_report", "finalize_daily_report", "send_authority_report",
    )
    for api in apis:
        assert f"def {api}(" in backend
        assert api in page or api in {"update_delivery_allocation"}
    assert "never creates an Iftar-specific trip" in backend
    assert '"administration" if roles & GLOBAL_MANAGEMENT_ROLES' in backend
    assert '"project_manager" if "WAFD Project Manager" in roles' in backend
    schemas = {
        "wafd_iftar_daily_operation": ("kitchen_started_at", "delivery_plan_approved_at", "site_report_approved_at", "authority_report_sent_at"),
        "wafd_iftar_supervisor_daily_report": ("handover_photo", "distribution_photo", "closeout_photo", "submitted_by"),
        "wafd_delivery_trip": ("iftar_bread_quantity", "iftar_loading_photo", "iftar_dispatch_notes"),
    }
    for name, required in schemas.items():
        path = ROOT / "wafd_one/wafd_one/doctype" / name / f"{name}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        fields = [row["fieldname"] for row in data["fields"]]
        assert len(fields) == len(set(fields))
        assert set(fields) == set(data["field_order"])
        assert all(field in fields for field in required)
    print("RC301 sequential Iftar workflow validation passed")


if __name__ == "__main__":
    main()
