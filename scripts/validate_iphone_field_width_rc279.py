#!/usr/bin/env python3
from pathlib import Path
root = Path(__file__).resolve().parents[1]
nav = (root / "wafd_one/public/js/wafd_mobile_navigation.js").read_text(encoding="utf-8")
bundle = (root / "wafd_one/public/wafd_mobile_navigation.bundle.js").read_text(encoding="utf-8")
assert nav == bundle
assert '(activePage || document.body).prepend(bar)' in nav
assert 'document.body.prepend(bar)' not in nav
assert 'v10_0_0_rc279.execute' in (root / "wafd_one/patches.txt").read_text(encoding="utf-8")
assert 'version = "10.0.0rc' in (root / "pyproject.toml").read_text(encoding="utf-8")
print("RC279 iPhone field width validation passed")
