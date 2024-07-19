from odoo import api, fields, models, _, tools
from odoo.exceptions import ValidationError


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    quality_point_count = fields.Integer(string='Instructions')
    quality_point_ids = fields.One2many('elw.quality.point', 'operation_id', string='Quality Point', store=True, copy=True)

    def action_mrp_workorder_show_steps(self):
        pass


class MrpBom(models.Model):
    """ Defines bills of material for a product or a product template """
    _inherit = 'mrp.bom'

    # quality_point_ids = fields.One2many('elw.quality.point', 'operation_id', string='Quality Point', store=True, copy=True)

