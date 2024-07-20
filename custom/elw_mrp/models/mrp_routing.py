from odoo import api, fields, models, _, tools
from odoo.exceptions import ValidationError


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    quality_point_count = fields.Integer(string='Instructions')
    quality_point_ids = fields.One2many('elw.quality.point', 'operation_id', string='Quality Point', store=True, copy=True)

    def action_mrp_workorder_show_steps(self):
        self.ensure_one()
        obj = self.bom_id
        # print('context', obj._context, obj._context.get('product_tmpl_id'))
        # {'params': {'id': 3, 'cids': 1, 'menu_id': 354, 'action': 543, 'model': 'mrp.bom', 'view_type': 'form'}, 'lang': 'en_US', 'tz': 'Asia/Singapore', 'uid': 2, 'allowed_company_ids': [1],
        # 'bom_id_invisible': True, 'default_bom_id': 3, 'tree_view_ref': 'mrp.mrp_routing_workcenter_bom_tree_view'} None
        # print("", self, self.id, self.bom_id, self.bom_id.operation_ids, self.bom_id.picking_type_id, self.bom_id.product_id, self.bom_id.product_tmpl_id,
        #       self.bom_id.product_tmpl_id.product_variant_id)

        return {
            'name': _('Quality Control Point'),
            'res_model': 'elw.quality.point',
            'domain': [('id', '=', self.quality_point_ids.ids)],
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'target': 'current',
        }


class MrpBom(models.Model):
    """ Defines bills of material for a product or a product template """
    _inherit = 'mrp.bom'

    # quality_point_ids = fields.One2many('elw.quality.point', 'operation_id', string='Quality Point', store=True, copy=True)

