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
    archive = fields.Boolean(default=False,
                             help="Set archive to true to hide the calibration request without deleting it.")
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