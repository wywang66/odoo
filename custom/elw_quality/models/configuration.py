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
    alert_count = fields.Integer("# Quality Alerts")
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


class QualityAlertStage(models.Model):
    _name = 'elw.quality.alert.stage'
    _description = 'ELW Quality Alter Stage'
    _order = 'sequence, id'

    name = fields.Char('Stage Name', required=True, translate=True)
    sequence = fields.Integer('Sequence')
    folded = fields.Boolean('Folded')
    done = fields.Boolean('Alert Processed')
    team_ids = fields.Many2many('elw.quality.team', string='Teams')


class QualityReason(models.Model):
    _name = 'elw.quality.reason'
    _description = 'ELW Quality Location'
    _order = 'id'

    active = fields.Boolean(default=True)
    name = fields.Char('Name', required=True, translate=True)
    # display_name = fields.Char('Display Name', required=True, translate=True)


class QualityTag(models.Model):
    _name = 'elw.quality.tag'
    _description = 'Quality Tag'

    name = fields.Char(string='Tag Name', required=True, trim=True)  # trim the spaces when user entering this field
    active = fields.Boolean(string="Active", default=True)
    color = fields.Integer("Color")

    _sql_constraints = [
        ('uniq_name', 'unique(name, active)', 'name must be unique.'),
    ]


class QualityPointTestType(models.Model):
    _name = 'elw.quality.test.type'
    _description = 'ELW Quality Control Point Test Type'

    active = fields.Boolean(default=True)
    name = fields.Char(string='Name')
    technical_name = fields.Char(string="Technical Name", compute="_compute_test_type")

    def _compute_test_type(self):
        if self.name == 'Instructions':
            self.technical_name = 'instructions'
        elif self.name == 'Take a Picture':
            self.technical_name = 'picture'
        elif self.name == 'Register Production':
            self.technical_name = 'register_production'
        elif self.name == 'Pass - Fail':
            self.technical_name = 'passfail'
        elif self.name == 'Measure':
            self.technical_name = 'measure'



