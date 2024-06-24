from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class CalibrationOverdue(models.Model):
    _name = 'elw.calibration.overdue'
    _inherit = ['mail.thread',
                'mail.activity.mixin',
                ]  # add a chatter
    _description = 'Redo calibration after calibration is overdue'
    _order = 'id desc, name desc'  # Move the newest record to the top

    @api.returns('self')
    def _default_stage(self):
        return self.env['elw.calibration.stage'].search([], limit=1)

    name = fields.Char(string='Ref#', default='New', copy=False, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, ondelete='cascade')
    archive = fields.Boolean(default=False)
    calibration_id = fields.Many2one(comodel_name='elw.maintenance.calibration', string="Calibration Ref#")
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment name', required=True, store=True, ondelete='cascade')
    request_date = fields.Date('Request Date', tracking=True, store=True, related='calibration_id.request_date',
                               readonly=True, help="Original date requested for calibration")
    owner_user_id = fields.Many2one('res.users', string='Created by User', ondelete='cascade')
    category_id = fields.Many2one('maintenance.equipment.category', string='Category', store=True, readonly=True, ondelete='cascade')
    calibration_due_date = fields.Date(string="Original Calibration Due Date", tracking=True, store=True, readonly=True)
    priority = fields.Selection([('0', 'Very Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High')], string='Priority', store=True, default='3')
    maintenance_team_id = fields.Many2one('maintenance.team', string='Team', required=True, store=True, readonly=False,
                                          check_company=True, ondelete='cascade')
    repeat_interval = fields.Integer(string='Repeat Every', default=3, readonly=True,store=True)
    repeat_unit = fields.Selection([
        ('day', 'Days'),
        ('week', 'Weeks'),
        ('month', 'Months'),
        ('year', 'Years'),
    ], default='month', store=True)
    is_calibration_overdue = fields.Boolean(string="Is Calibration Overdue", store=True)
    calibration_completion_date = fields.Date(string='Calibration Completion Date', store=True, help="Date of the calibration is done.")
    technician_doing_calibration_id = fields.Many2one('res.users', string='Technician Doing Calibration', store=True, ondelete='cascade')
    stage_id = fields.Many2one('elw.calibration.stage', string='Stage', ondelete='restrict', tracking=True,
                               group_expand='_read_group_stage_ids', default=_default_stage, copy=False)
    ori_stage_id = fields.Many2one('elw.calibration.stage', string='Original Status', ondelete='restrict', tracking=True, readonly=True, copy=False)
    done = fields.Boolean(related='stage_id.done', store=True)
    description = fields.Html('Description')
    instruction_type = fields.Selection([
        ('pdf', 'PDF'), ('google_slide', 'Google Slide'), ('text', 'Text')],
        string="Instruction", default="text",
    )
    instruction_pdf = fields.Binary('PDF')
    instruction_google_slide = fields.Char('Google Slide', help="Paste the url of your Google Slide. Make sure the access to the document is public.")
    instruction_text = fields.Html('Text')
    reason_for_overdue = fields.Html(string="Reason for Overdue", related='calibration_id.reason_for_overdue')

    @api.constrains('calibration_completion_date')  # execute when clicking the 'save'
    def check_calibration_completion_date(self):
        for rec in self:
            if rec.calibration_completion_date:  # has data?
                if rec.calibration_completion_date > fields.Date.today():
                    raise UserError(_("Calibration completion date cannot be after today !"))

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """ Read group customization in order to display all the stages in the
            kanban view, even if they are empty
        """
        stage_ids = stages._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

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

    def action_see_calibration(self):
        return {
            'name': _('Calibration Overdue'),
            'res_model': 'elw.maintenance.calibration',
            'res_id': self.calibration_id.id,  # open the corresponding form
            # 'domain': [('id', '=', self.alert_ids.ids)],
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            # 'view_mode': 'tree,form',
            'target': 'current',
        }

    @api.depends('stage_id')
    def action_doing_calibration(self):
        for rec in self:
            if rec.stage_id.id == 1:
                rec.stage_id = 2
            else:
                raise UserError(_("You cannot change to 'In Progress' if this equipment is not in 'Pending Calibration' state"))

    @api.depends('stage_id')
    def action_passed_calibration(self):
        for rec in self:
            if rec.stage_id.id == 2:
                rec.stage_id = 3
                self.archive = True
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': (_("Calibration passed!")),
                        'type': 'rainbow_man',
                    }
                }
            else:
                raise UserError(_("You cannot change to 'Passed' if this equipment is not in 'In Progress' state"))

    @api.depends('stage_id')
    def action_failed_calibration(self):
        for rec in self:
            if rec.stage_id.id == 2:
                rec.stage_id = 4
            else:
                raise UserError(_("You cannot change to 'Failed' if this equipment is not in 'In Progress' state"))
