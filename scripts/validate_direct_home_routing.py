"""Static and isolated regression checks for RC249 login/home routing."""

from __future__ import annotations

import ast
import json
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_HOME = "/app/wafd-role-home"


def _assignment(module, name):
    for node in module.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name} was not found")


class RedirectSignal(Exception):
    pass


def _mobile_target(user, roles):
    fake = types.ModuleType("frappe")
    fake.session = types.SimpleNamespace(user=user)
    fake.local = types.SimpleNamespace(flags=types.SimpleNamespace())
    fake.Redirect = RedirectSignal
    fake.get_roles = lambda _user: list(roles)

    source = ROOT / "wafd_one/www/wafd_mobile.py"
    module = types.ModuleType("wafd_mobile_under_test")
    previous = sys.modules.get("frappe")
    sys.modules["frappe"] = fake
    try:
        exec(compile(source.read_text(encoding="utf-8"), str(source), "exec"), module.__dict__)
        try:
            module.get_context(types.SimpleNamespace())
        except RedirectSignal:
            return fake.local.flags.redirect_location
        raise AssertionError("wafd_mobile did not redirect")
    finally:
        if previous is None:
            sys.modules.pop("frappe", None)
        else:
            sys.modules["frappe"] = previous


def main():
    hooks_source = ROOT / "wafd_one/hooks.py"
    hooks = ast.parse(hooks_source.read_text(encoding="utf-8"))
    assert _assignment(hooks, "app_home") == CANONICAL_HOME

    rules = _assignment(hooks, "website_route_rules")
    assert not any(row.get("from_route") == CANONICAL_HOME for row in rules), (
        "The canonical Desk Page route must not be captured by website_route_rules"
    )
    assert any(row.get("from_route") == "/wafd-mobile" for row in rules)
    launch_template = ROOT / "wafd_one/www/wafd_mobile.html"
    assert launch_template.exists(), "The /wafd-mobile controller requires a website template"
    launch_html = launch_template.read_text(encoding="utf-8")
    assert 'window.location.replace("/app/wafd-role-home")' in launch_html

    redirects = _assignment(hooks, "website_redirects")
    assert any(
        row.get("source") == r"/desk/wafd-role-home/?"
        and row.get("target") == CANONICAL_HOME
        for row in redirects
    )

    apps = _assignment(hooks, "add_to_apps_screen")
    wafd_app = next(row for row in apps if row.get("name") == "wafd_one")
    assert wafd_app.get("route") == CANONICAL_HOME

    assert _mobile_target("Guest", ()) == "/login?redirect-to=/wafd-mobile"
    assert _mobile_target("driver@example.com", {"WAFD Driver"}) == CANONICAL_HOME
    assert _mobile_target("manager@example.com", {"WAFD Operations Manager"}) == CANONICAL_HOME
    assert _mobile_target(
        "mixed@example.com", {"WAFD Client Portal User", "WAFD Operations Manager"}
    ) == CANONICAL_HOME
    assert _mobile_target(
        "client@example.com", {"WAFD Client Portal User"}
    ) == "/wafd-client"

    manifest = json.loads(
        (ROOT / "wafd_one/public/pwa/manifest.webmanifest").read_text(encoding="utf-8")
    )
    assert manifest["start_url"] == CANONICAL_HOME

    fallbacks = (
        ROOT / "wafd_one/public/js/wafd_mobile_navigation.js",
        ROOT / "wafd_one/public/wafd_mobile_navigation.bundle.js",
        ROOT / "wafd_one/wafd_one/doctype/wafd_hotel_undertaking/wafd_hotel_undertaking.js",
    )
    for path in fallbacks:
        text = path.read_text(encoding="utf-8")
        assert f'window.location.assign("{CANONICAL_HOME}")' in text

    patch = (
        ROOT / "wafd_one/wafd_one/patches/v10_0_0_rc249/execute.py"
    ).read_text(encoding="utf-8")
    assert 'CANONICAL_HOME = "/app/wafd-role-home"' in patch
    assert '"/desk/wafd-role-home"' in patch

    print("Direct home routing validation passed: guest, driver, manager, mixed and client")


if __name__ == "__main__":
    main()
