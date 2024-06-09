# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from odoo.addons.base.models.ir_mail_server import MailDeliveryException


class CalibrationStage(models.Model):
    """ Model for case stages. This models the main stages of a Calibration Request management flow. """
    _name = 'elw.calibration.stage'
    _description = 'Calibration Stage'
    _order = 'sequence, id'

    name = fields.Char('Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=20)
    done = fields.Boolean('Request Done')


class MaintenanceCalibration(models.Model):
    _name = 'elw.maintenance.calibration'
    _description = 'Digital BigBite Scheduled Calibration'
    _order = 'id desc, name desc'  # Move the newest record to the top

    def _get_default_team_id(self):
        MT = self.env['maintenance.team']
        team = MT.search([('company_id', '=', self.env.company.id)], limit=1)
        if not team:
            team = MT.search([], limit=1)
        return team.id

    @api.returns('self')
    def _default_stage(self):
        return self.env['calibration.stage'].search([], limit=1)

    name = fields.Char(string='Ref#', default='New', copy=False, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company, ondelete='cascade')
    active = fields.Boolean(default=True)
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment name', required=True, store=True,
                                   ondelete='cascade')
    request_date = fields.Date('Request Date', tracking=True, default=fields.Date.context_today,
                               help="Date requested for calibration")
    owner_user_id = fields.Many2one('res.users', string='Created by User', default=lambda s: s.env.uid,
                                    ondelete='cascade')
    category_id = fields.Many2one('maintenance.equipment.category', related='equipment_id.category_id',
                                  string='Category', store=True, readonly=True, ondelete='cascade')
    sending_email_notification_days_ahead = fields.Integer(string="Send a Mail Notification ", default=10,
                                                           required=True, store=False)
    calibration_due_date = fields.Date(string="Calibration Due Date", store=True,
                                       compute='_compute_calibration_due_date')
    # calibration_date = fields.Date(string="Calibration Due Date", compute='_compute_calibration_date', tracking=True, store=True, required=True, default = datetime.today().date() )
    calibration_date = fields.Date(string="Calibration Due Date", tracking=True, store=True)
    send_email_date = fields.Date(string="Send Email Notification after", compute='_compute_send_email_date',
                                  tracking=True, store=True)

    priority = fields.Selection([('0', 'Very Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High')], string='Priority')
    color = fields.Integer('Color Index')
    close_date = fields.Date('Close Date', help="Date the calibration was finished. ")

    maintenance_team_id = fields.Many2one('maintenance.team', string='Team', required=True,
                                          default=_get_default_team_id,
                                          compute='_compute_maintenance_team_id', store=True, readonly=False,
                                          check_company=True, ondelete='cascade')
    repeat_interval = fields.Integer(string='Repeat Every', default=3)
    repeat_unit = fields.Selection([
        ('day', 'Days'),
        ('week', 'Weeks'),
        ('month', 'Months'),
        ('year', 'Years'),
    ], default='month')
    repeat_type = fields.Selection([
        ('forever', 'Forever'),
        ('until', 'Until'),
    ], default="forever", string="Until")
    repeat_until = fields.Date(string="End Date")

    def _compute_calibration_due_date(self):
        pass


    # send_email_date = fields.Date(string="Send Email Notification On", store=True)

    # is_calibration_done = fields.Boolean(string="Is Calibration Done", compute='action_done_calibration', required=True,
    #                                      default=False, store=True)
    # is_doing_calibration = fields.Boolean(string="Is Doing Calibration", default=False, store=False, compute='action_doing_calibration')
    calibration_completion_date = fields.Date(string='Calibration Completion Date', required=True, store=True,
                                              default=fields.Date.context_today)
    technician_doing_calibration_id = fields.Many2one('res.users', string='Technician Doing Calibration', store=True,
                                                      default=lambda self: self.env.uid, ondelete='cascade')
    # list sequence is same as xml's statusbar sequence

    stage_id = fields.Many2one('elw.calibration.stage', string='Stage', ondelete='restrict', tracking=True,
                               group_expand='_read_group_stage_ids', default=_default_stage, copy=False)
    done = fields.Boolean(related='stage_id.done')

    # state = fields.Selection([
    #     ('pending_calibration', 'Pending Calibration'),
    #     ('doing_calibration', 'Doing Calibration'),
    #     ('done_calibration', 'Done Calibration'),
    #     ('calibration_overdue', 'Calibration Overdue'),], default = "pending_calibration", string="Status", required = True, tracking=True)
    # is_calibration_overdue = fields.Boolean(string="Is Preventive Maintenance Overdue", default=False,
    #                                         compute='_compute_calibration_overdue', store=True)

    # reason_overdue = fields.Text(string="Reason for Overdue", required=True)

    # # override the active field. archieve if 'done_calibration'
    # active = fields.Boolean()

    # member_ids = fields.Many2many('hr.employee', string="Team Members from HR")
    # company_id = fields.Many2one('hr.employee',string="Company")

    # def name_get(self):
    #     result = []
    #     for vals in self:
    #         name = vals.name + ' ' + vals.category_id
    #         result.append(vals.id, name)
    #     return result

    # @api.constrains('calibration_interval')  # execute when clicking the 'save'
    # def check_calibration_interval(self):
    #     for rec in self:
    #         # print("----------", rec.calibration_interval)
    #         if rec.calibration_interval < -20:
    #             raise ValidationError(_("Calibration interval must be > 1 !"))

    # @api.constrains('calibration_completion_date')  # execute when clicking the 'save'
    # def check_calibration_completion_date(self):
    #     for rec in self:
    #         if rec.calibration_completion_date:  # has data?
    #             if rec.calibration_completion_date > fields.Date.today():
    #                 raise ValidationError(_("Calibration completion date cannot be after today !"))

    # @api.depends('calibration_interval', 'calibration_interval_by', 'is_calibration_required')
    # def _compute_calibration_date(self):
    #     for record in self:
    #         # # # get calibration_date based cali completion date
    #         # print(" --------------- ", record.calibration_completion_date)
    #         # if record.calibration_completion_date:
    #         #     self.check_calibration_completion_date()
    #         #     print(" --------------- " )
    #         #     if record.calibration_interval:
    #         #         if record.calibration_interval_by == 'months':
    #         #             months = record.calibration_interval
    #         #             record.calibration_date = record.calibration_completion_date + timedelta(days=months*30)
    #         #         elif record.calibration_interval_by == 'years':
    #         #             years = record.calibration_interval
    #         #             record.calibration_date = record.calibration_completion_date + timedelta(years*365)
    #         #         else:
    #         #             record.calibration_date = record.calibration_completion_date + timedelta(days=record.calibration_interval)
    #         # else: # not done the calibration
    #         # get calibration_date based on 'today'
    #         if record.is_calibration_required == True:
    #             today = fields.Date.today()
    #             self.check_calibration_interval()
    #             if record.calibration_interval_by == 'months':
    #                 months = record.calibration_interval
    #                 record.calibration_date = today + timedelta(days=months * 30)
    #             elif record.calibration_interval_by == 'years':
    #                 years = record.calibration_interval
    #                 record.calibration_date = today + timedelta(years * 365)
    #             else:
    #                 record.calibration_date = today + timedelta(days=record.calibration_interval)
    #                 record.state = "pending_calibration"  # force it to be "pending"

    @api.depends('sending_email_notification_days_ahead')
    def _compute_send_email_date(self):
        pass
        # for record in self:
        #     if record.is_calibration_required:
        #         if record.calibration_date:
        #             record.send_email_date = record.calibration_date - timedelta(
        #                 days=record.sending_email_notification_days_ahead)
        #             # print('=====================record',record.send_email_date, timedelta(days=record.sending_email_notification_days_ahead) )   #record maintenance.equipment(8,) 2024-06-14
        #             day_delta = (record.send_email_date - datetime.today().date()).days
        #             # print('===============', day_delta)
        #             if day_delta < 0:  # overdue case
        #                 record.send_email_date = datetime.today().date()
        #         else:
        #             raise ValidationError(_("Failed to obtain send email date!"))
        #     print('------------record', record, record.send_email_date)

    @api.model
    def get_email_to(self):
        user_group = self.env.ref("maintenance.group_equipment_manager")
        email_list = [
            usr.partner_id.email for usr in user_group.users if usr.partner_id.email]
        # print("---------------", email_list) #--------------- ['wendy.bigbite@gmail.com', 'admin@yourcompany.example.com', 'taknetwendy@gmail.com']
        return ",".join(email_list)

    # send a email now by clicking the btn
    def action_send_pm_notification_email(self):
        template = self.env.ref('dbb_maintenance.dbb_calibration_email_template')
        for rec in self:
            try:
                template.send_mail(rec.id, force_send=True)
            except MailDeliveryException as e:
                raise ValidationError(_("Sending mail error: ", e))

    # send a scheduled email. stop sending if is_calibration_done= True
    @api.depends('send_email_date')
    def action_send_email_on_scheduled_date(self):
        template = self.env.ref('dbb_maintenance.dbb_calibration_email_template')
        records_of_send_email_today = self.env['maintenance.equipment'].search(
            [('send_email_date', '=', fields.Date.today())])
        # print("++++++++++++++", records_of_send_email_date_met)
        for record in records_of_send_email_today:
            if record.send_email_date == fields.Date.today() and record.is_calibration_done == False:
                try:
                    template.send_mail(record.id, force_send=True)
                except MailDeliveryException as e:
                    raise ValidationError(_("Sending mail error: ", e))

    # # disallow delete the record if is_calibration_required=True
    # @api.ondelete(at_uninstall=False)
    # def _disallow_delete(self):
    #     for rec in self:
    #         if rec.state == 'doing_calibration' or rec.state == 'calibration_overdue':
    #             raise ValidationError(
    #                 _("You cannot delete if this equipment is in 'Doing Calibration' or 'Calibration Overdue' state"))

    # @api.depends('is_calibration_required', 'state')
    # def action_doing_calibration(self):
    #     for rec in self:
    #         if rec.is_calibration_required and rec.state == "pending_calibration":
    #             rec.state = 'doing_calibration'
    #         else:
    #             raise ValidationError(
    #                 _("You cannot change to 'Doing Calibration' if this equipment is not in 'Pending Calibration' state"))

    # @api.depends('calibration_date', 'is_calibration_required')
    # def action_pending_calibration(self):
    #     for rec in self:
    #         # from today to PM_date is "pending_calibration"
    #         if rec.is_calibration_required and rec.calibration_date:
    #             if datetime.today().date() <= rec.calibration_date:
    #                 rec.state = "pending_calibration"
    #                 rec.is_calibration_done = False
    #             else:
    #                 raise ValidationError(_("Please check if 'Cailbration Date' field is invalid"))
    #         else:
    #             raise ValidationError(_("Please check if 'Cailbration Date' field is empty"))

    # @api.depends('calibration_date', 'is_calibration_required')
    # def action_calibration_overdue(self):
    #     for rec in self:
    #         if rec.is_calibration_required:
    #             if datetime.today().date() > rec.calibration_date:
    #                 rec.state = "calibration_overdue"
    #                 rec.is_calibration_done = False
    #                 rec.is_calibration_overdue = True
    #             else:
    #                 rec.is_calibration_overdue = False

    # @api.depends('calibration_date', 'is_calibration_required')
    # def _compute_calibration_overdue(self):
    #     for rec in self:
    #         if rec.is_calibration_required and rec.calibration_date:
    #             overdue_days = (datetime.today().date() - rec.calibration_date).days
    #             if overdue_days > 0:
    #                 rec.state = "calibration_overdue"
    #                 rec.is_calibration_done = False
    #                 rec.is_calibration_overdue = True  # Assign True if maintenance is overdue
    #         else:
    #             rec.is_calibration_overdue = False

    # @api.depends('is_calibration_required')
    # def action_done_calibration(self):
    #     for rec in self:
    #         if rec.is_calibration_required and rec.state == "doing_calibration":
    #             rec.state = 'done_calibration'
    #             # update two fields
    #             rec.is_calibration_done = True
    #             rec.calibration_completion_date = fields.Date.today()
    #             # rec.technician_doing_calibration_id = rec.technician_user_id
    #             # archive the record once the calibration is done
    #             rec.active = False
    #             return {
    #                 'type': 'ir.actions.client',
    #                 'tag': 'display_notification',
    #                 'params': {
    #                     'title': _("Notification"),
    #                     'type': 'warning',
    #                     'message': _("Please check if 'Technician Doing Calibration' is updated"),
    #                     'sticky': True,
    #                 },
    #             }
    #             # return {
    #             #     'effect': {
    #             #         'fadeout': 'slow',
    #             #         'message': "Calibration is Done",
    #             #         'type': 'rainbow_man',
    #             #     }
    #             # }

    # below is inherit method from model to avoid warning not override use @api.model_create_multi
    @api.model_create_multi
    def create(self, data_list):
        for vals in data_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('maintenance.equipment.sequence')
            # print("Success ............", vals.get('name'))
        return super(MaintenanceCalibration, self).create(vals)

    # #  no decorator needed

    def write(self, vals):
        # print("write Success ............", self.name, vals.get('name'))
        if not vals.get('name') and self.name == "New":
            vals['name'] = self.env['ir.sequence'].next_by_code('maintenance.equipment.sequence')
            # print("write Success 2 ............", vals.get('name'))
        return super(MaintenanceCalibration, self).write(vals)

    class Dbb_CalibrationOverdue(models.Model):
        _name = 'dbb.maintenance.calibrationoverdue'
        _description = 'Digital BigBite Maintenance Scheduled Calibration Overdue'

        equipment_sequence_id = fields.Many2one(comodel_name='maintenance.equipment', string="Equipment")
        # appointment_id = fields.Many2one(comodel_name='hospital.appointment', string ="Appointment",domain=['|',('state','=','draft'),('priority','in', ('0','1', False))]) # prioriry is a selection in appointment.py, false : no data
        reason = fields.Text(string="Reason", required=True, default="equipment was breaking down")
        date_rescheduled = fields.Date(string="Reschedule Calibartion Date")

        def action_reschedule_calibration(self):
            return
