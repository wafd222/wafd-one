// WAFD Meal Plan is an internal operational record from v8.4 onward.
// Users plan from WAFD Daily Meal Plan; this DocType remains for compatibility
// with production, loading, delivery, invoicing and historical records.
frappe.ui.form.on("WAFD Meal Plan", {
    onload(frm) {
        if (frm.is_new() && !frappe.route_options?.allow_internal_meal_plan) {
            frappe.msgprint({
                title: __("Use Daily Meal Planning"),
                indicator: "blue",
                message: __("Individual meal records are generated automatically from WAFD Daily Meal Plan. Open the project and use Generate Daily Plans.")
            });
        }
    },
    refresh(frm) {
        if (frm.is_new() && !frappe.route_options?.allow_internal_meal_plan) {
            frm.disable_save();
            frm.add_custom_button(__("Open Daily Meal Plans"), () => {
                const filters = frm.doc.project ? { project: frm.doc.project } : {};
                frappe.set_route("List", "WAFD Daily Meal Plan", filters);
            });
        }
    }
});

frappe.ui.form.on("WAFD Meal Plan", {
    refresh(frm) {
        configure_hotel_query(frm);
        if (frm.doc.project) load_project_context(frm, false);
        if (frm.is_new()) return;
        frm.add_custom_button(__("Create Production Batch"), () => {
            frappe.call({
                method: "wafd_one.wafd_one.doctype.wafd_meal_plan.wafd_meal_plan.create_production_batch",
                args: { meal_plan_name: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating production batch..."),
                callback(r) {
                    if (r.message) frappe.set_route("Form", "WAFD Production Batch", r.message.name);
                }
            });
        }, __("Operations"));
    },

    setup(frm) {
        configure_hotel_query(frm);
    },

    project(frm) {
        frm.set_value("hotel", null);
        load_project_context(frm, true);
    },

    recipe(frm) {
        if (!frm.doc.recipe) return;
        frappe.db.get_value("WAFD Recipe", frm.doc.recipe, ["cost_per_portion", "recipe_name"]).then(r => {
            if (!r.message) return;
            frm.set_value("estimated_unit_cost", r.message.cost_per_portion || 0);
            if (!frm.doc.menu_name) frm.set_value("menu_name", r.message.recipe_name);
        });
    },

    quantity: calculate_totals,
    unit_price: calculate_totals,
    estimated_unit_cost: calculate_totals
});

function configure_hotel_query(frm) {
    frm.set_query("hotel", () => {
        const hotels = frm.__project_hotels || [];
        return hotels.length ? { filters: { name: ["in", hotels] } } : {};
    });
}

function load_project_context(frm, auto_select) {
    frm.__project_hotels = [];
    configure_hotel_query(frm);
    if (!frm.doc.project) return;

    frappe.db.get_doc("WAFD Catering Project", frm.doc.project).then(project => {
        const hotels = (project.hotels || []).map(row => row.hotel).filter(Boolean);
        if (project.primary_hotel && !hotels.includes(project.primary_hotel)) {
            hotels.unshift(project.primary_hotel);
        }
        frm.__project_hotels = [...new Set(hotels)];
        configure_hotel_query(frm);

        if (auto_select && !frm.doc.hotel && frm.__project_hotels.length === 1) {
            frm.set_value("hotel", frm.__project_hotels[0]);
        }
    });
}

function calculate_totals(frm) {
    const value = flt(frm.doc.quantity) * flt(frm.doc.unit_price);
    const cost = flt(frm.doc.quantity) * flt(frm.doc.estimated_unit_cost);
    frm.set_value("total_value", value);
    frm.set_value("estimated_cost", cost);
    frm.set_value("estimated_profit", value - cost);
    frm.set_value("estimated_margin_percent", value ? ((value - cost) / value) * 100 : 0);
}
