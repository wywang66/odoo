from odoo import models, fields, api

# https://www.odoo.com/forum/help-1/pass-a-many2one-field-from-purchase-module-to-inventory-module-249828

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    # ---------------------
    #  Before: with the command in line 19, categ_id did not show under Product category
    #  After: copy line 18 from 'purchase.order.line', categ_id shows
    #  Now:  commented line 18, it works as expected.       
    # ---------------------
    # purchase.order.line defines order_id as many2one 
    # use related='order_id.categ_id' results in RecursionError: maximum recursion depth exceeded
   
    # product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True)], change_default=True, index='btree_not_null')
    # copy product_id from 'purchase.order.line'
    # product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True)], change_default=True, index='btree_not_null')
    categ_id = fields.Many2one('product.category', related='product_id.categ_id')
    

# order_line = fields.One2many('purchase.order.line', 'order_id', string='Order Lines', copy=True)
class PurchaseOrder(models.Model):
    _inherit = "purchase.order"    
  
    # for list view
    # use order_line to relate the field
    # purchase.order defines order_line as one2many 
    # order_line = fields.One2many('purchase.order.line', 'order_id', string='Order Lines', copy=True)
    # product_id = fields.Many2one('product.product', related='order_line.product_id', string='Product')
    categ_id = fields.Many2one('product.category', related='order_line.categ_id', string='Product Category', store=True)
    # print("----------------purchase.order", categ_id)
    

# # bewlo has product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
# class StockMoveLine(models.Model):
#     _inherit = "stock.move.line"
    

# #move_line_ids = fields.One2many('stock.move.line', 'move_id')    
# class StockMove(models.Model):
#     _inherit = "stock.move"
    
#     categ_id = fields.Many2one('purchase.order', string='Product Category') 
#     print("----------------stock.move", categ_id)
    
#     categ_id2 = fields.Many2one('stock.move.line', related='move_line_ids.product_uom_category_id', string='Product Category') 
#     print("----------------stock.move", categ_id2)

# # below model has move_ids = fields.One2many('stock.move', 'picking_id', string="Stock Moves", copy=True)
# #  move_ids_without_package = fields.One2many(
#         # 'stock.move', 'picking_id', string="Stock move", domain=['|', ('package_level_id', '=', False), ('picking_type_entire_packs', '=', False)])
# class Picking(models.Model):
#     _inherit = "stock.picking"   
    
#     categ_id = fields.Many2one('stock.move', related='move_ids_without_package.categ_id', string='Product Category')        

