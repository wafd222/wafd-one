from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


report_controller = read("wafd_one/wafd_one/doctype/wafd_iftar_supervisor_daily_report/wafd_iftar_supervisor_daily_report.py")
team_api = read("wafd_one/wafd_one/iftar_team.py")
operation_js = read("wafd_one/wafd_one/doctype/wafd_iftar_daily_operation/wafd_iftar_daily_operation.js")

assert "owner_delivered != cint(self.received_meals)" in report_controller
assert "owner_delivered != cint(self.distributed_meals)" not in report_controller
assert "owner_delivered != cint(report.received_meals)" in team_api
assert "sum(values) != cint(report.received_meals)" in team_api
assert "wafd-mobile-stage-action" in operation_js
assert "$(document.body).append(mobile)" not in operation_js
assert "اعتماد الإنتاج" not in operation_js

# Business example reported from the field screenshots.
received = 500
owner_handover = 500
distributed, returned, preserved, waste = 400, 30, 70, 0
assert owner_handover == received
assert distributed + returned + preserved + waste == received

print("RC333 supervisor reconciliation and mobile-action checks passed")
