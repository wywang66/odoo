from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from odoo.addons.base.models.ir_mail_server import MailDeliveryException



class Dbb_CalibrationOverdue(models.Model):
    _name = 'dbb.maintenance.calibrationoverdue'
    _description = 'Digital BigBite Maintenance Scheduled Calibration Overdue'
   
    # equipment_sequence_id = fields.Many2one(comodel_name='maintenance.equipment', string ="Equipment") 
    # equipment_state = fields.Selection(related="equipment_sequence_id.state", readonly=True)
    # # appointment_id = fields.Many2one(comodel_name='hospital.appointment', string ="Appointment",domain=['|',('state','=','draft'),('priority','in', ('0','1', False))]) # prioriry is a selection in appointment.py, false : no data
    # reason = fields.Text(string="Reason for Reschedule", required = True, default = "e.g. This equipment was out of order ..")
    # date_rescheduled = fields.Date(string="Reschedule Calibartion Date")
    
    
    @api.model
    def default_get(self, fields):
        result = super(Dbb_CalibrationOverdue, self).default_get(fields)
        print("-------------context", self.env.context)
        print("-------------context", self.env.context.get('active_id')) 
        result['equipment_sequence_id'] = self.env.context.get('active_id')
        
        # result['date_rescheduled'] = fields.Date.today()
        return result
   
    equipment_sequence_id = fields.Many2one(comodel_name='maintenance.equipment', string ="Equipment", domain=[('state','=','calibration_overdue')]) 
    reason = fields.Text(string="Reason", required = True, default = "e.g. This equipment was out of order ..")
    # date_rescheduled = fields.Date(string="Reschedule Calibartion Date", default=fields.Date.today())
        
    def action_reschedule_calibration(self):
        eq_name = self.env['ir.config_parameter'].get_param(
            'om_hpspital.cancel_days' )
        return