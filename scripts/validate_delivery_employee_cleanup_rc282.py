from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def main():
    role_home = read("wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js")
    delivery = read("wafd_one/wafd_one/page/wafd_delivery_supervisor/wafd_delivery_supervisor.js")
    delivery_css = read("wafd_one/wafd_one/page/wafd_delivery_supervisor/wafd_delivery_supervisor.css")
    employee_ui = read("wafd_one/wafd_one/page/wafd_employee_team/wafd_employee_team.js")
    employee_api = read("wafd_one/employee_team.py")

    assert 'label: "إدارة التوصيل"' in role_home
    assert 'action: "delivery_locations"' in role_home
    assert 'label: "الرحلات الحالية"' not in role_home
    assert 'label: "سجل التسليم"' not in role_home
    for label in ("رحلة واحدة", "جدول عدة أيام", "إفطار صائم"):
        assert label in delivery
    assert "view==='current'" in delivery
    assert "view==='delivered'" in delivery
    assert "button:first-child{grid-column:1/-1}" in delivery_css

    for marker in ("update_employee_account", "delete_employee_account", "_assert_manageable_user", "_has_operational_links", "_archive_employee_account"):
        assert marker in employee_api
    for marker in ("wafd-edit-account", "wafd-delete-account", 'fieldtype: "Password"', "حذف الحساب", "تعديل الحساب"):
        assert marker in employee_ui

    assert 'version = "10.0.0rc282"' in read("pyproject.toml")
    assert "v10_0_0_rc282.execute" in read("wafd_one/patches.txt")
    print("RC282 delivery and employee-account validation passed")


if __name__ == "__main__":
    main()
