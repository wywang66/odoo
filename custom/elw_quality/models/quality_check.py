from odoo import models, fields, api, _


class ElwQualityCheck(models.Model):
    _name = 'elw.quality.check'
    _description = 'elw quality check'

    name = fields.Char(
        string='Reference', default='New', copy=False, readonly=True)
    # company_id = fields.Many2one()
    point_id = fields.Many2one('elw.quality.point', string='Control Point ID')
    stock_picking_id = fields.Many2one('stock.picking', string='Stock Picking ID')
    product_id = fields.Many2one('product.product', string='product', store=True)
    picking_id = fields.Many2one('stock.picking', string='Picking', store=True)
    measure_on = fields.Selection(related='point_id.measure_on', string='Control per')

    test_type_id = fields.Many2one(related='point_id.test_type_id', string='Test Type', )
    team_id = fields.Many2one('elw.quality.team', string='Team')
    control_date = fields.Date(string="Control Date")
    quality_state = fields.Selection([('pass', 'PASS'), ('fail', 'Fail'),('none', 'None')])
    test_type = fields.Char(string="Test Type")

    # for notebook
    note = fields.Text('Note')
    instructions = fields.Html('Instructions')
    alert_count = fields.Integer(default=0)

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
        pass

    def do_fail(self):
        pass

    def do_measure(self):
        pass

    def do_alert(self):
        pass
