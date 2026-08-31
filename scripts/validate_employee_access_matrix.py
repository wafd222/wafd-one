"""Validate every employee home card against installed Page/DocType permissions."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROLE_HOME_JS = ROOT / "wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js"
ROLE_HOME_JSON = ROOT / "wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.json"

REQUIRED_CAPABILITIES = {
    ("WAFD Project Manager", "WAFD Catering Project"): {"read"},
    ("WAFD Production Supervisor", "WAFD Production Batch"): {"read", "write", "create"},
    ("WAFD Production Supervisor", "WAFD Packaging Record"): {"read"},
    ("WAFD Quality Inspector", "WAFD Quality Inspection"): {"read", "write", "create"},
    ("WAFD Quality Inspector", "WAFD CCP Check"): {"read", "write", "create"},
    ("WAFD Storekeeper", "WAFD Stock Movement"): {"read", "write", "create"},
    ("WAFD Cleaning Supervisor", "WAFD Stock Balance"): {"read"},
    ("WAFD Cleaning Supervisor", "WAFD Stock Movement"): {"read"},
    ("WAFD Delivery Supervisor", "WAFD Delivery Trip"): {"read", "write", "create"},
    ("WAFD Delivery Supervisor", "WAFD Loading Record"): {"read", "write", "create"},
    ("WAFD Driver", "WAFD Delivery Trip"): {"read", "write"},
    ("WAFD Finance User", "WAFD Invoice"): {"read", "write", "create"},
    ("WAFD Finance User", "WAFD Payment"): {"read", "write", "create"},
    ("WAFD Approver", "WAFD Approval Request"): {"read", "write"},
    ("WAFD Auditor", "WAFD Invoice"): {"read"},
    ("WAFD Auditor", "WAFD Payment"): {"read"},
    ("WAFD Undertaking Officer", "WAFD Hotel Undertaking"): {"read", "write", "create"},
    ("WAFD Undertaking Reviewer", "WAFD Hotel Undertaking"): {"read"},
    ("WAFD Operations Manager", "WAFD Quotation"): {"read", "write", "create"},
    ("WAFD Project Manager", "WAFD Quotation"): {"read", "write", "create"},
    ("WAFD Approver", "WAFD Quotation"): {"read", "write"},
    ("WAFD Finance User", "WAFD Quotation"): {"read"},
    ("WAFD Auditor", "WAFD Quotation"): {"read"},
}


def managed_roles():
    module = ast.parse((ROOT / "wafd_one/employee_team.py").read_text(encoding="utf-8"))
    for node in module.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "ROLE_LABELS" for target in node.targets
        ):
            return set(ast.literal_eval(node.value))
    raise AssertionError("ROLE_LABELS was not found")


def role_targets():
    text = ROLE_HOME_JS.read_text(encoding="utf-8")
    matches = list(re.finditer(r'\brole:\s*"([^"]+)"', text))
    targets = {}
    for index, match in enumerate(matches):
        role = match.group(1)
        end = matches[index + 1].start() if index + 1 < len(matches) else text.find(
            "const preferredRole", match.start()
        )
        block = text[match.start() : end]
        targets[role] = re.findall(r'\b(page|doctype):\s*"([^"]+)"', block)
    return targets


def page_index():
    index = {}
    for path in ROOT.glob("wafd_one/wafd_one/page/*/*.json"):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("doctype") == "Page":
            index[doc["name"]] = doc
    return index


def doctype_index():
    index = {}
    for path in ROOT.glob("wafd_one/wafd_one/doctype/*/*.json"):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("doctype") == "DocType":
            index[doc["name"]] = doc
    return index


def main():
    employees = managed_roles()
    targets = role_targets()
    pages = page_index()
    doctypes = doctype_index()
    home_roles = {row["role"] for row in json.loads(ROLE_HOME_JSON.read_text())["roles"]}

    assert employees <= set(targets), f"Roles missing from role home: {sorted(employees - set(targets))}"
    assert employees <= home_roles, f"Roles blocked from role home Page: {sorted(employees - home_roles)}"

    checked = 0
    for role in sorted(employees | {"System Manager", "WAFD Operations Manager"}):
        role_items = targets.get(role) or []
        assert role_items, f"No home tools configured for {role}"
        for kind, target in role_items:
            checked += 1
            if kind == "page":
                assert target in pages, f"Missing Page {target} shown to {role}"
                allowed = {row["role"] for row in pages[target].get("roles", [])}
                assert role in allowed, f"{role} cannot open Page {target}"
            else:
                assert target in doctypes, f"Missing DocType {target} shown to {role}"
                permissions = {
                    row["role"]: row for row in doctypes[target].get("permissions", [])
                }
                permission = permissions.get(role) or {}
                assert permission.get("read") or permission.get("select"), (
                    f"{role} cannot read DocType {target}"
                )

    assert "assigned_driver_user" in {
        field.get("fieldname") for field in doctypes["WAFD Delivery Trip"]["fields"]
    }
    for (role, doctype), required in REQUIRED_CAPABILITIES.items():
        permission = next(
            (
                row
                for row in doctypes[doctype].get("permissions", [])
                if row.get("role") == role
            ),
            {},
        )
        missing = sorted(capability for capability in required if not permission.get(capability))
        assert not missing, f"{role} lacks {missing} on {doctype}"
    print(
        f"Employee access validation passed: {len(employees)} roles, "
        f"{checked} role-home targets, {len(REQUIRED_CAPABILITIES)} operational checks"
    )


if __name__ == "__main__":
    main()
