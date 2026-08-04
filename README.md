**Current release: 10.0.0 RC81**

# WAFD ONE

Production governance, approvals, auditability, operations, food safety and financial intelligence.

# WAFD ONE

نظام تشغيل وإدارة متكامل لشركة وفد المدينة لخدمات الإعاشة، مبني على Frappe Framework v16.

## الوحدات

- المشاريع والبعثات والفنادق والعقود
- خطط الوجبات والوصفات والمكونات
- الإنتاج وفحص الجودة والتحميل
- التوصيل وإثبات التسليم والشكاوى
- الأسطول والسائقون والمركبات
- الموردون والمشتريات والمستودعات والمخزون
- التكاليف والإيرادات والفواتير وربحية المشاريع

## المسار التشغيلي

المشروع → خطة الوجبات → الإنتاج → الجودة → التحميل → التوصيل → إثبات التسليم → التقارير المالية.

## التثبيت السحابي

أضف المستودع إلى Bench يعمل بـ Frappe v16، ثبّت التطبيق على الموقع، ثم نفّذ التحديث. يقوم التطبيق بمزامنة مساحة WAFD ONE تلقائيًا بعد كل migration.


## Version 10.0.0 RC81 — Migration Safety and Print Reliability

- Removed stale patch references whose Python modules were not included in the release package.
- Kept all available historical patches in their original execution order.
- Added an idempotent RC81 repair patch.
- Replaced the hard-coded Receiving Note template ID with dynamic default-template resolution.
- Re-applied the approved Hotel Undertaking print format and default signature/stamp settings.
- Added release validation checks for versions, patches, JSON, Python, JavaScript, and fixed template identifiers.

## Version 5.0.1
Smart Kitchen & Warehouse: stock balances, controlled stock posting, production workflow, packaging tracking, and quality gates.


## WAFD ONE v5.9.0 — Financial Intelligence
- Actual project profitability and per-meal economics.
- Invoice totals, outstanding receivables, and ageing buckets.
- Cost and revenue variance against estimates.
- Approval locks for posted costs and collected revenue.
- Automatic project financial refresh after financial transactions.
