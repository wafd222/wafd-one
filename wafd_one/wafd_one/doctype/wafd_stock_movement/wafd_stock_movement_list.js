frappe.listview_settings["WAFD Stock Movement"] = {
  onload(listview) {
    const has = (listview.filter_area && listview.filter_area.get && listview.filter_area.get().some(f => f[1] === "is_pre_go_live_test"));
    if (!has) listview.filter_area.add([["WAFD Stock Movement", "is_pre_go_live_test", "=", 0]]);
  }
};
