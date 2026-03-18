/** @odoo-module **/

import {registry} from "@web/core/registry";

const serviceRegistry = registry.category("services");

const dgcTurnBusService = {
    dependencies: ["bus_service", "action"],

    start(env, {bus_service, action}) {
        // Subscribe to turn updates for operator's areas
        bus_service.subscribe("dgc_turn_update", (payload) => {
            // Reload list view when a turn is updated
            action.doAction({type: "ir.actions.client", tag: "reload"});
        });

        bus_service.addChannel("dgc_turn_updates");
    },
};

serviceRegistry.add("dgc_turn_bus", dgcTurnBusService);
