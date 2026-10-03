"""Regression checks for RC353 Delivery Viewer localization."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
page = (ROOT / "wafd_one/wafd_one/page/wafd_delivery_viewer/wafd_delivery_viewer.js").read_text()
assert 'const T = {' in page
assert '"بيانات التسليم": {en:"Delivery Data",id:"Data Pengiriman"' in page
assert '"موعد التوصيل": {en:"Scheduled delivery",id:"Jadwal pengiriman"' in page
assert '"تم التسليم": {en:"Delivered",id:"Terkirim"' in page
assert '"في الطريق": {en:"In transit",id:"Dalam perjalanan"' in page
assert 'const rtl = lang === "ar" || lang === "ur";' in page
assert 'const $root = $(page.body).attr("dir", rtl ? "rtl" : "ltr");' in page
assert 'const tr = (a, e) => lang === "ar" ? a : (T[a]?.[lang] || e || a);' in page
assert 'id:"Dalam perjalanan"' in page
print("RC353 Delivery Viewer localization checks passed")
