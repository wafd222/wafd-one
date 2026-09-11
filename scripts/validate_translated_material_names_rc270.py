from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]


def main():
    meta = json.loads((ROOT / "wafd_one/wafd_one/doctype/wafd_ingredient/wafd_ingredient.json").read_text(encoding="utf-8"))
    fieldnames = {row.get("fieldname") for row in meta.get("fields", [])}
    expected = {
        "ingredient_name_en", "ingredient_name_bn", "ingredient_name_ur",
        "ingredient_name_hi", "ingredient_name_id", "ingredient_name_fr",
        "ingredient_name_ha", "ingredient_name_sw", "ingredient_name_uz",
    }
    assert expected <= fieldnames

    patch = (ROOT / "wafd_one/wafd_one/patches/v10_0_0_rc270/execute.py").read_text(encoding="utf-8")
    for material in ("أكياس نفايات", "شرائط فحص تعقيم", "غطاء رأس استخدام واحد", "منظف أرضيات مركز"):
        assert material in patch
    for translated in ("Waste Bags", "Sanitizer Test Strips", "Disposable Hair Cover"):
        assert translated in patch
    assert "update_modified=False" in patch

    cleaning_api = (ROOT / "wafd_one/cleaning_portal.py").read_text(encoding="utf-8")
    cleaning_ui = (ROOT / "wafd_one/wafd_one/page/wafd_cleaning_home/wafd_cleaning_home.js").read_text(encoding="utf-8")
    store_api = (ROOT / "wafd_one/storekeeper_portal.py").read_text(encoding="utf-8")
    store_ui = (ROOT / "wafd_one/wafd_one/page/wafd_storekeeper_home/wafd_storekeeper_home.js").read_text(encoding="utf-8")
    assert "get_cleaning_dashboard(language=None)" in cleaning_api
    assert cleaning_api.count("add_ingredient_labels") >= 4
    assert "args:{language:lang}" in cleaning_ui
    assert cleaning_ui.count("ingredient_label") >= 4
    assert "language_field(language)" in store_api
    assert store_api.count("add_ingredient_labels") >= 5
    assert store_ui.count("language: lang") >= 5
    assert store_ui.count("ingredient_label") >= 3

    patches = (ROOT / "wafd_one/patches.txt").read_text(encoding="utf-8")
    assert "wafd_one.wafd_one.patches.v10_0_0_rc270.execute" in patches
    print("RC270 translated material names validation passed")


if __name__ == "__main__":
    main()
