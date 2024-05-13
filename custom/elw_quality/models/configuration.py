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
    check_ids = fields.One2many('elw.quality.check', 'team_id', copy=False)
    alert_ids = fields.One2many('elw.quality.alert', 'team_id', copy=False)
    alert_count = fields.Integer("# Quality Alerts", compute="_compute_quality_alert_count")
    check_count = fields.Integer("# Quality Checks", compute="_compute_quality_check_count")

    # For the kanban dashboard only
    todo_qa_check_ids = fields.One2many('elw.quality.check', string="QA Requests", copy=False,
                                        compute='_compute_todo_qa_checks')
    todo_qa_check_count = fields.Integer(string="Number of Requests", compute='_compute_todo_qa_checks')
    todo_qa_check_count_high_priority = fields.Integer(string="Number of Requests in High Priority",
                                                       compute='_compute_todo_qa_checks')
    todo_qa_check_count_fail = fields.Integer(string="Number of Requests Blocked", compute='_compute_todo_qa_checks')

    @api.depends('alert_ids')
    def _compute_quality_alert_count(self):
        for team in self:
            unsolved = 0
            if team.alert_ids.ids:
                unsolved = sum(1 for alert in team.alert_ids if alert.stage_id.name != 'Solved')
            team.alert_count = unsolved

    @api.depends('check_ids')
    def _compute_quality_check_count(self):
        for rec in self:
            todo = 0
            if rec.check_ids.ids:
                todo = sum(1 for check in rec.check_ids if check.quality_state == 'none')
            rec.check_count = todo

    @api.depends('check_ids.quality_state')
    def _compute_todo_qa_checks(self):
        for team in self:
            team.todo_qa_check_ids = self.env['elw.quality.check'].search(
                [('team_id', '=', team.id), ('quality_state', '!=', 'pass'), ('archive', '=', False)])
            print("team.todo_qa_check_ids...", team.todo_qa_check_ids)
            data = self.env['elw.quality.check']._read_group(
                [('team_id', '=', team.id), ('quality_state', '!=', 'pass'), ('archive', '=', False)],
                ['priority', 'quality_state'],
                ['__count']
            )
            team.todo_qa_check_count = sum(count for (_, _, _, count) in data)
            team.todo_qa_check_count_high_priority = sum(count for (_, priority, _, count) in data if priority == 3)
            team.todo_qa_check_count_fail = sum(
                count for (_, _, quality_state, count) in data if quality_state == 'fail')


class QualityAlertStage(models.Model):
    _name = 'elw.quality.alert.stage'
    _description = 'ELW Quality Alter Stage'
    _order = 'sequence, id'

    name = fields.Char('Stage Name', required=True, translate=True)
    sequence = fields.Integer('Sequence')
    folded = fields.Boolean('Folded in Quality Alert')
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
