/** @odoo-module **/

import { registerAdventurePOSMode } from "@adventure_pos/pos/js/mode_registry";
import { RentalMode } from "./rental_mode";
import { PickupScreen, ReturnScreen } from "../rental_screens";

registerAdventurePOSMode({
    key: "rental",
    label: "Rental",
    icon: "fa-calendar",
    sequence: 20,
    component: RentalMode,
    isAvailable: () => true,
});

registerAdventurePOSMode({
    key: "pickup",
    label: "Pickup",
    icon: "fa-sign-out",
    sequence: 30,
    component: PickupScreen,
    isAvailable: () => true,
});

registerAdventurePOSMode({
    key: "return",
    label: "Return",
    icon: "fa-sign-in",
    sequence: 40,
    component: ReturnScreen,
    isAvailable: () => true,
});
