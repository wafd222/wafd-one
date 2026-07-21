from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCHES_FILE = ROOT / "wafd_one" / "patches.txt"


def exposes_execute(module_file: Path) -> bool:
    tree = ast.parse(module_file.read_text(encoding="utf-8"), filename=str(module_file))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "execute":
            return True
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.asname == "execute" or (alias.name == "execute" and alias.asname is None):
                    return True
    return False


def main() -> None:
    errors: list[str] = []
    checked = 0
    for line_no, raw in enumerate(PATCHES_FILE.read_text(encoding="utf-8").splitlines(), 1):
        patch = raw.strip()
        if not patch or patch.startswith("#") or (patch.startswith("[") and patch.endswith("]")):
            continue
        checked += 1
        relative = Path(*patch.split("."))
        module_file = ROOT / f"{relative}.py"
        package_init = ROOT / relative / "__init__.py"
        target = module_file if module_file.is_file() else package_init if package_init.is_file() else None
        if target is None:
            errors.append(f"line {line_no}: module not found: {patch}")
            continue
        if not exposes_execute(target):
            errors.append(f"line {line_no}: {patch} does not expose execute(): {target.relative_to(ROOT)}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Patch path validation passed: {checked} entries")


if __name__ == "__main__":
    main()
