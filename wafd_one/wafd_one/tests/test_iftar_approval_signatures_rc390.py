"""RC390 safety contract: project-scoped signatures and unchanged undertaking."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]


def read(rel):
    return (BASE / rel).read_text()


def test_signature_fields_are_project_scoped_and_snapshot_at_approval():
    project = json.loads(read('wafd_one/doctype/wafd_iftar_project/wafd_iftar_project.json'))
    operation = json.loads(read('wafd_one/doctype/wafd_iftar_daily_operation/wafd_iftar_daily_operation.json'))
    pf = {f['fieldname']: f for f in project['fields']}
    of = {f['fieldname']: f for f in operation['fields']}
    assert pf['site_manager_signature']['fieldtype'] == 'Signature'
    assert pf['site_manager_signature_user']['fieldtype'] == 'Link'
    assert of['site_report_signature']['fieldtype'] == 'Signature'
    assert of['site_report_approved_name']['fieldtype'] == 'Data'
    source = read('wafd_one/iftar_team.py')
    assert 'site_report_signature": manager_signature' in source
    assert 'site_report_approved_name": manager_name' in source
    assert 'project.site_manager_user != user' in source
    assert 'project.get("site_manager_signature_user") == user' in source
    assert 'project.site_manager_user or "").strip()' in source


def test_site_ui_registers_once_without_approving():
    js = read('wafd_one/page/wafd_iftar_site/wafd_iftar_site.js')
    assert 'ifs-register-signature' in js
    assert 'register_site_manager_project_signature' in js
    assert 'site_signature_registered' in js
    portal = read('wafd_one/iftar_stage_portal.py')
    assert 'registered_signature, signature_owner = frappe.db.get_value' in portal
    assert 'signature_owner == project.get("site_manager_user")' in portal


def test_company_assets_are_read_only_and_no_manual_admin_upload():
    team = read('wafd_one/iftar_team.py')
    assets = team[team.index('def _company_iftar_approval_assets'):team.index('@frappe.whitelist()\ndef send_authority_report')]
    assert 'WAFD Print Settings' in assets
    assert 'WAFD Document Template' in assets
    assert 'WAFD Hotel Undertaking' in assets
    assert 'frappe.db.set_value' not in assets
    assert 'frappe.get_doc("WAFD Hotel Undertaking"' not in assets
    js = read('wafd_one/page/wafd_iftar_team/wafd_iftar_team.js')
    assert 'fieldname:"administration_signature",fieldtype:"Signature"' not in js
    assert 'fieldname:"administration_stamp",fieldtype:"Attach Image"' not in js


def test_official_report_never_displays_approval_email_ids():
    report = read('templates/print_formats/wafd_iftar_official_daily_report.html')
    section = report[report.index('<div class="signature-grid">'):]
    assert 'site_manager_display_name' in section
    assert 'doc.site_report_signature' in section
    assert 'شركة وفد المدينة لخدمات الإعاشة' in section
    assert 'official_administration_signature' in section
    assert 'official_administration_stamp' in section
    assert 'doc.site_report_approved_by' not in section
    assert 'doc.administration_report_approved_by' not in section
