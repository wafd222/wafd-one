"""Static regression guard for the RC246 My Trips retrieval path."""

from __future__ import annotations

import ast
from pathlib import Path


root = Path(__file__).resolve().parents[1]
source_path = root / "wafd_one" / "driver_portal.py"
tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))

list_function = next(
    (
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "list_my_trips"
    ),
    None,
)
assert list_function is not None, "list_my_trips was not found"

calls = [node for node in ast.walk(list_function) if isinstance(node, ast.Call)]
call_names = {
    node.func.id
    for node in calls
    if isinstance(node.func, ast.Name)
}
assert "repair_trip_assignments" in call_names, "legacy assignment repair is missing"
assert "trips_for_user" in call_names, "secure explicit server-side filtering is missing"

for call in calls:
    if isinstance(call.func, ast.Attribute) and call.func.attr == "get_all":
        assert all(keyword.arg != "or_filters" for keyword in call.keywords), (
            "list_my_trips must not restore the combined or_filters query"
        )

print("RC246 My Trips retrieval validation passed")
