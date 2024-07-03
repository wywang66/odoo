from odoo import models, fields, api, SUPERUSER_ID, _

# # separate into two inheritance classes to avoid the "equipment_ids" not found error after inheriting 'mail' in MrpWorkcenter1
# New ValueError: The _name attribute MrpWorkcenter is not valid.
# class MrpWorkcenter(models.Model):
#     _inherit = ['mail.thread',
#                 'mail.activity.mixin',
#                 ]  # add a chatter


class MrpWorkcenter1(models.Model):
    _inherit = 'mrp.workcenter'
    # _inherit = ['mail.thread',
    #             'mail.activity.mixin',
    #             ]  # add a chatter

    equipment_ids = fields.Many2many('maintenance.equipment', string='Equipment', copy=True)

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    maintenance_ids = fields.One2many('maintenance.request', 'workcenter_id', string='Maintenance', store=True)
    maintenance_count = fields.Integer(compute='_compute_maintenance_count', string="Maintenance Count", store=True)
    maintenance_open_count = fields.Integer(compute='_compute_maintenance_count', string="Current Maintenance", store=True)
    maintenance_team_id = fields.Many2one('maintenance.team', string='Maintenance Team', compute='_compute_maintenance_team_id', store=True, readonly=False,
                                          check_company=True)
    technician_user_id = fields.Many2one('res.users', string='Technician', tracking=True)

    @api.depends('company_id')
    def _compute_maintenance_team_id(self):
        for record in self:
            if record.maintenance_team_id.company_id and record.maintenance_team_id.company_id.id != record.company_id.id:
                record.maintenance_team_id = False

    @api.depends('maintenance_ids.stage_id.done', 'maintenance_ids.archive')
    def _compute_maintenance_count(self):
        for record in self:
            record.maintenance_count = len(record.maintenance_ids)
            record.maintenance_open_count = len(record.maintenance_ids.filtered(lambda mr: not mr.stage_id.done and not mr.archive))


