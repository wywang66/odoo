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
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 related='calibration_id.company_id', ondelete='cascade')
    archive = fields.Boolean(default=False)
    calibration_id = fields.Many2one(comodel_name='elw.maintenance.calibration', string="Calibration Ref#")
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment name',
                                   related='calibration_id.equipment_id', required=True, store=True,
                                   ondelete='cascade')
    request_date = fields.Date('Request Date', tracking=True, store=True, related='calibration_id.request_date',
                               help="Date requested for calibration")
    owner_user_id = fields.Many2one('res.users', string='Created by User', related='calibration_id.owner_user_id',
                                    ondelete='cascade')
    category_id = fields.Many2one('maintenance.equipment.category', related='calibration_id.category_id',
                                  string='Category', store=True, readonly=True, ondelete='cascade')

    calibration_due_date = fields.Date(string="Calibration Due Date", related='calibration_id.calibration_due_date',
                                       tracking=True, store=True)
    priority = fields.Selection([('0', 'Very Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High')], string='Priority',
                                related='calibration_id.priority', store=True)
    close_date = fields.Date('Close Date', help="Date the calibration was finished.", store=True)
    maintenance_team_id = fields.Many2one('maintenance.team', string='Team', required=True,
                                          store=True, readonly=False, related='calibration_id.maintenance_team_id',
                                          check_company=True, ondelete='cascade')
    repeat_interval = fields.Integer(string='Repeat Every', default=3, related='calibration_id.repeat_interval',store=True)
    repeat_unit = fields.Selection([
        ('day', 'Days'),
        ('week', 'Weeks'),
        ('month', 'Months'),
        ('year', 'Years'),
    ], default='month', related='calibration_id.repeat_unit', store=True)
    is_calibration_overdue = fields.Boolean(string="Is Calibration Overdue", store=True)
    calibration_completion_date = fields.Date(string='Calibration Completion Date', required=True, store=True, default=fields.Date.context_today)
    technician_doing_calibration_id = fields.Many2one('res.users', string='Technician Doing Calibration', store=True,
                                                      ondelete='cascade')
    stage_id = fields.Many2one('elw.calibration.stage', string='Stage', ondelete='restrict', tracking=True,
                                copy=False)
    done = fields.Boolean(related='stage_id.done', store=True)
    description = fields.Html('Description')
    instruction_type = fields.Selection([
        ('pdf', 'PDF'), ('google_slide', 'Google Slide'), ('text', 'Text')],
        string="Instruction", default="text",
    )
    instruction_pdf = fields.Binary('PDF')
    instruction_google_slide = fields.Char('Google Slide',
                                           help="Paste the url of your Google Slide. Make sure the access to the document is public.")
    instruction_text = fields.Html('Text')
    reason_for_overdue = fields.Html(string="Reason for Overdue", related='calibration_id.reason_for_overdue')

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
