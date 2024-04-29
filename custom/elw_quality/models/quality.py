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

    title = fields.Char("Title")
    product_ids = fields.Many2many('product.product', string="Products", domain="[('type','in',('product','consu'))]", )
    product_category_ids = fields.Many2many('product.category', string="Product Categories")
    picking_type_ids = fields.Many2many('stock.picking.type', string='Operations', store=True, copy=True, required=True)
    active = fields.Boolean(default=True)
    user_id = fields.Many2one('res.users', string='Responsible')
    measure_on = fields.Selection([('operation', 'Operation'), ('product', 'Product'), ('move_line', 'Quantity')],
                                  required=True, string='Control per')
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
            # rtn['state'] = "pending_calibration" # set the default value when createing a record
            # create return ............ dbb.maintenance.calibration(6,)
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
        # vals.state = "pending_calibration"
        rtn = super(ElwQualityPoint, self).write(vals)
        # print("write return ............", rtn)
        return rtn


class ElwQualityCheck(models.Model):
    _name = 'elw.quality.check'
    _description = 'elw quality check'

    name = fields.Char(
        string='Reference', default='New', copy=False, readonly=True)

    point_id = fields.Many2one('elw.quality.point', string='Control Point ID')
    stock_picking_id = fields.Many2one('stock.picking', string='Stock Picking ID')
    product_id = fields.Many2one('product.product', string='product', store=True)
    picking_id = fields.Many2one('stock.picking', string='Picking', store=True)
    measure_on = fields.Selection(related='point_id.measure_on', string='Control per')

    # test_type_id = fields.Many2one(
    #     string='Test Type', default='New', copy=False, readonly=True)

    @api.model_create_multi
    def create(self, vals):
        for vals in vals:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.check.sequence')
            rtn = super(ElwQualityCheck, self).create(vals)
            return rtn

    # #  no decorator needed
    def write(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.check.sequence')
        rtn = super(ElwQualityCheck, self).write(vals)
        return rtn


class ElwQualityPointTestType(models.Model):
    _name = 'elw.quality.test.type'
    _description = 'elw quality Point Test Type'

    active = fields.Boolean(default=True)
    name = fields.Char(string='Name')
