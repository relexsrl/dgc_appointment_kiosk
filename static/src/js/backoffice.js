/** @odoo-module **/

import {registry} from "@web/core/registry";
import {rpc} from "@web/core/network/rpc";

const serviceRegistry = registry.category("services");

const dgcTurnBusService = {
    dependencies: ["bus_service"],

    async start(env, {bus_service}) {
        // Fetch the area IDs assigned to the current operator
        let areaIds = [];
        try {
            const result = await rpc("/backoffice/api/my_area_ids", {});
            areaIds = result.area_ids || [];
        } catch {
            // If the call fails, no channels will be subscribed
        }

        // Subscribe to one bus channel per area
        for (const areaId of areaIds) {
            bus_service.addChannel("dgc_turn_area_" + areaId);
        }

        // Re-dispatch bus events as DOM CustomEvents so components can
        // subscribe without importing the bus service directly.
        bus_service.subscribe("dgc_turn_update", (payload) => {
            document.dispatchEvent(
                new CustomEvent("dgc_turn_update", {detail: payload})
            );
        });
    },
};

serviceRegistry.add("dgc_turn_bus", dgcTurnBusService);
