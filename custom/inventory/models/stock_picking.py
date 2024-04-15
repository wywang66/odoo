from odoo import models, fields, api

# https://www.odoo.com/forum/help-1/pass-a-many2one-field-from-purchase-module-to-inventory-module-249828

class StockMove(models.Model):
    _inherit = "stock.move"    
    
    # for notebook view having one2many field 
    categ_id = fields.Many2one('product.category', 'Product Category', related = 'picking_id.purchase_id.categ_id', required=True)
    # 'stock.move.line' defines picking_id picking_id = fields.Many2one('stock.picking', 'Transfer',)
    # 'stock.picking' defines purchase_id = fields.Many2one('purchase.order', related='move_ids.purchase_line_id.order_id',)
    # \addons\product\models\product_template.py 'product.template' defines 
    # categ_id = fields.Many2one('product.category', 'Product Category', change_default=True, default=_get_default_category_id,


class Picking(models.Model):
    _inherit = "stock.picking"    
    
    # Seen in categ_id = technical|Fields|inherit stock picking
    #  this is inside 'stock.picking' move_ids = fields.One2many('stock.move', 'picking_id', string="Stock Moves", copy=True)
    categ_id = fields.Many2one('product.category', 'Product Category', related = 'purchase_id.categ_id',)
    is_part_qa_checked = fields.Boolean(string='Is Part QA Checked', required = True, default = False)
   
   


