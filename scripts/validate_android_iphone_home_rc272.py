from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def main():
    source_js = read("wafd_one/public/js/wafd_mobile_navigation.js")
    bundle_js = read("wafd_one/public/wafd_mobile_navigation.bundle.js")
    source_css = read("wafd_one/public/css/wafd_mobile_navigation.css")
    bundle_css = read("wafd_one/public/wafd_mobile_navigation.bundle.css")
    role_home = read("wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js")

    assert source_js == bundle_js
    assert source_css == bundle_css
    assert "/Android|iPhone|iPad|iPod|Mobile/i" in source_js
    assert 'window.matchMedia("(max-width: 900px)").matches || mobileUa || touchDevice' in source_js
    assert "const hide = !!(home && isMobile());" in source_js
    assert "home && isMobile() && isStandalonePwa()" not in source_js
    for selector in (".navbar", ".layout-side-section", ".standard-sidebar", ".desk-sidebar", ".body-sidebar-container"):
        assert selector in source_js and selector in source_css
    assert "@media (max-width: 900px), (pointer: coarse)" in source_css
    assert ".wafd-pwa-appbar" in source_css
    assert "wafd-pwa-language" in role_home
    assert "localStorage.setItem(\"wafd_lang\",uiLang)" in role_home
    assert 'const isMobile = window.matchMedia("(max-width: 900px)").matches || mobileUa || touchDevice;' in role_home
    assert "wafd_one.wafd_one.patches.v10_0_0_rc272.execute" in read("wafd_one/patches.txt")
    print("RC272 Android/iPhone unified home validation passed")


if __name__ == "__main__":
    main()
