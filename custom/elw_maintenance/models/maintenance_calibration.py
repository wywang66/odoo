# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from markupsafe import Markup
import datetime


class CalibrationStage(models.Model):
    """ Model for case stages. This models the main stages of a Calibration Request management flow. """
    _name = 'elw.calibration.stage'
    _description = 'Define calibration stage'
    _order = 'sequence, id'

    name = fields.Char('Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=20)
    done = fields.Boolean('Request Done', default=False)


class MaintenanceCalibration(models.Model):
    _name = 'elw.maintenance.calibration'
    _description = 'Perform calibration on selected equipment'
    _inherit = ['mail.thread',
                'mail.activity.mixin',
                ]  # add a chatter
    _order = 'id desc, name desc'  # Move the newest record to the top

    def _get_default_team_id(self):
        MT = self.env['maintenance.team']
        team = MT.search([('company_id', '=', self.env.company.id)], limit=1)
        if not team:
            team = MT.search([], limit=1)
        return team.id

    @api.returns('self')
    def _default_stage(self):
        return self.env['elw.calibration.stage'].search([], limit=1)

    name = fields.Char(string='Ref#', default='New', copy=False, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company, ondelete='cascade')
    archive = fields.Boolean(default=False, store=True, help="Set archive to true to hide the calibration request without deleting it.")
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment name', required=True, store=True, ondelete='cascade')
    request_date = fields.Date('Request Date', tracking=True, store=True, default=fields.Date.context_today, help="Date requested for calibration")
    owner_user_id = fields.Many2one('res.users', string='Created by User', default=lambda s: s.env.uid, ondelete='cascade')
    category_id = fields.Many2one('maintenance.equipment.category', related='equipment_id.category_id', string='Category', store=True, readonly=True,
                                  ondelete='cascade')
    sending_email_notification_days_ahead = fields.Integer(string="Send a Mail Notification ", default=10, required=True, store=False)
    calibration_due_date = fields.Date(string="Calibration Due Date", readonly=True, tracking=True, store=True)
    send_email_date = fields.Date(string="Send Email Notification From", readonly=True, store=True)
    priority = fields.Selection([('0', 'Very Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High')], string='Priority', store=True)
    color = fields.Integer('Color Index')
    maintenance_team_id = fields.Many2one('maintenance.team', string='Team', required=True, default=_get_default_team_id,
                                          compute='_compute_maintenance_team_id', store=True, readonly=False, check_company=True, ondelete='cascade')
    repeat_interval = fields.Integer(string='Repeat Every', default=3, store=True)
    repeat_unit = fields.Selection([
        ('day', 'Days'),
        ('week', 'Weeks'),
        ('month', 'Months'),
        ('year', 'Years'),
    ], default='month', store=True)
    is_calibration_overdue = fields.Boolean(string="Is Calibration Overdue", store=True)
    calibration_completion_date = fields.Date(string='Calibration Completion Date', store=True, help="Date of the calibration is done.")
    technician_doing_calibration_id = fields.Many2one('res.users', string='Technician Doing Calibration', store=True,
                                                      ondelete='cascade')
    stage_id = fields.Many2one('elw.calibration.stage', string='Status', ondelete='restrict', tracking=True, group_expand='_read_group_stage_ids',
                               default=_default_stage, copy=False)
    done = fields.Boolean(related='stage_id.done', store=True)
    description = fields.Html('Description')
    instruction_type = fields.Selection([
        ('pdf', 'PDF'), ('google_slide', 'Google Slide'), ('text', 'Text')],
        string="Instruction", default="text"
    )
    instruction_pdf = fields.Binary('PDF')
    instruction_google_slide = fields.Char('Google Slide', help="Paste the url of your Google Slide. Make sure the access to the document is public.")
    instruction_text = fields.Html('Text')
    reason_for_overdue = fields.Html(string="Reason for Overdue")
    duplicate_id = fields.Many2one('elw.maintenance.calibration', string="Next Calibration Ref#", store=True)
    original_id = fields.Many2one('elw.maintenance.calibration', string="Original Ref#", store=True)

    @api.onchange('calibration_due_date')
    def _onchange_priority(self):
        self.ensure_one()
        if (self.calibration_due_date - fields.Date.today()).days <= 3:
            self.priority = '3'

    @api.onchange('calibration_due_date')
    def _onchange_is_calibration_overdue(self):
        self.ensure_one()
        if self.calibration_due_date and self.calibration_due_date < fields.Date.today():
            self.is_calibration_overdue = True
            self.priority = '3'
            # print('rec.calibration_due_date', rec.stage_id, rec.is_calibration_overdue)
        else:
            self.is_calibration_overdue = False

    @api.onchange('repeat_interval', 'repeat_unit')
    def _onchange_calibration_due_date(self):
        self.ensure_one()
        if self.repeat_interval and self.repeat_unit:
            self.calibration_due_date = self.request_date
            self.calibration_due_date += relativedelta(**{f"{self.repeat_unit}s": self.repeat_interval})
        else:
            raise UserError(_("Failed to get Calibration Due Date"))

    @api.constrains('calibration_completion_date')  # execute when clicking the 'save'
    def check_calibration_completion_date(self):
        for rec in self:
            if rec.calibration_completion_date:  # has data?
                if rec.calibration_completion_date > fields.Date.today():
                    raise UserError(_("Calibration completion date cannot be after today !"))

    @api.onchange('sending_email_notification_days_ahead', 'calibration_due_date')
    def _onchange_send_email_date(self):
        if self.calibration_due_date:
            self.send_email_date = self.calibration_due_date - timedelta(
                days=self.sending_email_notification_days_ahead)
            if self.send_email_date <= fields.Date.today():
                self.send_email_date = fields.Date.today()
        else:
            raise ValidationError(_("No calibration due date to derive the send email date!"))

    # below is call by elw_email_template_data.xml
    @api.model
    def get_email_to(self):
        user_group = self.env.ref("maintenance.group_equipment_manager")
        email_list = [
            usr.partner_id.email for usr in user_group.users if usr.partner_id.email]
        # print("---------------", email_list) #--------------- ['admin@yourcompany.example.com', 'taknetwendy@gmail.com']
        return ",".join(email_list)

    # send a email now by clicking the btn
    def action_send_notification_email_now(self):
        template = self.env.ref('elw_maintenance.elw_calibration_email_template')
        try:
            template.send_mail(self.id, force_send=True)
        except MailDeliveryException as e:
            raise ValidationError(_("Sending mail error: ", e))

    # send a scheduled email. stop sending if done = True
    @api.depends('send_email_date', 'done')
    def action_send_email_on_scheduled_date(self):
        # from elw_email_template_data.xml <record id="elw_calibration_email_template" model="mail.template">
        template = self.env.ref('elw_maintenance.elw_calibration_email_template')
        records_of_send_email_today = self.env['elw.maintenance.calibration'].search(
            [('send_email_date', '<=', fields.Date.today()), ('archive', '!=', True), ('done', '!=', True)])
        # print("++++++++++++++", records_of_send_email_today)
        for record in records_of_send_email_today:
            if record.send_email_date <= fields.Date.today() and not record.done:
                try:
                    template.send_mail(record.id, force_send=True)
                except MailDeliveryException as e:
                    raise ValidationError(_("Sending mail error: ", e))

    def unlink(self):
        self.ensure_one()
        if self.stage_id != 1:
            raise UserError(_("You cannot delete record that is not in 'To Do' state"))
        return super(MaintenanceCalibration, self).unlink()

    # below is inherit method from model to avoid warning not override use @api.model_create_multi
    @api.model_create_multi
    def create(self, data_list):
        for vals in data_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('maintenance.calibration.sequence')
            # print("Success ............", vals)
        return super(MaintenanceCalibration, self).create(vals)

    # #  no decorator needed

    def write(self, vals):
        # print("write Success ............", self.name, vals.get('name'))
        if not vals.get('name') and self.name == "New":
            vals['name'] = self.env['ir.sequence'].next_by_code('maintenance.calibration.sequence')
            # print("write Success 2 ............", vals.get('name'))
        return super(MaintenanceCalibration, self).write(vals)

    def archive_calibration_request(self):
        self.write({'archive': True})

    def reset_calibration_request(self):
        """ Reinsert the calibration request into the calibration pipe in the first stage"""
        first_stage_obj = self.env['elw.calibration.stage'].search([], order="sequence asc", limit=1)
        # self.write({'active': True, 'stage_id': first_stage_obj.id})
        self.write({'archive': False, 'stage_id': first_stage_obj.id})

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """ Read group customization in order to display all the stages in the
            kanban view, even if they are empty
        """
        stage_ids = stages._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    @api.depends('stage_id')
    def action_doing_calibration(self):
        self.ensure_one()
        if self.stage_id.id == 1:
            self.stage_id = 2
        else:
            raise UserError(_("You cannot change to 'In Progress' if this equipment is not in 'Pending Calibration' state"))

    @api.depends('stage_id')
    def action_passed_calibration(self):
        self.ensure_one()
        if self.stage_id.id == 2:
            self.stage_id = 3
            self.duplicate_id = self.copy({
                'request_date': fields.Date.today() + timedelta(days=1),
                'calibration_due_date': self.calibration_due_date - self.request_date + fields.Date.today() + timedelta(days=1),
                'technician_doing_calibration_id': False,
                'calibration_completion_date': False,
            })
            if self.duplicate_id:
                self.archive = True
                # archived the original cali record too
                if self.original_id:
                    self.original_id.archive = True
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': (_("Next calibration request %s is created. Please check if all fields are correct", self.duplicate_id.name)),
                        'type': 'rainbow_man',
                    }
                }
            else:
                raise ValidationError(_("Failed to create next calibration request for equipment %s", self.equipment_id.name))
        else:
            raise UserError(_("You cannot change to 'Passed' if this equipment is not in 'In Progress' state"))

    @api.depends('stage_id')
    def action_failed_calibration(self):
        self.ensure_one()
        if self.stage_id.id == 2:
            self.stage_id = 4
            # duplicate a record for redo this failed calibration
            self.duplicate_id = self.copy({
                'technician_doing_calibration_id': False,
                'calibration_completion_date': False,
                'original_id': self.id,
            })
        else:
            raise UserError(_("You cannot change to 'Failed' if this equipment is not in 'In Progress' state"))

    # @api.depends('stage_id')
    # def action_reschedule_calibration_overdue(self):
    #     self.ensure_one()
    #     # current_data = self.env['elw.maintenance.calibration'].browse(self.id).copy()
    #     # print('current_data', current_data) #elw.maintenance.calibration(2,)
    #     # current_data = self.env['elw.maintenance.calibration'].search_read([('id', '=', self.id)])
    #     data = self.env['elw.maintenance.calibration'].browse(self.id).read(
    #         ['name', 'company_id', 'equipment_id', 'request_date', 'owner_user_id', 'category_id',
    #          'calibration_due_date', 'priority', 'maintenance_team_id', 'repeat_interval', 'repeat_unit',
    #          'technician_doing_calibration_id', 'stage_id', 'done', 'description', 'instruction_type', 'instruction_pdf',
    #          'instruction_google_slide', 'instruction_text',
    #          # 'reason_for_overdue',
    #          ])
    #     data = data[0]
    #     for key, value in data.items():
    #         if isinstance(value, tuple):
    #             data[key] = value[0]
    #
    #     # Remove the first 2 key-value pair 'id':1, 'name': 'ECxxxxx'
    #     keys_to_remove = list(data.keys())[:2]
    #     for key in keys_to_remove:
    #         data.pop(key)
    #     data['calibration_id'] = self.id
    #     value = data.pop('stage_id')
    #     data['ori_stage_id'] = value
    #     data['priority'] = '3'
    #     data['technician_doing_calibration_id'] = False
    #     data['calibration_completion_date'] = False
    #     # print(data)
    #     self.overdue_id = self.env['elw.calibration.overdue'].create(data)

    def action_see_next_calibration_request(self):
        return {
            'name': _('Next Calibration Request'),
            'res_model': 'elw.maintenance.calibration',
            'res_id': self.duplicate_id.id,  # open the corresponding form
            # 'domain': [('id', '=', self.alert_ids.ids)],
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'current',
        }

    def action_see_original_calibration_request(self):
        return {
            'name': _('Original Calibration Request'),
            'res_model': 'elw.maintenance.calibration',
            'res_id': self.original_id.id,  # open the corresponding form
            # 'domain': [('id', '=', self.alert_ids.ids)],
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'current',
        }

class MaintenanceTeam(models.Model):
    _inherit = 'maintenance.team'
    _description = 'Inheritance of Maintenance Teams'

    calibration_request_ids = fields.One2many('elw.maintenance.calibration', 'maintenance_team_id', copy=False)
    todo_calibration_request_ids = fields.One2many('elw.maintenance.calibration', string="Calibration Requests", copy=False,
                                                   compute='_compute_todo_calibration_requests')
    todo_calibration_request_count = fields.Integer(string="Number of Calibration Requests", compute='_compute_todo_calibration_requests')
    todo_calibration_high_priority_count = fields.Integer(string="Number of High Priority", compute='_compute_todo_calibration_requests')
    todo_calibration_fail_count = fields.Integer(string="Number of Failed Calibration", compute='_compute_todo_calibration_requests')

    @api.depends('request_ids.stage_id.done')
    def _compute_todo_calibration_requests(self):
        for team in self:
            team.todo_calibration_request_ids = self.env['elw.maintenance.calibration'].search(
                [('maintenance_team_id', '=', team.id), ('stage_id.done', '=', False), ('archive', '=', False)])
            # print('team.todo_calibration_request_ids', team.todo_calibration_request_ids) #elw.maintenance.calibration(3, 2, 1)
            data = self.env['elw.maintenance.calibration']._read_group(
                [('maintenance_team_id', '=', team.id), ('stage_id.done', '=', False), ('archive', '=', False)],
                ['done','priority', 'stage_id'],
                ['__count']
            )
            # print('data', data) # data [(False, False, elw.calibration.stage(1,), 1), (False, False, elw.calibration.stage(2,), 1), (False, False, elw.calibration.stage(5,), 1)]
            team.todo_calibration_request_count = sum(count for (_, _, _, count) in data)
            team.todo_calibration_high_priority_count = sum(count for (_, priority, _, count) in data if priority == '3')
            team.todo_calibration_fail_count = sum(count for (_, _, stage_id, count) in data if stage_id.id == 4)
            # print(team.todo_calibration_request_count,team.todo_calibration_high_priority_count,team.todo_calibration_fail_count)