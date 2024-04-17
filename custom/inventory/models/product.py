from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    detailed_type = fields.Selection(selection_add=[('product', 'Storable Product')], tracking=True, ondelete={'product': 'set consu'}, default = 'product')