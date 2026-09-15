from pathlib import Path
import ast


ROOT = Path(__file__).resolve().parents[1]


def main():
    css = (ROOT / "wafd_one/wafd_one/page/wafd_iftar_team/wafd_iftar_team.css").read_text(encoding="utf-8")
    page = (ROOT / "wafd_one/wafd_one/page/wafd_iftar_team/wafd_iftar_team.js").read_text(encoding="utf-8")
    backend_path = ROOT / "wafd_one/wafd_one/iftar_team.py"
    backend = backend_path.read_text(encoding="utf-8")
    ast.parse(backend)
    assert "grid-template-columns:minmax(0,1fr) minmax(112px,1fr)" in css
    assert "font-variant-numeric:tabular-nums" in css
    assert "const complete=Number(p.supervisors_count)>0" in page
    assert "أضف المشرفين وأصحاب السفر" in page
    assert '"time": when if cint(done) else None' in backend
    assert "def normalize_legacy_iftar_sequence(" in backend
    assert '"authority_inspection_approved": 0' in backend
    assert '"جاهز للتحميل / Ready to Load" if effective_ready' in backend
    print("RC302 Iftar mobile and legacy-sequence validation passed")


if __name__ == "__main__":
    main()
