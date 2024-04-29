from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    # _name = 'product.template'
    _inherit = 'product.product'