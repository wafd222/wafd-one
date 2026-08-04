const WAFD_DEFAULT_MEALS = "إفطار / Breakfast\nغداء / Lunch\nعشاء / Dinner";
frappe.ui.form.on("WAFD Hotel Undertaking", {
  setup(frm) {
    frm.set_query("hotel", () => ({ query: "wafd_one.wafd_one.doctype.wafd_hotel.wafd_hotel.hotel_link_query" }));
  },
  onload(frm) {
    if (frm.is_new() && !frm.doc.meal_types) frm.set_value("meal_types", WAFD_DEFAULT_MEALS);
    if (frm.is_new() && !frm.doc.company_logo) frm.set_value("company_logo", "/assets/wafd_one/images/wafd-almadinah-official.png");
  },
  before_save(frm) { if (!frm.doc.meal_types) frm.set_value("meal_types", WAFD_DEFAULT_MEALS); },
  refresh(frm) {
    frm.toggle_display("project", !!frm.doc.project);
    if (frm.is_new()) return;
    if (frm.doc.docstatus === 0) frm.add_custom_button(__("تحديث البيانات المرتبطة"), () => frappe.call({method:"wafd_one.wafd_one.doctype.wafd_hotel_undertaking.wafd_hotel_undertaking.load_linked_data",args:{name:frm.doc.name},freeze:true,callback:()=>frm.reload_doc()}), __("الإجراءات"));
    if (frm.doc.docstatus !== 2) frm.add_custom_button(__("اعتماد وإصدار PDF"), () => frappe.call({method:"wafd_one.wafd_one.doctype.wafd_hotel_undertaking.wafd_hotel_undertaking.approve_and_generate_pdf",args:{name:frm.doc.name},freeze:true,freeze_message:__("جارٍ اعتماد التعهد وإصدار ملف PDF..."),callback(r){if(r.message?.file_url){frm.reload_doc();window.open(r.message.file_url,"_blank");}}})).addClass("btn-primary");
    frm.add_custom_button(__("معاينة التعهد"), async () => { const r = await frappe.call({method:"wafd_one.document_studio.get_default_template", args:{reference_doctype:frm.doctype}}); if(!r.message){frappe.msgprint(__("لا يوجد قالب تعهد مفعل")); return;} const q=new URLSearchParams({template_name:r.message,doctype:frm.doctype,docname:frm.doc.name}); window.open(`/api/method/wafd_one.document_studio.download_pdf?${q.toString()}`,"_blank"); }, __("الإجراءات"));
  },
  project(frm){ if(!frm.doc.project)return; frappe.db.get_doc("WAFD Catering Project",frm.doc.project).then(p=>frm.set_value({contract:frm.doc.contract||p.contract,mission:frm.doc.mission||p.mission,hotel:frm.doc.hotel||p.primary_hotel,beneficiary_count:frm.doc.beneficiary_count||p.beneficiary_count,start_date:frm.doc.start_date||p.start_date,end_date:frm.doc.end_date||p.end_date})); },
});
