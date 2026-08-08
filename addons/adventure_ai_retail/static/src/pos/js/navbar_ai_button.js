/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { Navbar } from "@point_of_sale/app/components/navbar/navbar";
import { AdventureAiSearchPanel } from "./ai_search_panel";

patch(Navbar.prototype, {
    setup() {
        super.setup(...arguments);
        this.adventureAiDialog = useService("dialog");
    },

    onClickAdventureAiSearch() {
        this.adventureAiDialog.add(AdventureAiSearchPanel, {});
    },
});
