from odoo import models, fields, api, _


class ElwQualityCheck(models.Model):
    _name = 'elw.quality.check'
    _description = 'elw quality check'
    _order = 'id desc, name desc'

    name = fields.Char(
        string='Reference', default='New', copy=False, readonly=True)
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        readonly=True, required=True,
        help='The company is automatically set from your user preferences.')

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

    # for notebook
    additional_note = fields.Text('Note')
    note = fields.Html('Instructions')

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

    def do_alert(self):
        pass
