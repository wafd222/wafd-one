const fs = require("fs");
const vm = require("vm");

const source = fs.readFileSync(
  "wafd_one/wafd_one/page/wafd_iftar_supervisor/wafd_iftar_supervisor.js",
  "utf8"
);

let makePageCalls = 0;
let rendered = "";
const root = {
  appendTo() { return this; },
  html(value) { if (value !== undefined) rendered = String(value); return this; },
  off() { return this; },
  on() { return this; },
};

function dollar(value) {
  if (typeof value === "string") return root;
  return { addClass() { return this; } };
}

const report = {
  name: "IFTAR-SREP-00001",
  project: "WAFD-IFTAR-00001",
  project_title: "المسجد النبوي الشريف",
  distribution_site: "التوسعة الشرقية",
  contracting_entity: "شؤون الحرمين",
  operation_date: "2026-09-19",
  planned_meals: 500,
  received_meals: 500,
  table_owners: [],
  assistants: [],
};

const context = {
  console,
  $: dollar,
  __: (value) => value,
  FileReader: function FileReader() {},
  frappe: {
    pages: { "wafd-iftar-supervisor": {} },
    ui: {
      make_app_page() { makePageCalls += 1; return { body: {} }; },
      Dialog: function Dialog() {},
    },
    utils: { escape_html: (value) => String(value) },
    call() {
      return Promise.resolve({
        message: {
          user: "supervisor@example.com",
          full_name: "مشرف الاختبار",
          reports: [report],
          plans: [],
        },
      });
    },
    throw(message) { throw new Error(message); },
    show_alert() {},
    msgprint() {},
  },
};

vm.createContext(context);
vm.runInContext(source, context);

const page = context.frappe.pages["wafd-iftar-supervisor"];
if (makePageCalls !== 0) throw new Error("Page loader executed while assets were evaluated");
if (typeof page.on_page_load !== "function" || typeof page.on_page_show !== "function") {
  throw new Error("Supervisor Page handlers were not registered");
}

const wrapper = {};
page.on_page_load(wrapper);
page.on_page_load(wrapper);
if (makePageCalls !== 1) throw new Error("Supervisor Page initializer is not idempotent");
if (!wrapper.__ifsup) throw new Error("Supervisor Page container was not initialized");

page.on_page_show(wrapper);
setTimeout(() => {
  if (!rendered.includes("تكليفاتي اليومية")) throw new Error("Supervisor task heading was not rendered");
  if (!rendered.includes("المسجد النبوي الشريف")) throw new Error("Assigned supervisor report was not rendered");
  console.log("RC330 supervisor page bootstrap and assigned-task rendering passed");
}, 0);
