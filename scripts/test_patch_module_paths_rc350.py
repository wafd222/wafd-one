#!/usr/bin/env python3
"""Every migration entry must resolve to a Python file in the release ZIP."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
entries = []
for raw in (ROOT / "wafd_one" / "patches.txt").read_text(encoding="utf-8").splitlines():
    entry = raw.strip()
    if not entry or entry.startswith("#") or entry.startswith("["):
        continue
    entries.append(entry)

missing = []
for entry in entries:
    path = ROOT / (entry.replace(".", "/") + ".py")
    if not path.is_file():
        missing.append(f"{entry} -> {path.relative_to(ROOT)}")

if missing:
    raise AssertionError("Missing migration modules:\n" + "\n".join(missing))

print(f"RC350 migration module path checks passed ({len(entries)} entries)")
