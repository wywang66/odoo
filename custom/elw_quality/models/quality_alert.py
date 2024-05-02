from odoo import models, fields, api, _


class ElwQualityAlert(models.Model):
    _name = 'elw.quality.alert'
    _description = 'elw quality alert'
    _order = 'id desc, name desc'

    name = fields.Char(
        string='Reference', default='New', copy=False, readonly=True)
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        readonly=True, required=True,
        help='The company is automatically set from your user preferences.')

    partner_id = fields.Many2one('res.partner', string='Partner')
    product_id = fields.Many2one('product.product', string='Product', store=True)
    picking_id = fields.Many2one('stock.picking', string='Picking', store=True)
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Very High')], string="Priority", tracking=True, store=True)  # used to order
    check_id = fields.Many2one('elw.quality.check', string='Check', store=True)
    lot_id = fields.Many2one('stock.lot', string='Lot/Serial', store=True)
    # stage_id = fields.Many2one('quality.alert.stage', string='Stage', store=True, copy=True)
    user_id = fields.Many2one('res.users', string='Responsible', store=True)
    team_id = fields.Many2one('elw.quality.team', string='Team')
    date_assign = fields.Date(string='Date Assigned')
    date_close = fields.Date(string='Date Closed')
    tag_ids = fields.Many2many('elw.quality.tag', string='Tags')
    reason_id = fields.Many2one('elw.quality.reason', string='Root Cause')

    title = fields.Char(string='Title')

    # for notebook
    # additional_note = fields.Text('Note')
    # note = fields.Html('Instructions')
    description = fields.Text('Description')
    action_preventive = fields.Html('Preventive Action', store=True, copy =True)
    action_corrective = fields.Html('Corrective Action', store=True, copy=True)

    @api.model_create_multi
    def create(self, vals):
        for vals in vals:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.check.sequence')
            rtn = super(ElwQualityAlert, self).create(vals)
            return rtn

    # #  no decorator needed
    def write(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.check.sequence')
        rtn = super(ElwQualityAlert, self).write(vals)
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
