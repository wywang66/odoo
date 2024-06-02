from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class QualityCheckPopup(models.TransientModel):
    _name = 'elw.quality.check.popup.wizard'
    _description = 'elw quality check popup notification'

    product_ids = fields.Many2many('product.product', string='Product')
    check_ids = fields.Many2many('elw.quality.check', string="QA Check Reference#")
    partner_id = fields.Many2one('res.partner', string='Vendor/Customer', ondelete='cascade')
    quality_state = fields.Selection([('none', 'To Do'), ('pass', 'Passed'), ('fail', 'Failed')],
                                     compute="_compute_quality_state")
    # quality_alert_ids = fields.Many2many('elw.quality.alert', string="Alerts")
    # quality_alert_open_count = fields.Integer(string="Quality Alert Open Count")
    is_all_quality_fails_resolved = fields.Boolean(string="Solved all Failing?")
    qa_status = fields.Char("Status", compute="_compute_qa_status")
    info = fields.Text(string="Next", default="Please Proceed to Quality Checks for 'To Do' or 'Failed' Actions...",
                       readonly=True)

    @api.depends('qa_status')
    def _compute_quality_state(self):
        for rec in self:
            rec.quality_state = 'none'
            if "Failed" in rec.qa_status:
                rec.quality_state = 'fail'

    def _get_selection_field_value(self, key):
        if key == 'none':
            return "To Do"
        elif key == 'fail':
            return "Failed"
        elif key == 'pass':
            return "Passed"

    @api.depends('check_ids')
    def _compute_qa_status(self):
        for rec in self:
            rec.qa_status = ''
            temp = []
            for chk_id in self.check_ids:
                temp.append(chk_id.name + ': ' + self._get_selection_field_value(chk_id.quality_state))
            rec.qa_status = ', '.join(temp)


