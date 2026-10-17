# WAFD ONE 10.0.0 RC379

**Current release: 10.0.0 RC379 — Repair authority report images and mobile return navigation**

نظام تشغيل وإدارة متكامل لشركة **وفد المدينة لخدمات الإعاشة**، مبني على Frappe Framework v16 لإدارة دورة الإعاشة من العقد والتخطيط وحتى التسليم والفوترة والتحصيل.


## RC310 — وصول مهام إفطار الصائم للموظفين

- يعتمد ظهور المهمة على الموظف المسند داخل المشروع نفسه، وليس على ترتيب الأدوار في الحساب.
- يدعم الموظف صاحب أكثر من مهمة ويعرض جميع مهامه في شاشة واحدة.
- يضيف بطاقة مهمة إفطار الصائم مباشرة في الصفحة الرئيسية للموظف بعد اعتماد المشروع.
- يصلح أدوار الموظفين للمشاريع الحالية ويعيد توليد سجلات التشغيل اليومية المفقودة دون تغيير التاريخ التشغيلي.


## RC379 — إصلاح التقرير الرسمي والعودة من معاينة الجوال

- يحل تضمين صور التقرير من سجل File ومخازن Frappe، مع معالجة أسماء الملفات المشفرة، بدلاً من الاعتماد على مسار ملف محلي فقط.
- يمنع طبقة الانتظار من البقاء فوق شاشة المتابع الخارجي عند الرجوع من معاينة التقرير أو المشاركة على iPhone.
- يعطل تجميد واجهة Frappe أثناء تجهيز ملف PDF، ويزيل الرجوع غير الآمن عبر سجل المتصفح الذي قد يخرج من شاشة المتابعة.
- نطاق التعديل محصور في التقرير الرسمي للجهة المتعاقدة والتنقل الخاص به؛ لا تغيير في وحدات التشغيل الأخرى أو البيانات أو الصلاحيات.
- التحقق: فحص JavaScript وPython، و30 اختباراً مستهدفاً ناجحاً، وسلامة بنية ZIP. يلزم التحقق البصري النهائي من الصور على بيئة Frappe Cloud بعد النشر.

## الوحدات الرئيسية

- المشاريع والبعثات والفنادق والعقود
- خطط الوجبات والوصفات والمكونات
- الإنتاج والجودة وسلامة الغذاء والتغليف
- التحميل والتوصيل وإثبات التسليم
- الأسطول والسائقون والمركبات
- الموردون والمشتريات والمستودعات والمخزون
- الفواتير والتحصيل والتكاليف وربحية المشاريع
- التعهدات الفندقية وإدارة فريق التعهدات
- بوابة العميل الخارجية
- إفطار صائم والتقارير التشغيلية

## المسار التشغيلي

العقد → المشروع → خطة الوجبات اليومية → الإنتاج → الجودة → التغليف → التحميل → التوصيل → إثبات التسليم → الفاتورة → التحصيل.

## التثبيت والتحديث على Frappe Cloud

استخدم المستودع مع Frappe Framework v16 ثم نفّذ التحديث/النشر المعتاد. عند وجود patches جديدة في أي إصدار مستقبلي يجب تشغيل `migrate`. RC225 يضيف حقل الاسم العربي للفندق ويحدّث بيانات الفنادق الثنائية اللغة، لذلك يجب تشغيل migrate بعد النشر.

## ملاحظات سلامة الترقية

- RC302 يصلح التفاف الأرقام في بطاقات الجوال، ويطبع مراحل السجلات القديمة وفق تسلسل RC301 دون اعتماد فحص سابق للاستلام.
- RC301 يحول إفطار الصائم إلى سلسلة تشغيل معتمدة زمنياً من خطة الإدارة حتى إرسال التقرير للجهة، ويستخدم جدول التوصيل الحالي دون إنشاء رحلة مكررة.
- RC300 يفصل استعلامات كل شاشة حسب صلاحيتها، ويضيف إسناد الفريق الثابت للمشروع حتى تظهر بيانات اليوم للحساب الصحيح دون توسيع الصلاحيات.
- RC299 يصلح فشل ترحيل RC298 الناتج عن غياب وحدة Python الخاصة بجدول أصحاب السفر اليومي، ويضيف فحص إصدار يمنع تكرار نقص وحدات DocType من الحزمة.
- لا تحذف أو تعيد ترتيب السجل التاريخي في `wafd_one/patches.txt`.
- ملفات البيانات المرجعية وقوالب الاستيراد جزء من تجهيز بيانات التشغيل ولا تُحذف لمجرد تقليل الحجم.
- RC219 هو خط الأساس المعتمد لإصلاح زر الرجوع على الجوال، وRC222 يحافظ على سلوك التنقل المعتمد.
- RC222 يقوّي فقط مسار الحفظ الأول للتعهد بحيث يبقى المستخدم داخل التعهد الجديد، مع الحفاظ على PDF والتوقيع والختم والصلاحيات الحالية.


## RC223 final consolidated QA
- Preserves the validated RC222 undertaking direct-preview and manager-permission fixes.
- Synchronizes both Python package version markers with pyproject metadata.
- Revalidates patch paths, release structure, JavaScript/JSON syntax, assets, finance safeguards, and repository cleanliness.

## RC363 — Iftar pricing and authority-viewer candidate
- Adds an editable project-level standard meal base price (default SAR 9.00 VAT-inclusive) while retaining the calculated selling price and VAT accounting.
- Adds per-table-owner handover evidence to the authority monitoring view and an interactive report preview with zoom/scroll/print/share controls.
- See `wafd_one/RELEASE_NOTES_10.0.0rc363.md` for scope and verification limits. This source candidate requires staging verification before production deployment.

## RC364 — Focused Iftar workflow completion
- Extends the RC363 candidate with the kitchen vehicle-assignment queue after loading approval, including project-manager access to driver/vehicle reassignment before proof of delivery.
- Synchronizes the assigned driver login when a WAFD Driver is changed.
- Removes the separate delivery-supervisor selection from the Iftar employee assignment dialog while retaining any legacy assignment data for rollback/compatibility.
- Adds delivery photos and table-owner evidence to the authority report preview and print layout.
- See `wafd_one/RELEASE_NOTES_10.0.0rc366.md`. The unchanged RC362 backup remains separate.
