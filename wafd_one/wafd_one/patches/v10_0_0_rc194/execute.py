"""RC194: replace undertaking terms with the approved hotel terms, renumbered 1-7."""
import json
import frappe

TARGET = "WAFD Hotel Undertaking"
TERMS_HTML = r'''<div style="direction:rtl;border:1px solid #ddd;padding:9px;font-size:8.7px;line-height:1.45;"><b>الشروط والملاحظات</b><ol style="margin:5px 18px 0 0;padding:0;"><li>يتعهد الطرفان بصحة البيانات المدونة أعلاه.</li><li>يلتزم الطرفان بالمواعيد المحددة في تقديم الوجبات دون تأخير.</li><li>يحق للطرف الأول المطالبة بإلغاء التعهد والمطالبة بالمبالغ المتبقية في حالة زيادة الأعداد أو اختلاف في البيانات المدونة، ولا يتم تعديل أي بند من القائمة أو جدول المواعيد.</li><li>يلتزم الطرف الثاني بتأمين عمالة بشهادات صحية للتوريد للفندق.</li><li>يجب على الفندق التدقيق والتأكد من صحة البيانات، وهي على مسؤولية الفندق في حالة عدم مطابقتها.</li><li>يحق للفندق رفض التعهد في حالة عدم صحة البيانات للأعداد أو الأيام أو الجنسية.</li><li>يلتزم الطرف الأول بتسليم الفندق صورة من الأوراق الرسمية من السجل، ورخصة البلدية، والعقد الخاص بالتغذية</li></ol><div style="margin-top:6px;font-weight:700;">نأمل من إدارة الفندق التعاون والتواصل معنا بشكل مباشر في وجود أي ملاحظات ليتم تلافيها فوراً من قبلنا، وعرض هذا التعهد للجهات المسؤولة.</div></div>'''

def execute():
    if frappe.db.exists("DocType", "WAFD Document Template"):
        rows = frappe.get_all("WAFD Document Template", filters={"reference_doctype": TARGET}, fields=["name", "canvas_json"])
        for row in rows:
            try:
                canvas = json.loads(row.canvas_json or "{}")
            except Exception:
                continue
            changed = False
            for block in canvas.get("blocks") or []:
                bid = str(block.get("id") or "").lower()
                if bid == "terms":
                    block["html"] = TERMS_HTML
                    block["text"] = TERMS_HTML
                    block["content"] = TERMS_HTML
                    block["height"] = max(int(block.get("height") or 0), 225)
                    changed = True
                elif bid in {"signatory", "signature", "stamp"}:
                    y = int(block.get("y") or 0)
                    if y and y < 840:
                        block["y"] = y + 60
                        changed = True
            if changed:
                frappe.db.set_value("WAFD Document Template", row.name, {"canvas_json": json.dumps(canvas, ensure_ascii=False), "compiled_html": ""}, update_modified=False)
    from wafd_one.setup import ensure_hotel_undertaking_print_format
    ensure_hotel_undertaking_print_format()
    frappe.clear_cache(doctype=TARGET)
