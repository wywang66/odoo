from odoo import models, fields, api, _


class ElwQualityCheck(models.Model):
    _name = 'elw.quality.check'
    _inherit = ['mail.thread',
                'mail.activity.mixin',
                ]  # add a chatter
    _description = 'elw quality check'
    _order = 'id desc, name desc'

    name = fields.Char(
        string='Reference', default='New', copy=False, readonly=True)
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        readonly=True, required=True,
        help='The company is automatically set from your user preferences.')
    active = fields.Boolean(default=True)
    point_id = fields.Many2one('elw.quality.point', string='Control Point ID')

    partner_id = fields.Many2one('res.partner', string='Partner')
    product_id = fields.Many2one('product.product', string='Product', store=True)
    picking_id = fields.Many2one('stock.picking', string='Picking', store=True)
    measure_on = fields.Selection(related='point_id.measure_on', string='Control per')
    lot_id = fields.Many2one('stock.lot', string='Lot/Serial', store=True)
    user_id = fields.Many2one('res.users', string='Checked By', store=True)
    test_type_id = fields.Many2one(related='point_id.test_type_id', string='Test Type', )
    team_id = fields.Many2one('elw.quality.team', string='Team')
    control_date = fields.Date(string='Checked Date')
    quality_state = fields.Selection([('none', 'To Do'), ('pass', 'Passed'), ('fail', 'Failed')], required=True,
                                     default='none')
    test_type = fields.Char(related='point_id.test_type', string="Test Type")
    alert_count = fields.Integer(default=0)
    alert_ids = fields.One2many('elw.quality.alert', 'check_id', string="Alerts")
    alert_result = fields.Char(compute="_compute_alert_result")
    # for notebook
    additional_note = fields.Text('Note')
    note = fields.Html('Instructions')

    @api.depends('alert_ids')
    def _compute_alert_result(self):
        for rec in self:
            alert_result_list = [alert_res.stage_id.name for alert_res in rec.alert_ids] if rec.quality_state == 'fail' else []
            print("alert_result_list=========", alert_result_list)
            if all(res == 'Solved' for res in alert_result_list):
                rec.alert_result = 'Solved'
            else:
                rec.alert_result = 'Unsolved'

    @api.model_create_multi
    def create(self, vals):
        for vals in vals:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.check.sequence')
            rtn = super(ElwQualityCheck, self).create(vals)
            return rtn

    # #  no decorator needed
    def write(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.check.sequence')
        rtn = super(ElwQualityCheck, self).write(vals)
        return rtn

    def action_see_alerts(self):
        pass

    def do_pass(self):
        for rec in self:
            if rec.quality_state == 'none':
                rec.quality_state = 'pass'

    def do_fail(self):
        for rec in self:
            if rec.quality_state == 'none':
                rec.quality_state = 'fail'

    def do_measure(self):
        pass

    def _create_qa_alert_record(self, vals):
        self.ensure_one()
        qa_alert_rec = self.env['elw.quality.alert'].create(vals)
        print("created qa_alert_rec--------", qa_alert_rec, qa_alert_rec.id, qa_alert_rec.name)
        return qa_alert_rec

    def do_alert(self):
        self.ensure_one()
        # get vals to create a quality.alert record
        vals = {
            'product_id': self.product_id.id,
            'check_id': self.id,
            'picking_id': self.picking_id.id,
            'partner_id': self.partner_id.id,
            'team_id': self.team_id.id,
            'user_id': self.user_id.id,
        }
        print("vals in quality.check---------", vals)
        qa_alert_rec = self._create_qa_alert_record(vals)

        return {
            'name': _('Quality Alert'),
            'res_model': 'elw.quality.alert',
            'res_id': qa_alert_rec.id,  # open the corresponding form
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('elw_quality.elw_quality_alert_form_view').id,
            # 'target': 'new',
        }
