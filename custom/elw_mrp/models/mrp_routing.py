from odoo import api, fields, models, _, tools
from odoo.exceptions import ValidationError


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    quality_point_count = fields.Integer(string='Instructions')
    quality_point_ids = fields.One2many('elw.quality.point', 'operation_id', string='Quality Point', store=True, copy=True)

