/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { RentalConfigPopup } from "../rental_popup";
import { sampleReservations } from "../rental_data";

export class RentalMode extends Component {
    static template = "adventure_rental.RentalMode";

    setup() {
        this.pos = usePos();
        this.dialog = useService("dialog");
    }

    get reservations() {
        return sampleReservations;
    }

    openRentalReservation() {
        const line = this.pos.getOrder()?.getSelectedOrderline?.() || this.pos.getOrder()?.getLastOrderline?.();
        const product = line?.product_id?.product_tmpl_id;
        this.dialog.add(RentalConfigPopup, { product });
    }
}
