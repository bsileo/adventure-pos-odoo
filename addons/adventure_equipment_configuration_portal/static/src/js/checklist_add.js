/** Simple checklist add: type free-text or pick matching equipment. */
(function () {
  function initChecklistAdd(root) {
    var form = root.querySelector("[data-checklist-add]");
    if (!form) {
      return;
    }
    var input = form.querySelector("[data-checklist-input]");
    var assetField = form.querySelector("[data-checklist-asset]");
    var listEl = form.querySelector("[data-checklist-suggestions]");
    var suggestUrl = form.getAttribute("data-suggest-url");
    if (!input || !assetField || !listEl || !suggestUrl) {
      return;
    }

    var activeIndex = -1;
    var results = [];
    var timer = null;

    function closeSuggestions() {
      listEl.classList.remove("is-open");
      listEl.innerHTML = "";
      activeIndex = -1;
      results = [];
    }

    function setAsset(id, label) {
      assetField.value = id || "";
      if (label) {
        input.value = label;
      }
      closeSuggestions();
    }

    function render() {
      listEl.innerHTML = "";
      if (!results.length) {
        closeSuggestions();
        return;
      }
      results.forEach(function (item, index) {
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className =
          "o_equip_checklist_suggestion" + (index === activeIndex ? " is-active" : "");
        btn.setAttribute("data-asset-id", String(item.id));
        btn.innerHTML =
          "<div>" +
          escapeHtml(item.label) +
          "</div>" +
          (item.category
            ? '<div class="o_equip_checklist_suggestion_meta">' +
              escapeHtml(item.category) +
              "</div>"
            : "");
        btn.addEventListener("mousedown", function (ev) {
          ev.preventDefault();
          setAsset(item.id, item.label);
        });
        listEl.appendChild(btn);
      });
      listEl.classList.add("is-open");
    }

    function escapeHtml(value) {
      return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    function fetchSuggestions(query) {
      if (!query) {
        closeSuggestions();
        return;
      }
      fetch(suggestUrl + "?q=" + encodeURIComponent(query), {
        credentials: "same-origin",
        headers: { Accept: "application/json" },
      })
        .then(function (response) {
          return response.json();
        })
        .then(function (payload) {
          results = (payload && payload.results) || [];
          activeIndex = results.length ? 0 : -1;
          render();
        })
        .catch(function () {
          closeSuggestions();
        });
    }

    input.addEventListener("input", function () {
      assetField.value = "";
      var query = input.value.trim();
      if (timer) {
        window.clearTimeout(timer);
      }
      timer = window.setTimeout(function () {
        fetchSuggestions(query);
      }, 180);
    });

    input.addEventListener("keydown", function (ev) {
      if (!listEl.classList.contains("is-open") || !results.length) {
        return;
      }
      if (ev.key === "ArrowDown") {
        ev.preventDefault();
        activeIndex = (activeIndex + 1) % results.length;
        render();
      } else if (ev.key === "ArrowUp") {
        ev.preventDefault();
        activeIndex = (activeIndex - 1 + results.length) % results.length;
        render();
      } else if (ev.key === "Enter" && activeIndex >= 0 && results[activeIndex]) {
        // Keep Enter as submit; if a suggestion is highlighted, bind it first.
        setAsset(results[activeIndex].id, results[activeIndex].label);
      } else if (ev.key === "Escape") {
        closeSuggestions();
      }
    });

    form.addEventListener("submit", function () {
      // Free-text add when no equipment picked.
      if (!assetField.value) {
        assetField.value = "";
      }
    });

    document.addEventListener("click", function (ev) {
      if (!form.contains(ev.target)) {
        closeSuggestions();
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-equip-checklist]").forEach(initChecklistAdd);
  });
})();
