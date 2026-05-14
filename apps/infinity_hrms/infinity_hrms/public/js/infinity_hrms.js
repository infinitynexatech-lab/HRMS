// Infinity HRMS — client-side brand finalization.
//
// Loaded into Desk and Web via hooks.py. Runs on every page load.

(function () {
  "use strict";

  const BRAND = "Infinity HRMS";

  // 1. Set window title BEFORE Frappe's default flashes.
  //    Frappe sets document.title from app_title in hooks, but on slow
  //    networks the index.html ships with <title>Frappe</title> first.
  //    Rewriting it here closes that window.
  function setTitle() {
    const current = document.title || "";
    if (!current || /^Frappe(\s|$)/i.test(current) || current === "Loading...") {
      document.title = BRAND;
    } else if (!current.includes(BRAND)) {
      // Append brand if Frappe set its own page title (e.g. "Employee List")
      document.title = `${current} | ${BRAND}`;
    }
  }

  setTitle();

  // Re-apply on Frappe's route change (Desk is a SPA — title gets reset).
  if (window.frappe && frappe.router) {
    frappe.router.on("change", setTitle);
  }

  // Re-apply on history changes for the website portal too.
  window.addEventListener("popstate", setTitle);
})();
