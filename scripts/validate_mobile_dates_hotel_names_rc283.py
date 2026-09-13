import ast
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    page = (ROOT / "wafd_one/wafd_one/page/wafd_delivery_supervisor/wafd_delivery_supervisor.js").read_text(encoding="utf-8")
    patch = (ROOT / "wafd_one/wafd_one/patches/v10_0_0_rc283/execute.py").read_text(encoding="utf-8")
    ast.parse(patch)
    assert "unicode-bidi:bidi-override" in page
    assert 'setAttribute("dir","ltr")' in page
    assert 'setAttribute("lang","en-CA")' in page
    assert "OLD_ARABIC" in patch and "WAFD Delivery Trip" in patch
    for corrected in ("الصفا البركة", "فندق آفاق السلام الذهبي", "فندق برج مودة", "نزل سنابل المدينة"):
        assert corrected in patch

    data_file = ROOT / "wafd_one/reference_data/madinah_hotels_400_ota_review.csv"
    with data_file.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 400
    arabic = {row["hotel_name_ar"] for row in rows}
    assert "الصفا البركة" in arabic
    assert any(name.startswith("فندق آفاق السلام الذهبي") for name in arabic)
    for wrong in ("الصفا ال باراكاه", "فندق افاك السلام الذهبي يكس ريياده المدينة", "فندق بورج مودة"):
        assert wrong not in arabic

    assert 'version = "10.0.0rc283"' in (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "v10_0_0_rc283.execute" in (ROOT / "wafd_one/patches.txt").read_text(encoding="utf-8")
    print("RC283 mobile date and Arabic hotel-name validation passed")


if __name__ == "__main__":
    main()
