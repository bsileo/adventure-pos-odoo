/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { FormController } from "@web/views/form/form_controller";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

import { Component, useState, xml } from "@odoo/owl";

const PARTNER_KINDS = [
    { value: "person", label: _t("Person"), buttonLabel: _t("Person") },
    { value: "company", label: _t("Company"), buttonLabel: _t("Company") },
    { value: "ambiguous", label: _t("Ambiguous"), buttonLabel: _t("Ambiguous") },
];
const D360_IMPORT_BATCH_MODEL = "adventure.d360.customer.import.batch";
const D360_UPSERT_ACTION = "action_upsert_partners";
const D360_UPSERT_CHUNK_ACTION = "action_upsert_partners_chunk";
const D360_UPSERT_CHUNK_SIZE = 250;
const D360_PROGRESS_STYLE_ID = "o_d360_import_progress_style";
const D360_PROGRESS_BAR_ID = "o_d360_import_progress";

let d360ProgressBarUsers = 0;

function ensureD360ProgressStyle() {
    if (document.getElementById(D360_PROGRESS_STYLE_ID)) {
        return;
    }
    const style = document.createElement("style");
    style.id = D360_PROGRESS_STYLE_ID;
    style.textContent = `
        .o_d360_busy_cursor,
        .o_d360_busy_cursor * {
            cursor: progress !important;
        }

        .o_d360_import_progress {
            position: fixed;
            inset: 0 0 auto 0;
            height: 26px;
            z-index: 1100;
            pointer-events: none;
            background: rgba(13, 110, 253, 0.12);
            overflow: hidden;
            border-bottom: 1px solid rgba(13, 110, 253, 0.15);
        }

        .o_d360_import_progress_bar {
            width: 0%;
            height: 100%;
            background: linear-gradient(90deg, #0d6efd, #6ea8fe);
            box-shadow: 0 0 10px rgba(13, 110, 253, 0.2);
            transition: width 180ms ease-out;
        }

        .o_d360_import_progress_text {
            position: absolute;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0 12px;
            color: #052c65;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.01em;
            white-space: nowrap;
        }
    `;
    document.head.appendChild(style);
}

function ensureD360ProgressBar() {
    let progressBar = document.getElementById(D360_PROGRESS_BAR_ID);
    if (progressBar) {
        return progressBar;
    }
    progressBar = document.createElement("div");
    progressBar.id = D360_PROGRESS_BAR_ID;
    progressBar.className = "o_d360_import_progress";
    progressBar.setAttribute("role", "progressbar");
    progressBar.setAttribute("aria-valuemin", "0");
    progressBar.setAttribute("aria-valuemax", "100");
    progressBar.setAttribute("aria-valuenow", "0");
    progressBar.setAttribute("aria-valuetext", _t("Upserting partners"));
    progressBar.setAttribute("aria-hidden", "true");
    progressBar.hidden = true;

    const progressIndicator = document.createElement("div");
    progressIndicator.className = "o_d360_import_progress_bar";
    progressBar.appendChild(progressIndicator);

    const progressText = document.createElement("div");
    progressText.className = "o_d360_import_progress_text";
    progressText.textContent = _t("Preparing partner upsert...");
    progressBar.appendChild(progressText);

    document.body.appendChild(progressBar);
    return progressBar;
}

function showD360ProgressBar() {
    ensureD360ProgressStyle();
    const progressBar = ensureD360ProgressBar();
    d360ProgressBarUsers += 1;
    document.body.classList.add("o_d360_busy_cursor");
    progressBar.hidden = false;
    progressBar.setAttribute("aria-hidden", "false");
}

function updateD360ProgressBar(batchValues = {}) {
    const progressBar = ensureD360ProgressBar();
    const progressIndicator = progressBar.querySelector(".o_d360_import_progress_bar");
    const progressText = progressBar.querySelector(".o_d360_import_progress_text");
    const lineCount = batchValues.line_count || 0;
    const processedCount = batchValues.processed_count || 0;
    const failedCount = batchValues.failed_count || 0;
    const percent = Math.max(
        0,
        Math.min(
            100,
            Number.isFinite(batchValues.progress_percent)
                ? batchValues.progress_percent
                : lineCount
                  ? (processedCount * 100) / lineCount
                  : 0
        )
    );
    progressIndicator.style.width = `${percent}%`;
    progressText.textContent = `${Math.round(percent)}% - ${processedCount}/${lineCount} ${_t("rows processed")}${
        failedCount ? ` (${failedCount} ${_t("failed")})` : ""
    }`;
    progressBar.setAttribute("aria-valuenow", String(Math.round(percent)));
    progressBar.setAttribute("aria-valuetext", progressText.textContent);
}

function hideD360ProgressBar() {
    d360ProgressBarUsers = Math.max(0, d360ProgressBarUsers - 1);
    if (d360ProgressBarUsers) {
        return;
    }
    document.body.classList.remove("o_d360_busy_cursor");
    const progressBar = document.getElementById(D360_PROGRESS_BAR_ID);
    if (progressBar) {
        progressBar.hidden = true;
        progressBar.setAttribute("aria-hidden", "true");
        progressBar.setAttribute("aria-valuenow", "0");
        const progressIndicator = progressBar.querySelector(".o_d360_import_progress_bar");
        if (progressIndicator) {
            progressIndicator.style.width = "0%";
        }
        const progressText = progressBar.querySelector(".o_d360_import_progress_text");
        if (progressText) {
            progressText.textContent = _t("Preparing partner upsert...");
        }
    }
}

function isD360UpsertAction(controller, clickParams) {
    return (
        controller.props.resModel === D360_IMPORT_BATCH_MODEL &&
        clickParams.type === "object" &&
        clickParams.name === D360_UPSERT_ACTION
    );
}

export class D360PartnerKindActionsField extends Component {
    static template = xml`
        <div class="d-flex align-items-center gap-1 flex-wrap">
            <span class="badge text-bg-light">
                <t t-out="this.currentLabel"/>
            </span>
            <t t-foreach="this.availableActions" t-as="action" t-key="action.value">
                <button
                    type="button"
                    class="btn btn-secondary btn-sm"
                    t-att-class="action.value === 'ambiguous' ? 'btn btn-outline-secondary btn-sm' : 'btn btn-secondary btn-sm'"
                    t-att-disabled="this.isDisabled"
                    t-on-click="(ev) => this.onSetKind(ev, action.value)"
                >
                    <t t-out="action.buttonLabel"/>
                </button>
            </t>
        </div>
    `;
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            busy: false,
        });
    }

    get currentKind() {
        return this.props.record.data[this.props.name] || "ambiguous";
    }

    get currentLabel() {
        const current = PARTNER_KINDS.find((item) => item.value === this.currentKind);
        return current ? current.label : this.currentKind;
    }

    get availableActions() {
        return PARTNER_KINDS.filter((item) => item.value !== this.currentKind);
    }

    get isDisabled() {
        return (
            this.state.busy ||
            !this.props.record.resId ||
            this.props.record._parentRecord?.data?.state === "done"
        );
    }

    get list() {
        return this.props.record._parentRecord?.data?.line_ids || null;
    }

    async onSetKind(ev, partnerKind) {
        ev.preventDefault();
        ev.stopPropagation();
        if (this.isDisabled || partnerKind === this.currentKind) {
            return;
        }

        this.state.busy = true;
        try {
            const result = await this.orm.call(
                this.props.record.resModel,
                "action_set_partner_kind",
                [[this.props.record.resId], partnerKind],
                {
                    context: this.props.record.context,
                }
            );
            await this.props.record.load();
            const batchRecord = this.props.record._parentRecord;
            if (batchRecord && result?.batch_values) {
                batchRecord._applyValues(result.batch_values);
            }
        } catch (error) {
            this.notification.add(_t("Could not update the partner kind."), {
                type: "danger",
            });
            throw error;
        } finally {
            this.state.busy = false;
        }
    }
}

export const d360PartnerKindActionsField = {
    component: D360PartnerKindActionsField,
    supportedTypes: ["selection"],
};

registry.category("fields").add("d360_partner_kind_actions", d360PartnerKindActionsField);

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        this.notification = useService("notification");
        this.d360UpsertProgressVisible = false;
    },

    async beforeExecuteActionButton(clickParams) {
        const showProgress = isD360UpsertAction(this, clickParams);
        if (!showProgress) {
            return super.beforeExecuteActionButton(...arguments);
        }
        const record = this.model.root;
        const saved = await super.beforeExecuteActionButton(...arguments);
        if (saved === false) {
            return false;
        }
        showD360ProgressBar();
        updateD360ProgressBar(record.data);
        this.d360UpsertProgressVisible = true;
        try {
            let result;
            do {
                result = await this.orm.call(
                    D360_IMPORT_BATCH_MODEL,
                    D360_UPSERT_CHUNK_ACTION,
                    [[record.resId]],
                    {
                        context: record.context,
                        chunk_size: D360_UPSERT_CHUNK_SIZE,
                    }
                );
                if (result?.batch_values && this.model.root._applyValues) {
                    this.model.root._applyValues(result.batch_values);
                }
                updateD360ProgressBar(result?.batch_values || record.data);
            } while (!result?.done);

            await this.model.load();
            const batchValues = result?.batch_values || this.model.root.data;
            const failedCount = batchValues.failed_count || 0;
            const importedCount = batchValues.imported_count || 0;
            this.notification.add(
                failedCount
                    ? `${_t("Partner upsert finished")}: ${importedCount} ${_t("imported")}, ${failedCount} ${_t(
                          "failed"
                      )}. ${_t("Review failed rows for details.")}`
                    : `${_t("Partner upsert finished")}: ${importedCount} ${_t("imported")}.`,
                { type: failedCount ? "warning" : "success" }
            );
            return false;
        } finally {
            if (this.d360UpsertProgressVisible) {
                hideD360ProgressBar();
                this.d360UpsertProgressVisible = false;
            }
        }
    },

    async afterExecuteActionButton(clickParams) {
        if (isD360UpsertAction(this, clickParams)) {
            return;
        }
        return super.afterExecuteActionButton(...arguments);
    },
});
