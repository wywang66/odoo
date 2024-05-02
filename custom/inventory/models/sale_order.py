from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
   
    # product_id = fields.Many2one(comodel_name='product.product', string="Product",
    categ_id = fields.Many2one('product.category', related='product_id.categ_id', store=True)

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    # for notebook view having one2many field 
    categ_id = fields.Many2one('product.category', 'Product Category', related = 'order_line.categ_id', required=True)
    product_id = fields.Many2one('product.product', 'Product', related = 'order_line.product_id')