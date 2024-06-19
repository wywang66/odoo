from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from odoo.addons.base.models.ir_mail_server import MailDeliveryException


class CalibrationOverdue(models.Model):
    _name = 'elw.calibration.overdue'
    _inherit = ['mail.thread',
                'mail.activity.mixin',
                ]  # add a chatter
    _description = 'Redo calibration after calibration is overdue'
    _order = 'id desc, name desc'  # Move the newest record to the top

    name = fields.Char(string='Ref#', default='New', copy=False, readonly=True)
    archive = fields.Boolean(default=False)
    calibration_id = fields.Many2one(comodel_name='elw.maintenance.calibration', string ="Calibration Ref#")
    # equipment_state = fields.Selection(related="equipment_sequence_id.state", readonly=True)
    # # appointment_id = fields.Many2one(comodel_name='hospital.appointment', string ="Appointment",domain=['|',('state','=','draft'),('priority','in', ('0','1', False))]) # prioriry is a selection in appointment.py, false : no data
    original_calibration_due_date = fields.Date(string="Original Calibration Due Date", related='calibration_id.calibration_due_date')

    description = fields.Html('Description')
    instruction_type = fields.Selection([
        ('pdf', 'PDF'), ('google_slide', 'Google Slide'), ('text', 'Text')],
        string="Instruction", default="text"
    )
    instruction_pdf = fields.Binary('PDF')
    instruction_google_slide = fields.Char('Google Slide',
                                           help="Paste the url of your Google Slide. Make sure the access to the document is public.")
    instruction_text = fields.Html('Text')
    reason_for_overdue = fields.Html(string="Reason for Overdue")

    @api.model_create_multi
    def create(self, data_list):
        for vals in data_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('calibration.overdue.sequence')
            # print("Success ............", vals)
        return super(CalibrationOverdue, self).create(vals)

    # #  no decorator needed

    def write(self, vals):
        # print("write Success ............", self.name, vals.get('name'))
        if not vals.get('name') and self.name == "New":
            vals['name'] = self.env['ir.sequence'].next_by_code('calibration.overdue.sequence')
            # print("write Success 2 ............", vals.get('name'))
        return super(CalibrationOverdue, self).write(vals)