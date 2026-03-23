/** @odoo-module **/

import { registry } from "@web/core/registry";
import { CharField } from "@web/views/fields/char/char_field";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

/**
 * Custom widget for token fields that adds a "Regenerate" button
 * that works reactively via RPC without full page reload.
 */
export class DgcTokenField extends CharField {
    static template = "dgc_appointment_kiosk.TokenField";

    setup() {
        super.setup();
        this.notification = useService("notification");
    }

    async onRegenerate() {
        const fieldName = this.props.name;
        // Determine method based on field name
        const methodName = fieldName === "dgc_kiosk_token" 
            ? "action_regenerate_kiosk_token" 
            : "action_regenerate_display_token";
        
        try {
            const newToken = await rpc(`/web/dataset/call_kw/res.config.settings/${methodName}`, {
                model: "res.config.settings",
                method: methodName,
                args: [[]],
                kwargs: {},
            });
            
            if (newToken) {
                // This is the magic part: it updates the form record reactively
                await this.props.record.update({ [fieldName]: newToken });
                this.notification.add("Token regenerado con éxito", {
                    type: "success",
                });
            }
        } catch (error) {
            this.notification.add("Error al regenerar el token", {
                type: "danger",
            });
        }
    }
}

// Register the widget
registry.category("fields").add("dgc_token_regenerator", {
    ...registry.category("fields").get("char"),
    component: DgcTokenField,
});
