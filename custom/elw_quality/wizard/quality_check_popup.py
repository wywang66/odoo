from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class QualityCheckPopup(models.TransientModel):
    _name = 'elw.quality.check.popup.wizard'
    _description = 'elw quality check popup notification'

    name = fields.Char(
        string='Reference', default='New', copy=False, readonly=True)

    product_ids = fields.Many2many('product.product', string='Product')
    check_ids = fields.Many2many('elw.quality.check', string="QA Check Reference#")
    partner_id = fields.Many2one('res.partner', string='Vendor/Customer')
    quality_state = fields.Selection([('none', 'To Do'), ('pass', 'Passed'), ('fail', 'Failed')], default='none')
    quality_alert_ids = fields.Many2many('elw.quality.alert', string="Alerts")
    quality_alert_open_count = fields.Integer(string="Quality Alert Open Count")
    qa_status = fields.Char("Status", compute="_compute_qa_status")
    info = fields.Char(string="Next", default="Please Proceed to Quality Checks for 'To Do' or 'Failed' Actions...",
                       readonly=True)
    info_fail = fields.Char(string="Next", default="Please proceed Quality Checks for 'Failed' Actions...",
                            readonly=True)

    def _get_selection_field_value(self, key):
        if key == 'none':
            return "To Do"
        elif key == 'fail':
            return "Failed"
        elif key == 'pass':
            return "Passed"

    @api.depends('check_ids')
    def _compute_qa_status(self):
        temp = []
        for chk_id in self.check_ids:
            temp.append(chk_id.name + ': ' + self._get_selection_field_value(chk_id.quality_state))
        self.qa_status = ', '.join(temp)

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
