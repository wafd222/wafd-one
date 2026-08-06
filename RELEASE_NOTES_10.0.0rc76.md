# WAFD ONE 10.0.0 RC76

## Workflow navigation fix

- Fixed the **Packaging → Loading** primary action so it no longer stops with “No changes in document” when the packaging record is already saved.
- The action now opens the existing loading record directly, or opens a correctly populated new loading record immediately.
- Fixed the **Loading → Delivery Trip** primary action with the same clean-document protection.
- Removed delayed routing and changed both transitions to direct awaited routes for more reliable operation on desktop and mobile.
- Existing downstream records are opened instead of creating duplicates.

## التعديلات

- إصلاح توقف زر **اعتماد التغليف والانتقال للتحميل** بسبب رسالة «لا توجد تغييرات في المستند».
- فتح سجل التحميل الموجود مباشرة أو فتح سجل جديد معبأ تلقائياً.
- إصلاح زر **اعتماد التحميل وإنشاء رحلة التوصيل** بالطريقة نفسها.
- جعل الانتقال مباشرًا وأكثر ثباتًا على الكمبيوتر والجوال.
- منع تكرار سجلات التحميل ورحلات التوصيل عبر فتح السجل الموجود.
