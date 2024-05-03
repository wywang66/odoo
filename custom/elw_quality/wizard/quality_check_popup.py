from odoo import models, fields, api, _


class QualityCheckPopup(models.TransientModel):
    _name = 'elw.quality.check.popup.wizard'

    _description = 'elw quality check popup notification'

    name = fields.Char(
        string='Reference', default='New', copy=False, readonly=True)

    product_ids = fields.Many2many('product.product', string='Product', store=True)
    check_ids = fields.Many2many('elw.quality.check', string="QA Check Reference#")
    partner_id = fields.Many2one('res.partner', string='Vendor/Customer')
    quality_state = fields.Selection([('none', 'To Do'), ('pass', 'Passed'), ('fail', 'Failed')], required=True,
                                     default='none')

    @api.model_create_multi
    def create(self, vals):
        for vals in vals:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.check.popup.wizard.sequence')
            rtn = super(QualityCheckPopup, self).create(vals)
            return rtn

    # #  no decorator needed
    def write(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.check.popup.wizard.sequence')
        rtn = super(QualityCheckPopup, self).write(vals)
        return rtn

