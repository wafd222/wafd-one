const WAFD_DEFAULT_MEALS = "إفطار / Breakfast\nغداء / Lunch\nعشاء / Dinner";
frappe.ui.form.on("WAFD Hotel Undertaking", {
  onload(frm) {
    if (frm.is_new() && !frm.doc.meal_types) frm.set_value("meal_types", WAFD_DEFAULT_MEALS);
    if (frm.is_new() && !frm.doc.company_logo) frm.set_value("company_logo", "/assets/wafd_one/images/wafd-almadinah-official.png");
  },
  before_save(frm) { if (!frm.doc.meal_types) frm.set_value("meal_types", WAFD_DEFAULT_MEALS); },
  refresh(frm) {
    if (frm.is_new()) return;
    if (frm.doc.docstatus === 0) frm.add_custom_button(__("تحديث البيانات المرتبطة"), () => frappe.call({method:"wafd_one.wafd_one.doctype.wafd_hotel_undertaking.wafd_hotel_undertaking.load_linked_data",args:{name:frm.doc.name},freeze:true,callback:()=>frm.reload_doc()}), __("الإجراءات"));
    if (frm.doc.docstatus !== 2) frm.add_custom_button(__("اعتماد وإصدار PDF"), () => frappe.call({method:"wafd_one.wafd_one.doctype.wafd_hotel_undertaking.wafd_hotel_undertaking.approve_and_generate_pdf",args:{name:frm.doc.name},freeze:true,freeze_message:__("جارٍ اعتماد التعهد وإصدار ملف PDF..."),callback(r){if(r.message?.file_url){frm.reload_doc();window.open(r.message.file_url,"_blank");}}})).addClass("btn-primary");
    frm.add_custom_button(__("معاينة التعهد"), () => window.open(`/printview?doctype=${encodeURIComponent(frm.doctype)}&name=${encodeURIComponent(frm.doc.name)}&format=${encodeURIComponent("تعهد والتزام إعاشة — WAFD")}&no_letterhead=1`,"_blank"), __("الإجراءات"));
  },
  project(frm){ if(!frm.doc.project)return; frappe.db.get_doc("WAFD Catering Project",frm.doc.project).then(p=>frm.set_value({contract:frm.doc.contract||p.contract,mission:frm.doc.mission||p.mission,hotel:frm.doc.hotel||p.primary_hotel,beneficiary_count:frm.doc.beneficiary_count||p.beneficiary_count,start_date:frm.doc.start_date||p.start_date,end_date:frm.doc.end_date||p.end_date})); },
  hotel(frm){if(!frm.doc.hotel)return;frappe.db.get_value("WAFD Hotel",frm.doc.hotel,"hotel_name").then(r=>{if(r.message?.hotel_name)frm.set_value("supply_location",r.message.hotel_name);});}
});
