/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { formatRentalLine } from "./rental_data";

export class RentalConfigPopup extends Component {
    static template = "adventure_rental.RentalConfigPopup";
    static components = { Dialog };
    static props = {
        product: { type: Object, optional: true },
        close: Function,
        getPayload: { type: Function, optional: true },
    };

    setup() {
        this.pos = usePos();
        const currentOrder = this.pos.getOrder?.() || this.pos.get_order?.();
        const partner = currentOrder?.getPartner?.() || currentOrder?.get_partner?.();
        this.state = useState({
            customer: partner?.name || "",
            pickupDate: this.defaultDateTime(1),
            returnDate: this.defaultDateTime(49),
            quantity: 1,
            preferences: "",
            deposit: 200,
            availability: "available",
            error: "",
        });
    }

    defaultDateTime(offsetHours) {
        const date = new Date(Date.now() + offsetHours * 60 * 60 * 1000);
        date.setMinutes(0, 0, 0);
        return date.toISOString().slice(0, 16);
    }

    checkAvailability() {
        this.state.availability = this.isValidRange() ? "available" : "overdue";
        this.state.error = this.isValidRange() ? "" : _t("Return must be after pickup.");
    }

    isValidRange() {
        return new Date(this.state.returnDate) > new Date(this.state.pickupDate);
    }

    async confirm() {
        this.checkAvailability();
        if (this.state.error) {
            return;
        }
        const payload = {
            customer: this.state.customer,
            pickupDate: this.state.pickupDate,
            returnDate: this.state.returnDate,
            quantity: Number(this.state.quantity || 1),
            preferences: this.state.preferences,
            deposit: Number(this.state.deposit || 0),
            availability: this.state.availability,
        };
        const order = this.pos.getOrder?.() || this.pos.get_order?.();
        if (order) {
            if (!this.props.product) {
                this.state.error = _t("Select a rental product before configuring a rental.");
                return;
            }
            await this.pos.addLineToCurrentOrder(
                {
                    product_tmpl_id: this.props.product,
                    qty: payload.quantity,
                },
                {
                    rental: payload,
                }
            );
            const line = order.getLastOrderline?.() || order.lines?.at(-1);
            if (line?.set_customer_note) {
                line.set_customer_note(formatRentalLine(payload));
            } else if (line) {
                line.customer_note = formatRentalLine(payload);
            }
        }
        this.props.getPayload?.({ confirmed: true, payload });
        this.props.close();
    }

    cancel() {
        this.props.getPayload?.({ confirmed: false });
        this.props.close();
    }
}
