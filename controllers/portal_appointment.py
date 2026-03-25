import logging
import re

from odoo import http
from odoo.http import request
from odoo.exceptions import UserError

from odoo.addons.appointment.controllers.appointment import AppointmentController

_logger = logging.getLogger(__name__)


class DgcPortalAppointmentController(AppointmentController):
    """Override the appointment form submission to inject DNI/CUIT-based
    partner resolution for DGC area appointment types.

    Flow:
    1. Extract ``citizen_dni`` and ``doc_type`` from POST kwargs.
    2. Validate the DNI/CUIT server-side via Turn._validate_dni().
    3. Call Turn._find_or_create_partner() to locate or create a partner
       with the correct VAT, avoiding duplicates.
    4. Store the resolved partner so _get_customer_partner() returns it
       instead of creating a new one from email alone.
    5. Delegate to super() — standard flow creates the calendar.event,
       which triggers _create_dgc_turns_from_appointments() in
       calendar_event.py, producing the DGC turn with citizen_dni
       populated from partner.vat.
    """

    @http.route()
    def appointment_form_submit(
        self,
        appointment_type_id,
        datetime_str,
        duration_str,
        name,
        email,
        staff_user_id=None,
        available_resource_ids=None,
        asked_capacity=1,
        guest_emails_str=None,
        **kwargs,
    ):
        # Pop DGC-specific fields so they don't leak into super()
        citizen_dni = kwargs.pop("citizen_dni", "").strip()
        doc_type = kwargs.pop("doc_type", "dni").strip()

        if citizen_dni:
            # Resolve appointment type to check if it's a DGC area
            appointment_type = self._get_dgc_appointment_type(appointment_type_id, **kwargs)

            if appointment_type and appointment_type.is_dgc_area:
                raw_dni = re.sub(r"\D", "", citizen_dni)

                # Server-side validation
                Turn = request.env["dgc.appointment.turn"].sudo()
                if not Turn._validate_dni(raw_dni):
                    raise UserError(
                        "DNI/CUIT inválido. DNI debe tener 7-8 dígitos, "
                        "CUIT debe tener 11 dígitos con checksum válido."
                    )

                # Normalize: extract base DNI from CUIT
                raw_dni = Turn._normalize_dni(raw_dni)

                # Find or create partner by VAT
                result = Turn._find_or_create_partner(raw_dni, name, email)
                partner = request.env["res.partner"].sudo().browse(result["partner_id"])

                # Ensure partner.vat is set (critical for turn creation hook)
                if partner and not partner.vat:
                    partner.vat = raw_dni

                # Sync partner email/name so super()'s email comparison
                # doesn't discard our partner and create a duplicate.
                if partner and email:
                    partner.email = email
                if partner and name:
                    partner.name = name

                # Store resolved partner for _get_customer_partner override
                # Use request object instead of self (controller is a singleton)
                request._dgc_customer_partner = partner

        return super().appointment_form_submit(
            appointment_type_id,
            datetime_str,
            duration_str,
            name,
            email,
            staff_user_id=staff_user_id,
            available_resource_ids=available_resource_ids,
            asked_capacity=asked_capacity,
            guest_emails_str=guest_emails_str,
            **kwargs,
        )

    def _get_customer_partner(self):
        """Return the DNI-resolved partner if available (one-shot)."""
        partner = getattr(request, "_dgc_customer_partner", None)
        if partner:
            request._dgc_customer_partner = None
            return partner
        return super()._get_customer_partner()

    def _get_dgc_appointment_type(self, appointment_type_id, **_kwargs):
        """Fetch the appointment type by ID.

        Returns the appointment.type record or None if not found.
        """
        try:
            return request.env["appointment.type"].sudo().browse(
                int(appointment_type_id)
            ).exists()
        except (ValueError, TypeError):
            return None
