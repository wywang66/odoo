from odoo import models, fields, api, _


class QualityTeam(models.Model):
    _name = 'elw.quality.team'
    _inherit = ['mail.thread',
                'mail.activity.mixin',
                ]  # add a chatter
    _description = 'ELW Quality Teams'
    _rec_name = 'name'

    name = fields.Char('Team Name', required=True, translate=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    # odoo creates quality_team_users_rel table for this many2many field
    member_ids = fields.Many2many(
        'res.users',  string="Team Members",
        domain="[('company_ids', 'in', company_id)]")
    color = fields.Integer("Color Index", default=0)
    check_ids = fields.One2many('elw.quality.check', 'team_id', copy=False)
    alert_ids = fields.One2many('elw.quality.alert', 'team_id', copy=False)
    check_count = fields.Integer("# Quality Checks", compute="_compute_quality_check_count", store=True)
    alias_contact = fields.Selection(
        [('everyone', 'Everyone'), ('partners', 'Authenticated Partners'), ('followers', 'Followers'),
         ('employees', "Authenticated Employees")], default='everyone')
    alias_name = fields.Char(string="Alias Name",
                             help="The name of the email alias, e.g. 'jobs' if you want to catch emails for <jobs@example.odoo.com>")

    alias_domain_id = fields.Many2one('mail.alias.domain', string="Alias Domain")
    alias_id = fields.Many2one('mail.alias', string="Alias")
    alias_email = fields.Char(string="Email Alias")
    # For the kanban dashboard only
    todo_qa_check_ids = fields.One2many('elw.quality.check', string="QA Requests", copy=False,
                                        compute='_compute_todo_qa_checks')

    todo_qa_check_count = fields.Integer(string="# Requests", compute='_compute_todo_qa_checks')
    # todo_qa_check_count_high_priority = fields.Integer(string="Number of Requests in High Priority",
    #                                                    compute='_compute_todo_qa_checks')
    todo_qa_check_count_fail = fields.Integer(string="# Fail Checks", compute='_compute_todo_qa_checks')

    todo_qa_alert_ids = fields.One2many('elw.quality.alert', string="QA Alerts", copy=False,
                                        compute='_compute_todo_qa_alerts')
    todo_qa_alert_count = fields.Integer(string="# Alerts", compute='_compute_todo_qa_alerts')
    todo_qa_alert_count_high_priority = fields.Integer(string="# Alerts in High Priority",
                                                       compute='_compute_todo_qa_alerts')
    todo_qa_alert_count_unsolved = fields.Integer(string="# Unsolved Alerts", compute='_compute_todo_qa_alerts')

    @api.depends('check_ids', 'check_ids.alert_result')
    def _compute_quality_check_count(self):
        for rec in self:
            rec.check_count = sum(1 for check in rec.check_ids if check.alert_result != 'Passed') if len(
                rec.check_ids) else 0

    @api.depends('alert_ids')
    def _compute_todo_qa_alerts(self):
        for team in self:
            team.todo_qa_alert_ids = self.env['elw.quality.alert'].search(
                [('team_id', '=', team.id), ('stage_id.name', '!=', 'Solved')])
            # team.todo_qa_check_ids = self.env['elw.quality.check'].search(
            #     [('team_id', '=', team.id), ('quality_state', '!=', 'pass'), ('archive', '=', False)])
            # print("team.todo_qa_alert_ids...", team.todo_qa_alert_ids, team.id, team.name)

            data = self.env['elw.quality.alert']._read_group(
                domain=[('team_id', '=', team.id), ('stage_id.name', '!=', 'Solved')],
                groupby=['stage_id', 'priority'],
                aggregates=['__count']
            )
            # print("data...", data)  # data = [(elw.quality.alert.stage(1,), '2', 1), (elw.quality.alert.stage(1,), '3', 1)]
            # when iterating over data, the underscore _ is used to "catch" the first element of each tuple and ignore it.
            team.todo_qa_alert_count = sum(count for (_, _, count) in data)
            team.todo_qa_alert_count_high_priority = sum(count for (_, priority, count) in data if priority == '3')
            undone_data = [(stage_id, _, count) for stage_id, _, count in data if stage_id.name != 'Solved']
            team.todo_qa_alert_count_unsolved = sum(
                count for (_, _, count) in undone_data)
            # print("cnt/priority/undone_cnt...", team.todo_qa_alert_count, team.todo_qa_alert_count_high_priority, team.todo_qa_alert_count_unsolved)

    @api.depends('check_ids.quality_state')
    def _compute_todo_qa_checks(self):
        for team in self:
            team.todo_qa_check_ids = self.env['elw.quality.check'].search(
                [('team_id', '=', team.id), ('quality_state', '!=', 'pass')])
            # team.todo_qa_check_ids = self.env['elw.quality.check'].search(
            #     [('team_id', '=', team.id), ('quality_state', '!=', 'pass'), ('archive', '=', False)])
            # print("team.todo_qa_check_ids...", team.todo_qa_check_ids, team.id)

            data = self.env['elw.quality.check']._read_group(
                domain=[('team_id', '=', team.id), ('quality_state', '!=', 'pass')],
                groupby=['quality_state'],
                aggregates=['__count']
            )
            # print("data...", data)  # data = [('fail', 4), ('none', 1)]
            #  when iterating over data, the underscore _ is used to "catch" the first element of each tuple and ignore it.
            team.todo_qa_check_count = sum(count for (_, count) in data)
            fail_data = [(quality_state, count) for quality_state, count in data if quality_state == 'fail']
            team.todo_qa_check_count_fail = sum(
                count for (_, count) in fail_data)
            # print("data...", team.todo_qa_check_count, team.todo_qa_check_count_fail)


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
