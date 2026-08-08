/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";

export class AdventureAiSearchPanel extends Component {
    static template = "adventure_ai_retail.AiSearchPanel";
    static components = { Dialog };
    static props = {
        close: Function,
    };

    setup() {
        this.pos = usePos();
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            query: "",
            loading: false,
            error: "",
            assistantText: "",
            products: [],
            sessionId: null,
        });
    }

    async onSubmit(ev) {
        ev?.preventDefault?.();
        const query = (this.state.query || "").trim();
        if (!query || this.state.loading) {
            return;
        }
        this.state.loading = true;
        this.state.error = "";
        try {
            const result = await this.orm.call("adventure.ai.orchestrator", "run_turn", [], {
                message: query,
                session_id: this.state.sessionId || false,
                profile: "pos_retail",
                channel: "pos",
                context: { feature: "pos_retail" },
            });
            this.state.sessionId = result.session_id;
            this.state.assistantText = result.assistant_text || "";
            this.state.products = result.products || [];
            if (!this.state.products.length && !this.state.assistantText) {
                this.state.assistantText = _t("No products matched that request.");
            }
        } catch (error) {
            const message =
                error?.data?.message ||
                error?.message ||
                _t("AI search failed. Check connectivity and Adventure AI settings.");
            this.state.error = message;
            this.notification.add(message, { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }

    async onSelectProduct(product) {
        if (!product) {
            return;
        }
        try {
            if (!this.pos.getOrder?.() && !this.pos.get_order?.()) {
                this.pos.addNewOrder?.();
            }
            const tmpl =
                this.pos.models?.["product.template"]?.get?.(product.product_tmpl_id) ||
                this.pos.db?.get_product_by_id?.(product.product_id) ||
                null;

            // Prefer template from POS data store when available.
            let productTmpl = tmpl;
            if (!productTmpl && this.pos.models?.["product.product"]) {
                const variant = this.pos.models["product.product"].get(product.product_id);
                productTmpl = variant?.product_tmpl_id || variant;
            }
            if (!productTmpl && this.pos.models?.["product.template"]) {
                productTmpl = this.pos.models["product.template"].get(product.product_tmpl_id);
            }

            if (productTmpl) {
                await this.pos.addLineToCurrentOrder({
                    product_tmpl_id: productTmpl,
                    qty: 1,
                });
            } else {
                // Fallback: pass ids if the POS data layer accepts raw ids.
                await this.pos.addLineToCurrentOrder({
                    product_tmpl_id: product.product_tmpl_id,
                    product_id: product.product_id,
                    qty: 1,
                });
            }
            this.notification.add(_t("Added to order: ") + product.name, { type: "success" });
        } catch (error) {
            const message =
                error?.data?.message ||
                error?.message ||
                _t("Could not add the product to the order.");
            this.notification.add(message, { type: "danger" });
        }
    }

    onClose() {
        this.props.close();
    }
}
