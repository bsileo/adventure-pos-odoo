/** @odoo-module **/

import { Component, onMounted, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { rentalStateClass, sampleActiveRentals, sampleReservations } from "./rental_data";

class RentalWorkflowScreen extends Component {
    setup() {
        this.pos = usePos();
    }

    back() {
        this.pos.navigate("ProductScreen");
    }

    stateClass(state) {
        return rentalStateClass(state);
    }
}

export class PickupScreen extends RentalWorkflowScreen {
    static template = "adventure_rental.PickupScreen";

    setup() {
        super.setup();
        this.scanInput = useRef("scanInput");
        this.state = useState({
            reservations: sampleReservations,
            selectedId: sampleReservations[0]?.id,
            scannedAsset: "",
            status: "reserved",
            scanBuffer: "",
        });
        onMounted(() => this.focusScanner());
    }

    get selected() {
        return this.state.reservations.find((reservation) => reservation.id === this.state.selectedId);
    }

    select(reservation) {
        this.state.selectedId = reservation.id;
        this.state.status = reservation.state;
        this.state.scannedAsset = "";
        setTimeout(() => this.focusScanner());
    }

    onScan(ev) {
        this.state.scannedAsset = ev.target.value;
        this.state.status = ev.target.value ? "assigned" : this.selected?.state || "reserved";
    }

    focusScanner() {
        this.scanInput.el?.focus();
    }

    completeCheckout() {
        this.state.status = "checked_out";
    }
}

export class ReturnScreen extends RentalWorkflowScreen {
    static template = "adventure_rental.ReturnScreen";

    setup() {
        super.setup();
        this.scanInput = useRef("scanInput");
        this.state = useState({
            rentals: sampleActiveRentals,
            selectedId: sampleActiveRentals[0]?.id,
            scannedAsset: "",
            condition: "returned",
            route: "available",
        });
        onMounted(() => this.focusScanner());
    }

    get selected() {
        return this.state.rentals.find((rental) => rental.id === this.state.selectedId);
    }

    get feesTotal() {
        return (this.selected?.fees || []).reduce((sum, fee) => sum + fee.amount, 0);
    }

    select(rental) {
        this.state.selectedId = rental.id;
        this.state.scannedAsset = "";
        this.state.condition = rental.state === "overdue" ? "overdue" : "returned";
        setTimeout(() => this.focusScanner());
    }

    onScan(ev) {
        this.state.scannedAsset = ev.target.value;
    }

    closeRental() {
        this.state.condition = this.state.route === "repair" ? "damaged" : "returned";
    }

    focusScanner() {
        this.scanInput.el?.focus();
    }
}

registry.category("pos_pages").add("AdventureRentalPickupScreen", {
    name: "AdventureRentalPickupScreen",
    component: PickupScreen,
    route: `/pos/ui/${odoo.pos_config_id}/rental-pickup`,
    params: {},
});

registry.category("pos_pages").add("AdventureRentalReturnScreen", {
    name: "AdventureRentalReturnScreen",
    component: ReturnScreen,
    route: `/pos/ui/${odoo.pos_config_id}/rental-return`,
    params: {},
});
