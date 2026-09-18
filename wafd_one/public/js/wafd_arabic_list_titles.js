(function () {
  const titles = {
    'WAFD Catering Project': 'المشاريع',
    'WAFD Daily Meal Plan': 'الخطط اليومية',
    'WAFD Production Batch': 'دفعات الإنتاج',
    'WAFD Packaging Record': 'سجلات التغليف',
    'WAFD Loading Record': 'سجلات التحميل',
    'WAFD Quality Inspection': 'فحوص الجودة',
    'WAFD CCP Check': 'فحوص نقاط التحكم الحرجة',
    'WAFD Delivery Trip': 'عمليات التوصيل',
    'WAFD Iftar Project': 'مشاريع إفطار الصائم',
    'WAFD Iftar Daily Operation': 'التشغيل اليومي لإفطار الصائم',
    'WAFD Iftar Supervisor Plan': 'خطط مشرفي إفطار الصائم',
    'WAFD Iftar Supervisor Daily Report': 'تقارير مشرفي إفطار الصائم'
  };
  function localize() {
    if (!window.frappe || !frappe.get_route) return;
    const route = frappe.get_route();
    if (route[0] !== 'List' || !titles[route[1]]) return;
    const title = titles[route[1]];
    document.querySelectorAll('.page-title .title-text, .page-head .title-text').forEach(el => {
      el.textContent = title;
      el.setAttribute('title', title);
    });
  }
  function schedule() { window.setTimeout(localize, 40); window.setTimeout(localize, 250); }
  if (window.frappe && frappe.router && frappe.router.on) frappe.router.on('change', schedule);
  document.addEventListener('DOMContentLoaded', schedule);
})();
