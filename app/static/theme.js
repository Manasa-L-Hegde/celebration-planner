/* Apply a saved theme before first paint to avoid a colour flash. */
(function () {
  try {
    var saved = localStorage.getItem("theme");
    if (saved === "light" || saved === "dark") {
      document.documentElement.setAttribute("data-theme", saved);
    }
  } catch (err) { /* storage may be blocked; fall back to the system theme */ }
})();
