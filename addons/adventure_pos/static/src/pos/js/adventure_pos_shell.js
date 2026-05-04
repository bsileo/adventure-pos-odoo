/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";
import { Navbar } from "@point_of_sale/app/components/navbar/navbar";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import {
    getAdventurePOSMode,
    getAdventurePOSModes,
    getAdventurePOSState,
    setAdventurePOSMode,
} from "./mode_registry";

patch(Navbar.prototype, {
    setup() {
        super.setup();
        this.adventurePOSState = useState(getAdventurePOSState(this.pos));
    },

    get adventurePOSModes() {
        return getAdventurePOSModes(this.env, this.pos);
    },

    get adventurePOSActiveModeKey() {
        return this.adventurePOSState.activeMode || "sale";
    },

    onClickAdventurePOSMode(mode) {
        if (!setAdventurePOSMode(this.pos, mode.key)) {
            return;
        }
        if (mode.key === "sale") {
            this.onClickRegister();
            return;
        }
        if (!this.pos.getOrder()) {
            this.pos.addNewOrder();
        }
        if (this.pos.router.state.current !== "ProductScreen") {
            this.pos.navigate("ProductScreen", { orderUuid: this.pos.getOrder()?.uuid });
        }
    },
});

patch(ProductScreen.prototype, {
    setup() {
        super.setup();
        this.adventurePOSState = useState(getAdventurePOSState(this.pos));
    },

    get adventurePOSActiveMode() {
        const key = this.adventurePOSState.activeMode || "sale";
        return getAdventurePOSMode(key) || getAdventurePOSMode("sale");
    },

    get adventurePOSActiveComponent() {
        return this.adventurePOSActiveMode?.component || null;
    },

    get adventurePOSShowsSaleWorkspace() {
        return !this.adventurePOSActiveComponent;
    },
});
