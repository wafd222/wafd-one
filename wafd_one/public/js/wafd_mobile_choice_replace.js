(function () {
  "use strict";
  const mobileOrTouch = window.matchMedia("(pointer: coarse)").matches || (navigator.maxTouchPoints || 0) > 0;
  if (!mobileOrTouch) return;

  // On mobile, replacing a Link/autocomplete choice should not require deleting
  // the previous text character by character. Selecting the current value means
  // the next typed character replaces it, while the normal dropdown still works.
  $(document)
    .off("focusin.wafdChoiceReplace")
    .on("focusin.wafdChoiceReplace", ".frappe-control[data-fieldtype='Link'] input, .frappe-control[data-fieldtype='Dynamic Link'] input, .awesomplete > input", function () {
      const input = this;
      if (!input.value || input.readOnly || input.disabled) return;
      window.setTimeout(() => {
        try { input.setSelectionRange(0, input.value.length); } catch (error) { input.select(); }
      }, 0);
    });
})();
