from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
portal = (ROOT / "wafd_one" / "www" / "wafd_client.html").read_text(encoding="utf-8")
version = (ROOT / "wafd_one" / "__init__.py").read_text(encoding="utf-8")
pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
readme = (ROOT / "README.md").read_text(encoding="utf-8")

assert '10.0.0rc175' in version
assert 'version = "10.0.0rc175"' in pyproject
assert '10.0.0 RC175' in readme
assert "tr:'Türkçe'" in portal
for token in ('Teslimat başlangıcı','Varış zamanı','Teslim alma zamanı','Teslim alan kişi','Teslimattan teslim almaya kadar geçen süre','Yükleme','Yolda','Varış','Teslim alma'):
    assert token in portal, token
assert "tr:'Onaylandı'" in portal
print('RC175 Turkish portal + release metadata validation: PASS')
