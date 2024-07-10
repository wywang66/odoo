from odoo import api, fields, models, _, tools
from odoo.exceptions import ValidationError


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'