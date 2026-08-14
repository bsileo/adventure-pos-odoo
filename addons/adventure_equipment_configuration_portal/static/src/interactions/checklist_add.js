/** Checklist add: free-text or pick matching owned equipment (autocomplete). */
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class EquipmentChecklistAdd extends Interaction {
    static selector = "[data-equip-checklist]";
    static selectorHas = "[data-checklist-add]";

    dynamicContent = {
        "[data-checklist-input]": {
            "t-on-input": this.onInput,
            "t-on-keydown": this.onKeydown,
        },
        "[data-checklist-add]": {
            "t-on-submit": this.onSubmit,
        },
        _document: {
            "t-on-click": this.onDocumentClick,
        },
    };

    setup() {
        this.form = this.el.querySelector("[data-checklist-add]");
        this.input = this.form?.querySelector("[data-checklist-input]");
        this.assetField = this.form?.querySelector("[data-checklist-asset]");
        this.listEl = this.form?.querySelector("[data-checklist-suggestions]");
        this.suggestUrl = this.form?.getAttribute("data-suggest-url");
        this.activeIndex = -1;
        this.results = [];
        this.timer = null;
        this.emptyHint = false;
    }

    destroy() {
        if (this.timer) {
            window.clearTimeout(this.timer);
        }
    }

    closeSuggestions() {
        if (!this.listEl) {
            return;
        }
        this.listEl.classList.remove("is-open");
        this.listEl.innerHTML = "";
        this.activeIndex = -1;
        this.results = [];
        this.emptyHint = false;
    }

    setAsset(id, label) {
        if (!this.assetField || !this.input) {
            return;
        }
        this.assetField.value = id || "";
        if (label) {
            this.input.value = label;
        }
        this.closeSuggestions();
    }

    escapeHtml(value) {
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    render() {
        if (!this.listEl) {
            return;
        }
        this.listEl.innerHTML = "";
        if (!this.results.length) {
            if (this.emptyHint) {
                const empty = document.createElement("div");
                empty.className = "o_equip_checklist_suggestion_empty text-muted";
                empty.textContent =
                    "No matching equipment — press Add to keep this as a text item.";
                this.listEl.appendChild(empty);
                this.listEl.classList.add("is-open");
            } else {
                this.closeSuggestions();
            }
            return;
        }
        this.results.forEach((item, index) => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className =
                "o_equip_checklist_suggestion" +
                (index === this.activeIndex ? " is-active" : "");
            btn.setAttribute("data-asset-id", String(item.id));
            const hint = item.match_hint || item.category || "";
            btn.innerHTML =
                "<div>" +
                this.escapeHtml(item.label) +
                "</div>" +
                (hint
                    ? '<div class="o_equip_checklist_suggestion_meta">' +
                      this.escapeHtml(hint) +
                      "</div>"
                    : "");
            btn.addEventListener("mousedown", (ev) => {
                ev.preventDefault();
                this.setAsset(item.id, item.label);
            });
            this.listEl.appendChild(btn);
        });
        this.listEl.classList.add("is-open");
    }

    fetchSuggestions(query) {
        if (!this.suggestUrl) {
            return;
        }
        if (!query) {
            this.closeSuggestions();
            return;
        }
        fetch(this.suggestUrl + "?q=" + encodeURIComponent(query), {
            credentials: "same-origin",
            headers: { Accept: "application/json" },
        })
            .then((response) => response.json())
            .then((payload) => {
                this.results = (payload && payload.results) || [];
                this.activeIndex = this.results.length ? 0 : -1;
                this.emptyHint = !this.results.length && query.trim().length >= 2;
                this.render();
            })
            .catch(() => {
                this.closeSuggestions();
            });
    }

    onInput() {
        if (!this.input || !this.assetField) {
            return;
        }
        this.assetField.value = "";
        const query = this.input.value.trim();
        if (this.timer) {
            window.clearTimeout(this.timer);
        }
        this.timer = window.setTimeout(() => {
            this.fetchSuggestions(query);
        }, 180);
    }

    onKeydown(ev) {
        if (!this.listEl || !this.listEl.classList.contains("is-open")) {
            return;
        }
        if (!this.results.length) {
            if (ev.key === "Escape") {
                this.closeSuggestions();
            }
            return;
        }
        if (ev.key === "ArrowDown") {
            ev.preventDefault();
            this.activeIndex = (this.activeIndex + 1) % this.results.length;
            this.render();
        } else if (ev.key === "ArrowUp") {
            ev.preventDefault();
            this.activeIndex =
                (this.activeIndex - 1 + this.results.length) % this.results.length;
            this.render();
        } else if (
            ev.key === "Enter" &&
            this.activeIndex >= 0 &&
            this.results[this.activeIndex]
        ) {
            this.setAsset(
                this.results[this.activeIndex].id,
                this.results[this.activeIndex].label
            );
        } else if (ev.key === "Escape") {
            this.closeSuggestions();
        }
    }

    onSubmit() {
        if (this.assetField && !this.assetField.value) {
            this.assetField.value = "";
        }
    }

    onDocumentClick(ev) {
        if (this.form && !this.form.contains(ev.target)) {
            this.closeSuggestions();
        }
    }
}

registry
    .category("public.interactions")
    .add(
        "adventure_equipment_configuration_portal.checklist_add",
        EquipmentChecklistAdd
    );
