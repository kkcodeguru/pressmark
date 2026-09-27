(function () {
  document.querySelectorAll("form[data-confirm], form[data-pending]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      var message = form.getAttribute("data-confirm");
      if (message && !window.confirm(message)) {
        event.preventDefault();
        return;
      }
      var pending = form.getAttribute("data-pending");
      if (!pending) {
        return;
      }
      var button = event.submitter || form.querySelector("button[type=submit]");
      if (!button) {
        return;
      }
      if (button.name) {
        var hidden = document.createElement("input");
        hidden.type = "hidden";
        hidden.name = button.name;
        hidden.value = button.value;
        form.appendChild(hidden);
      }
      button.disabled = true;
      button.textContent = pending;
      form.setAttribute("aria-busy", "true");
    });
  });
})();
