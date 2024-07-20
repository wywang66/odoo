from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
import json

class ElwQualityPoint(models.Model):
    _inherit = 'elw.quality.point'

    operation_id = fields.Many2one('mrp.routing.workcenter', string='Step', ondelete='set null', store=True, copy=True)
    # operation_id = fields.Many2one('mrp.bom', string='Operation', ondelete='set null', store=True, copy=True)

    # parent_id = fields.Many2one('mrp.bom', string="Parent")
    # product_id = fields.Many2one('product.product', string="Product")
    # lst_price = fields.Float("Sale Price")
    #
    # @api.onchange('product_id')
    # def onchange_product_id(self):
    #     variant_ids_list = []
    #     if self._context.get('template_id'):   # We; will pass this; context from the xml; view.
    #         template_id = self.env["product.template"].browse(self._context.get('template_id'))
    #         for variant_id in template_id.product_variant_ids:
    #             if variant_id.lst_price > 100:
    #                 variant_ids_list.append(variant_id.id)

    @api.model
    def default_get(self, fields_list):
        res = super(ElwQualityPoint, self).default_get(fields_list)
        # print("default_get---", fields_list) # all the fields
        # print("res ---", res) # all default value
        # print("context.......", self.env.context)
        #context....... {'lang': 'en_US', 'tz': 'Asia/Singapore', 'uid': 2, 'allowed_company_ids': [1], 'params': {'id': 3, 'cids': 1, 'menu_id': 354, 'action': 543, 'model': 'mrp.bom', 'view_type': 'form'},
        # 'bom_id_invisible': True, 'active_model': 'mrp.routing.workcenter', 'active_id': 1, 'active_ids': [1]}
        routing_obj = self.env['mrp.routing.workcenter'].browse(self.env.context.get('active_id'))
        stock_type_obj = self.env['stock.picking.type'].search([])
        if not res.get('product_ids'):
            res['product_ids'] = [(6, 0, [routing_obj.bom_id.product_tmpl_id.product_variant_id.id])]
            if routing_obj.bom_id.type == 'normal':
                res['picking_type_ids'] = [(6, 0, [stock_type_obj[len(stock_type_obj) - 1].id])]
        if not res.get('picking_type_ids'):
            res['picking_type_ids'] = [(6, 0, [stock_type_obj.ids])]
        return res

    # @api.model
    # def default_get(self, fields_list):
    #     defaults = super(ElwQualityPoint, self).default_get(fields_list)

        # operation_id = self._context.get('default_operation_id')
        #
        # print("Operation ID from context:", operation_id)

        # if operation_id:
        #     operation = self.env['mrp.routing.workcenter'].browse(operation_id)
        #     if operation and operation.bom_id:
        #         # Set product_ids based on the product variant of the BoM
        #         defaults['product_ids'] = [(6, 0, [operation.bom_id.product_tmpl_id.product_variant_id.id])]
        #
        #         # Set picking_type_ids to 'Manufacturing' (assuming it's a specific picking type)
        #         manufacturing_picking_type = self.env.ref('stock.picking_type_manufacturing')
        #         if manufacturing_picking_type:
        #             defaults['picking_type_ids'] = [(6, 0, [manufacturing_picking_type.id])]
        #         else:
        #             print("Manufacturing picking type not found.")
        #     else:
        #         print("No BoM found for the operation.")
        # else:
        #     print("No operation_id in context.")

    # return defaults
