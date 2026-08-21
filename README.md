# WAFD ONE 10.0.0 RC214

**Current release: 10.0.0 RC214 — Undertaking Direct Save Flow, Officer Deactivation Enforcement & Mobile Back Button Fix**

نظام تشغيل وإدارة متكامل لشركة **وفد المدينة لخدمات الإعاشة**، مبني على Frappe Framework v16 لإدارة دورة الإعاشة من التخطيط والتشغيل حتى الفوترة والتحصيل.

## الوحدات الرئيسية

- المشاريع والبعثات والفنادق والعقود
- خطط الوجبات والوصفات والمكونات
- الإنتاج والجودة وسلامة الغذاء والتغليف
- التحميل والتوصيل وإثبات التسليم
- الأسطول والسائقون والمركبات
- الموردون والمشتريات والمستودعات والمخزون
- الفواتير والتحصيل والتكاليف وربحية المشاريع
- بوابة العميل الخارجية
- إفطار صائم والتقارير التشغيلية

## المسار التشغيلي

المشروع → خطة الوجبات → الإنتاج → الجودة → التغليف → التحميل → التوصيل → إثبات التسليم → الفاتورة → التحصيل.

## التثبيت والتحديث على Frappe Cloud

استخدم المستودع مع Frappe Framework v16، ثم نفّذ التثبيت أو التحديث المعتاد للتطبيق وتشغيل `migrate`. يقوم WAFD ONE بمزامنة الإعدادات والواجهات المطلوبة عبر hooks وعمليات ما بعد الترحيل.

## ملاحظات سلامة الترقية

- لا تحذف أو تعيد ترتيب السجل التاريخي في `wafd_one/patches.txt`.
- ملفات البيانات المرجعية وقوالب الاستيراد محفوظة لاستخدامها عند تجهيز بيانات التشغيل الحقيقية.
- يتضمن RC192 patch آمنًا لاستعادة التوقيع/الختم القديمين وتحديث قالب التعهد؛ لذلك يجب تشغيل `migrate` بعد الرفع.


## RC211
Removes undertaking signature/stamp status chips and prevents restricted officers from triggering protected attachment-file reads while keeping the approved assets automatic in Preview/PDF.



## RC214
- Keep a newly saved undertaking open on its own Form instead of returning to the list.
- Disabling an undertaking officer now invalidates active sessions immediately and blocks undertaking access server-side.
- Mobile/admin back control now has a guaranteed visible dark-gold arrow and is fixed at the upper-right without changing page width.
- Preserves RC213 private-file permissions, PDF preview/issue/save/share, signature, stamp and approved terms.

## RC213
Repairs least-privilege access to undertaking-generated PDFs and the centrally managed signature/stamp assets for undertaking officers, without granting general File access.
