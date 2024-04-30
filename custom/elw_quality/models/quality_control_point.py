# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class ElwQualityPoint(models.Model):
    _name = 'elw.quality.point'
    _description = 'elw quality Point'
    _rec_name = 'name'

    name = fields.Char(
        string='Reference', default='New', copy=False, readonly=True)

    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        readonly=True, required=True,
        help='The company is automatically set from your user preferences.')

    title = fields.Char("Title")
    product_ids = fields.Many2many('product.product', string="Products", domain="[('type','in',('product','consu'))]", )
    product_category_ids = fields.Many2many('product.category', string="Product Categories")
    picking_type_ids = fields.Many2many('stock.picking.type', string='Operations', store=True, copy=True, required=True)
    active = fields.Boolean(default=True)
    user_id = fields.Many2one('res.users', string='Responsible')
    measure_on = fields.Selection([('operation', 'Operation'), ('product', 'Product'), ('move_line', 'Quantity')],
                                  required=True, string='Control per', readonly=True,
                                  help='Product = A quality check is requested per product.'
                                       #  Operation = One quality check is requested at the operation level.
                                       # ' Quantity = A quality check is requested for each new product quantity registered,'
                                       # 'with partial quantity checks also possible.'
                                  )
    measure_frequency_type = fields.Selection([('all', 'All'), ('random', 'Randomly'), ('periodical', 'Periodically')],
                                              required=True, string='Control Frequency')
    measure_frequency_value = fields.Float(string="Control Frequency Value", store=True, copy=True)
    measure_frequency_unit = fields.Selection([('days', 'Days'), ('week', 'Weeks'), ('months', 'Months')],
                                              store=True, copy=True, default='days')
    measure_frequency_unit_value = fields.Integer(store=True, copy=True)

    test_type_id = fields.Many2one('elw.quality.test.type', required=True, string='Test Type')
    team_id = fields.Many2one('elw.quality.team', string='Team')

    # for notebook
    note = fields.Html('Note')

    @api.model_create_multi
    def create(self, vals):
        # print("create Success ............", vals)
        # print("create self ............", self)
        for vals in vals:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.point.sequence')
            # print("Success ............", vals.get('name'))
            rtn = super(ElwQualityPoint, self).create(vals)
            # print("create return ............", rtn)
            return rtn

    # #  no decorator needed
    def write(self, vals):
        # print("write Success ............", vals, vals.get(
        #     'state'))  # write the changes when saving
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.point.sequence')
            # print("write Success 2 ............", vals.get('name'))
        rtn = super(ElwQualityPoint, self).write(vals)
        # print("write return ............", rtn)
        return rtn

class ElwQualityPointTestType(models.Model):
    _name = 'elw.quality.test.type'
    _description = 'elw quality Point Test Type'

    active = fields.Boolean(default=True)
    name = fields.Char(string='Name')
