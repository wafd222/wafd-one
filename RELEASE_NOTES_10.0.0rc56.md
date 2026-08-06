# WAFD ONE 10.0.0 RC56

## التحصيلات
- تحويل **WAFD Payment** إلى مستند Frappe قابل للاعتماد والإلغاء: Draft → Submitted → Cancelled.
- إرجاع حالة الفاتورة ورصيدها تلقائياً عند إلغاء التحصيل.
- منع إنشاء تحصيل لفاتورة مدفوعة بالكامل.
- منع تجاوز الرصيد المتبقي وتكرار المرجع المالي.
- ترحيل التحصيلات القديمة المعتمدة إلى `docstatus=1` والملغاة إلى `docstatus=2`.

## حذف العقد التجريبي بالكامل
- زر جديد داخل العقد: **حذف العقد وبياناته التجريبية**.
- يعرض معاينة بعدد السجلات التي ستُحذف.
- يتطلب صلاحية Administrator أو System Manager وكتابة عبارة تأكيد خاصة بالعقد.
- يحذف فقط سلسلة العقد المحدد: المشروع، الخطط، الإنتاج، الجودة، التغليف، التحميل، التسليم، الفواتير، والتحصيلات المرتبطة.
- يلغي المستندات المعتمدة أولاً لتشغيل منطق العكس قبل الحذف.

## Final detailed review corrections
- Payment totals now count only submitted (`docstatus=1`) and confirmed WAFD Payment records.
- Project collected revenue uses only submitted confirmed payments.
- One-click contract purge now includes linked WAFD Complaint records.
