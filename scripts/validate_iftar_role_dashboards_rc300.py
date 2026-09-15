from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    backend = (ROOT / "wafd_one/wafd_one/iftar_team.py").read_text(encoding="utf-8")
    page = (ROOT / "wafd_one/wafd_one/page/wafd_iftar_team/wafd_iftar_team.js").read_text(encoding="utf-8")
    wizard = (ROOT / "wafd_one/wafd_one/page/wafd_iftar_wizard/wafd_iftar_wizard.js").read_text(encoding="utf-8")
    project = (ROOT / "wafd_one/wafd_one/doctype/wafd_iftar_project/wafd_iftar_project.json").read_text(encoding="utf-8")

    assert 'if mode in {"administration", "project_manager", "site", "supervisor"}:' in backend
    assert "Kitchen and delivery staff do not need supervisor reports" in backend
    assert "def assign_project_team(" in backend
    assert "def backfill_unambiguous_project_team(" in backend
    assert "_validate_team_user(fieldname, user)" in backend
    assert 'data-assign="${esc(p.name)}"' in page
    assert "إسناد الفريق الأساسي" in page
    assert "خطط المشرفين" in page
    for field in (
        "project_manager_user", "kitchen_supervisor_user",
        "delivery_supervisor_user", "site_manager_user",
    ):
        assert field in wizard
        marker = f'"fieldname": "{field}"'
        start = project.index(marker)
        assert '"allow_on_submit": 1' in project[start:start + 260]
    print("RC300 Iftar role dashboard and team assignment validation passed")


if __name__ == "__main__":
    main()
