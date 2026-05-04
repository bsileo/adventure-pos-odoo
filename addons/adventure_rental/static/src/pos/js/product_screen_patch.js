/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { RentalConfigPopup } from "./rental_popup";

patch(ProductScreen.prototype, {
    setup() {
        super.setup();
        this.dialog = useService("dialog");
    },

    async addProductToOrder(product) {
        if (product?.is_rental) {
            this.dialog.add(RentalConfigPopup, { product });
            return;
        }
        return super.addProductToOrder(product);
    },
});
