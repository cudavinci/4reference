/* Sidebar focus-mode toggle
   Adds a small circular button (bottom-left) that hides/shows the left
   navigation sidebar. State is persisted in localStorage so it survives
   page navigation.                                                        */

(function () {
  const STORAGE_KEY = "navHidden";
  const HIDDEN_CLASS = "nav-hidden";

  // Icons: panel-left-close / panel-left-open (simple SVG paths)
  const ICON_HIDE =
    '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">' +
    '<path d="M3 4h18v2H3V4zm0 7h11v2H3v-2zm0 7h18v2H3v-2z"/>' +
    '<path d="M17 8l4 4-4 4V8z"/>' +
    "</svg>";
  const ICON_SHOW =
    '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">' +
    '<path d="M3 4h18v2H3V4zm0 7h11v2H3v-2zm0 7h18v2H3v-2z"/>' +
    '<path d="M21 8l-4 4 4 4V8z"/>' +
    "</svg>";

  function applyState(hidden) {
    if (hidden) {
      document.body.classList.add(HIDDEN_CLASS);
    } else {
      document.body.classList.remove(HIDDEN_CLASS);
    }
  }

  function createButton() {
    const btn = document.createElement("button");
    btn.id = "sidebar-toggle";
    btn.title = "Toggle navigation sidebar";
    btn.setAttribute("aria-label", "Toggle navigation sidebar");

    function syncIcon() {
      const hidden = document.body.classList.contains(HIDDEN_CLASS);
      btn.innerHTML = hidden ? ICON_SHOW : ICON_HIDE;
    }

    btn.addEventListener("click", function () {
      const nowHidden = !document.body.classList.contains(HIDDEN_CLASS);
      applyState(nowHidden);
      localStorage.setItem(STORAGE_KEY, nowHidden ? "1" : "0");
      syncIcon();
    });

    document.body.appendChild(btn);
    syncIcon();
  }

  function init() {
    // Restore persisted state before first paint to avoid flicker
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "1") {
      applyState(true);
    }
    createButton();
  }

  // MkDocs Material with navigation.instant uses a custom page-load event
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Re-attach button after instant navigation swaps the DOM
  document.addEventListener("DOMContentSwitch", function () {
    if (!document.getElementById("sidebar-toggle")) {
      createButton();
    }
  });
})();
