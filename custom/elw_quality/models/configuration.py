from odoo import models, fields, api, _


class QualityTeam(models.Model):
    _name = 'elw.quality.team'
    _description = 'ELW Quality Teams'
    _rec_name = 'name'

    name = fields.Char('Team Name', required=True, translate=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    # odoo creates quality_team_users_rel table for this many2many field
    member_ids = fields.Many2many(
        'res.users', 'quality_team_users_rel', string="Team Members",
        domain="[('company_ids', 'in', company_id)]")
    color = fields.Integer("Color Index", default=0)
    # member_ids = fields.Many2many('hr.employee', string="Company employee",)

    # For the dashboard only
    # todo_request_ids = fields.One2many('maintenance.request', string="Requests", copy=False,
    #                                    compute='_compute_todo_requests')
    # todo_request_count = fields.Integer(string="Number of Requests", compute='_compute_todo_requests')
    # todo_request_count_date = fields.Integer(string="Number of Requests Scheduled", compute='_compute_todo_requests')
    # todo_request_count_high_priority = fields.Integer(string="Number of Requests in High Priority",
    #                                                   compute='_compute_todo_requests')
    # todo_request_count_block = fields.Integer(string="Number of Requests Blocked", compute='_compute_todo_requests')
    # todo_request_count_unscheduled = fields.Integer(string="Number of Requests Unscheduled",
    #                                                 compute='_compute_todo_requests')

class QualityStage(models.Model):
    """ Model for case stages. This models the main stages of a quality Request management flow. """

    _name = 'elw.quality.alter.stage'
    _description = 'ELW Quality Alter Stage'
    _order = 'sequence, id'

    name = fields.Char('Stage Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=20)
    fold = fields.Boolean('Folded in Quality Pipe')
    done = fields.Boolean('Request Done')
    team_id = fields.Many2one('elw.quality.team', string='Team')