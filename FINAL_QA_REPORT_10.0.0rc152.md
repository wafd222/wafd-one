# FINAL QA REPORT — WAFD ONE 10.0.0 RC152

## هدف الإصدار
توحيد صلاحيات جميع أدوار WAFD ONE داخل الكود وإنهاء الاعتماد على التعديلات اليدوية المتفرقة في Role Permissions Manager.

## نطاق المراجعة
تمت مراجعة 56 DocType غير فرعي داخل WAFD ONE، وجميع أدوار WAFD التشغيلية:
- WAFD Operations Manager
- WAFD Project Manager
- WAFD Production Supervisor
- WAFD Quality Inspector
- WAFD Delivery Supervisor
- WAFD Driver
- WAFD Finance User
- WAFD Storekeeper
- WAFD Approver
- WAFD Auditor
- System Manager

## قواعد الفصل الوظيفي المعتمدة
- System Manager: تحكم إداري كامل.
- WAFD Operations Manager: تحكم تشغيلي شامل مع تقليل الحذف في السجلات المعاملاتية.
- Project Manager: إدارة المشروع/العقد/الخطط/التعهدات، وقراءة ما يلزم من المراحل التابعة.
- Production Supervisor: إدارة الإنتاج والتغليف وما يتعلق بهما، والوصفات للقراءة فقط.
- Quality Inspector: إدارة فحوص الجودة وCCP، وقراءة السجلات التشغيلية التابعة.
- Delivery Supervisor: إدارة التحميل والتوصيل والاستلام والأسطول التشغيلي.
- Driver: وصول محدود لما يحتاجه لإثبات التسليم.
- Storekeeper: إدارة المكونات والمخزون والحركات والمشتريات والموردين، والوصفات للقراءة فقط.
- Finance User: إدارة الفواتير والمدفوعات والتكاليف والإيرادات، وقراءة البيانات التشغيلية اللازمة.
- Approver: محصور في طلبات الاعتماد.
- Auditor: قراءة/تقارير/تصدير فقط، بدون إنشاء أو تعديل.

## الصلاحيات القياسية ERPNext/Frappe
تمت إضافة سياسة Lookup آمنة للأدوار التي تحتاجها على:
- Item
- Item Group
- UOM
- Warehouse

يتم الحفاظ على صلاحيات ERPNext الأصلية عن طريق نسخ DocPerm القياسي إلى Custom DocPerm أولاً ثم استبدال صفوف WAFD فقط، حتى لا تتأثر أدوار ERPNext الأصلية.

## حماية الوصفات
- Production Supervisor: Read/Print/Report فقط.
- Storekeeper: Read/Print/Report فقط.
- إنشاء/تعديل/حذف الوصفات: System Manager وWAFD Operations Manager فقط.
- يوجد تحقق Server-side داخل WAFD Recipe لمنع تجاوز الواجهة.

## صفحات النظام
تم تقييد الصفحات الحساسة حسب الدور، بما في ذلك:
- WAFD Administration Console
- WAFD Document Studio
- WAFD Launch Center
- WAFD Iftar Wizard
- WAFD Iftar Operations
- WAFD Iftar Report Center
- WAFD ONE Dashboard

## اختبارات تم تنفيذها محلياً على الحزمة
- Permission metadata audit: PASS — 56 DocTypes.
- Critical segregation assertions: PASS.
- Page-role audit: PASS.
- Standard lookup Custom DocPerm safety audit: PASS.
- Python compilation: PASS.
- Patch path validation: PASS — 143 entries.
- Release validator: PASS — 10.0.0rc152.
- ZIP integrity test: to be run after packaging.

## ملاحظة تشغيلية
الاختبارات المحلية تتحقق من الكود والـmetadata ومسارات الترحيل. الاختبار النهائي داخل Frappe Cloud يحتاج Deploy/Migrate ثم تسجيل الدخول بحسابات اختبار لكل دور للتأكد من سلوك الواجهة والخادم مع بيانات الموقع الفعلية.
