from odoo import models, fields, api, _
from datetime import date
import datetime
from odoo.exceptions import ValidationError
from dateutil import relativedelta


class QualityCheckWizard(models.TransientModel):
    _name = 'quality.check.wizard'
    _description = 'ELW Quality Check Wizard'

    # default_get fun must be ahead of fields
    # default_get return the existing all fields' values.
    # and assign or override to the fields
    @api.model
    def default_get(self, fields):
        result = super(CancelAppointmentWizard, self).default_get(fields)
        # print ("default_get", fields) #default_get ['appointment_id', 'reason', 'date_cancel']
        # print ("default_get", result) #default_get {}
        # print("-------------context", self.env.context)
        # -------------context {'lang': 'en_US', 'tz': 'Asia/Singapore', 'uid': 2, 'allowed_company_ids': [1],
        # 'params': {'id': 1, 'cids': 1, 'menu_id': 109, 'action': 170, 'model': 'hospital.appointment', 'view_type': 'form'},
        # 'default_appointment_id': 2, 'active_model': 'hospital.appointment', 'active_id': 2, 'active_ids': [2]}
        # print("-------------context", self.env.context.get('active_id'))
        result['appointment_id'] = self.env.context.get('active_id')
        result['date_cancel'] = datetime.date.today()
        return result

    # '|', is or cond. wo it, and cond
    appointment_id = fields.Many2one(comodel_name='hospital.appointment', string="Appointment", domain=[
        ('state', 'in', ('draft', 'in_consultation'))])  # show on draft and in_consulation
    # appointment_id = fields.Many2one(comodel_name='hospital.appointment', string ="Appointment",domain=['|',('state','=','draft'),('priority','in', ('0','1', False))]) # prioriry is a selection in appointment.py, false : no data
    reason = fields.Text(string="Reason", default="unaviable")
    date_cancel = fields.Date(string="Cancellation Date")

    # validate first before cancelation
    def action_cancel_appointment(self):
        if self.appointment_id.booking_date == fields.Date.today():
            print("appointment booking ....", self.appointment_id.booking_date)
            raise ValidationError(
                _("Sorry, cancelation is disallowed on the same date of booking or appointment"))  # _ is for transition purpose
        # self.appointment_id.appointment_time == fields.Date.today() this is datetime cannot compared to date

        cancel_day = self.env['ir.config_parameter'].get_param(
            'om_hpspital.cancel_days')
        print("----------", cancel_day, self.env['ir.config_parameter'])
        allowed_days = self.appointment_id.booking_date + relativedelta.relativedelta(days=int(cancel_day))
        # print("----------", cancel_day, allowed_days, date.today()) #----------- 6 2024-01-10 2024-03-21
        if allowed_days > date.today():
            raise ValidationError(
                _("Sorry, cancelation is disallowed as booking date is closer "))  # _ is for transition purpose
        self.appointment_id.state = "cancel"
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
