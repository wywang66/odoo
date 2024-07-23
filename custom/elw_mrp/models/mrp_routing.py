from odoo import api, fields, models, _, tools
from odoo.exceptions import ValidationError


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    quality_point_count = fields.Integer(string='Instructions', compute="_compute_quality_point_count")
    quality_point_ids = fields.One2many('elw.quality.point', 'operation_id', string='Quality Point', store=True, copy=True)

    @api.depends('quality_point_ids')
    def _compute_quality_point_count(self):
        for rec in self:
            rec.quality_point_count = self.env['elw.quality.point'].search_count(
                [('operation_id', '=', rec.id)])

    def action_mrp_workorder_show_steps(self):
        self.ensure_one()
        # print('context routing', self.env.context, self.env.context.get('default_bom_id'))
        # {'params': {'id': 3, 'cids': 1, 'menu_id': 354, 'action': 543, 'model': 'mrp.bom', 'view_type': 'form'}, 'lang': 'en_US', 'tz': 'Asia/Singapore', 'uid': 2, 'allowed_company_ids': [1],
        # 'bom_id_invisible': True, 'default_bom_id': 3, 'tree_view_ref': 'mrp.mrp_routing_workcenter_bom_tree_view'} None
        # print("", self, self.id, self.bom_id, self.bom_id.operation_ids, self.bom_id.picking_type_id, self.bom_id.product_id, self.bom_id.product_tmpl_id,
        #       self.bom_id.product_tmpl_id.product_variant_id)

        # use action to fix the no list view display after creating a new record in elw.quality.point
        action = self.env["ir.actions.actions"]._for_xml_id("elw_mrp.elw_quality_control_point_action_window_mrp")
        action['domain'] = [('operation_id', '=', self.id)]
        # below setting is for elw.quality.point
        action['context'] = {
            'default_product_id': self.bom_id.product_tmpl_id.product_variant_id.id,
            'default_operation_id': self.id,
        }
        # print('action_context', self, self.id, self.quality_point_ids) # action_context mrp.routing.workcenter(1,) 1 elw.quality.point(4, 2, 1)
        return action

        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': 'Steps',
        #     'res_model': 'elw.quality.point',
        #     'domain': [('operation_id', '=', self.id)],
        #     'view_mode': 'tree,form',
        #     'target': 'current',
        # }


class MrpBom(models.Model):
    """ Defines bills of material for a product or a product template """
    _inherit = 'mrp.bom'



