from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


team = read("wafd_one/wafd_one/iftar_team.py")
portal = read("wafd_one/wafd_one/iftar_stage_portal.py")
site = read("wafd_one/wafd_one/page/wafd_iftar_site/wafd_iftar_site.js")
project_manager = read("wafd_one/wafd_one/page/wafd_iftar_team/wafd_iftar_team.js")
supervisor = read("wafd_one/wafd_one/page/wafd_iftar_supervisor/wafd_iftar_supervisor.js")
official = read("wafd_one/wafd_one/print_format/wafd_iftar_official_daily_report/wafd_iftar_official_daily_report.json")

for token in (
    "authority_inspector_signature", "recipient_signature", "delivery_photo",
    "delivered_bread", "delivered_tablecloths", "absence_reason",
    "preservation_receipt_photo", "preservation_receiver_signature",
    "administration_signature", "administration_stamp",
):
    assert token in team or token in portal or token in site or token in supervisor or token in official, token

assert "إعداد المشرفين والمساعدين وأصحاب السفر" in project_manager
assert "ps-assistants" in project_manager and "bread_quantity" in project_manager and "tablecloths_quantity" in project_manager
assert "openSetup" not in site, "Site Manager must not own Project Manager team planning"
assert "Signature" in supervisor and "capture=\"environment\"" in supervisor
assert "active\": 1" in team
assert "اسم المشرف" in official and "عدد المساعدين" in official
assert "assistant_name" not in official, "Presidency report must never print assistant names"
assert "administration_report_approved" in official

print("RC332 complete Iftar field workflow checks passed")
