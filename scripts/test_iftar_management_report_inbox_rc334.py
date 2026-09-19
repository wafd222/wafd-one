from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


team = read("wafd_one/wafd_one/iftar_team.py")
portal = read("wafd_one/wafd_one/iftar_stage_portal.py")
page = read("wafd_one/wafd_one/page/wafd_iftar_team/wafd_iftar_team.js")
patch = read("wafd_one/wafd_one/patches/v10_0_0_rc334/execute.py")

assert "finalize_daily_report(report.daily_operation)" in team
assert '"site_report_finalized": finalized' in team
assert "def _approved_report_inbox(projects):" in portal
assert '"site_report_approved": 1' in portal
assert 'response["report_inbox"] = _approved_report_inbox(projects)' in portal
assert "التقارير اليومية للإدارة" in page
assert "ift-admin-approve-report" in page
assert "WAFD Iftar Official Daily Report" in page
assert "send_authority_report" in page
assert "finalize_daily_report(operation_name)" in patch

print("RC334 management and administration report inbox checks passed")
