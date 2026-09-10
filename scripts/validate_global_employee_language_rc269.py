from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    role_home = (ROOT / "wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js").read_text(encoding="utf-8")
    cleaning = (ROOT / "wafd_one/wafd_one/page/wafd_cleaning_home/wafd_cleaning_home.js").read_text(encoding="utf-8")
    driver = (ROOT / "wafd_one/wafd_one/page/wafd_driver_trips/wafd_driver_trips.js").read_text(encoding="utf-8")
    storekeeper = (ROOT / "wafd_one/wafd_one/page/wafd_storekeeper_home/wafd_storekeeper_home.js").read_text(encoding="utf-8")
    language_api = (ROOT / "wafd_one/language.py").read_text(encoding="utf-8")

    assert role_home.count('id="wafd-pwa-language"') == 1
    assert "wafd-role-lang" not in role_home
    assert "set_user_language" in role_home and "window.location.reload()" in role_home
    assert "wafd-clean-lang" not in cleaning
    assert "page.set_title(t(\"title\"))" in cleaning
    assert "wafdApplyCleaningLanguage" in cleaning
    for code in ("ar", "en", "bn", "ur", "hi", "id", "fr", "ha", "sw", "uz"):
        assert f"{code}:" in cleaning
        assert code in language_api
    assert "activeLanguage" in driver and 'localStorage.getItem("wafd_lang")' in driver
    assert 'localStorage.getItem("wafd_lang")' in storekeeper
    assert "Receive and Distribute Purchases" in storekeeper
    assert "Hand Over Materials to Employees" in storekeeper
    assert "localData" in storekeeper
    print("RC269 global employee language validation passed")


if __name__ == "__main__":
    main()
