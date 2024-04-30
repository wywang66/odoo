from odoo import models, fields, api, _
from datetime import date
import datetime
from odoo.exceptions import ValidationError
from dateutil import relativedelta


class QualityCheckWizard(models.TransientModel):
    _name = 'elw.quality.check.wizard'
    _description = 'ELW Quality Check Wizard'

    check_ids = fields.Many2many('elw.quality.check', string="Check")
    current_check_id = fields.Many2one('elw.quality.check', string="Current Check")
    measure_on = fields.Selection(related='current_check_id.measure_on', string='Control per')

    note = fields.Html('Note')
    product_id = fields.Many2one('product.product', string='Product', related="current_check_id.product_id")
    test_type = fields.Char(related='current_check_id.test_type')
    is_last_check = fields.Boolean(readonly=True)
    name = fields.Char(related='current_check_id.name', string="Reference")
    quality_state = fields.Selection([('pass', 'PASS'), ('fail', 'Fail'), ('none', 'To Do')])
    additional_note = fields.Text(string="Additional Note")

    def do_pass(self):
        qa_check_obj = self.env['elw.quality.check']
        pass

    def do_fail(self):
        pass
