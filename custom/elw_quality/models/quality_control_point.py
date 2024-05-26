# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class ElwQualityPoint(models.Model):
    _name = 'elw.quality.point'
    _description = 'elw quality Point'
    _inherit = ['mail.thread',
                'mail.activity.mixin',
                ]  # add a chatter
    _rec_name = 'name'
    _order = 'id desc, name desc'

    def _default_test_type_id(self):
        return self.env['elw.quality.test.type'].search([('name', '=', 'Pass - Fail')], limit=1).id

    name = fields.Char(
        string='Reference', default='New', copy=False, readonly=True)

    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        readonly=True, required=True,
        help='The company is automatically set from your user preferences.')

    title = fields.Char("Title")
    product_ids = fields.Many2many('product.product', string="Products", domain="[('type','in',('product','consu'))]",
                                   store=True, compute="_get_product_from_category", readonly=False,
                                   help="Quality Point will apply to every selected Products.")
    product_category_ids = fields.Many2many('product.category', string="Product Categories", store=True,
                                            help="Quality Point will apply to every Products in the selected Product Categories.")
    picking_type_ids = fields.Many2many('stock.picking.type', string='Operations', store=True, copy=True, required=True)
    active = fields.Boolean(default=True)
    user_id = fields.Many2one('res.users', string='Responsible', ondelete='set null')
    measure_on = fields.Selection([('operation', 'Operation'), ('product', 'Product'), ('move_line', 'Quantity')],
                                  required=True, string='Control per',
                                  help='Product = A quality check is requested per product.'
                                       ' Operation = One quality check is requested at the operation level.'
                                       ' Quantity = A quality check is requested for each new product quantity registered,'
                                       'with partial quantity checks also possible.',
                                  default='operation')
    measure_frequency_type = fields.Selection([('all', 'All'), ('random', 'Randomly'), ('periodical', 'Periodically')],
                                              required=True, string='Control Frequency Type', default='all')
    measure_frequency_value = fields.Float(string="Control Frequency Value", store=True, copy=True)
    measure_frequency_unit = fields.Selection([('days', 'Days'), ('week', 'Weeks'), ('months', 'Months')],
                                              store=True, copy=True, default='days')
    measure_frequency_unit_value = fields.Integer(store=True, copy=True)

    test_type_id = fields.Many2one('elw.quality.test.type', required=True, string='Test Type',
                                   default=_default_test_type_id, ondelete='restrict', store=True, tracking=True,
                                   help="Defines the type of the quality control point.")
    team_id = fields.Many2one('elw.quality.team', string='Team', ondelete='restrict')
    quality_check_count = fields.Integer(string="Check Count", compute="_compute_quality_check_count")
    check_ids = fields.One2many('elw.quality.check', 'point_id', string="Check IDS")
    # for notebook
    note = fields.Html('Note')
    #  measure data
    measure_data_ids = fields.One2many('elw.quality.measure.spec', 'point_id')

    @api.depends('check_ids')
    def _compute_quality_check_count(self):
        for rec in self:
            if rec.check_ids.ids:
                rec.quality_check_count = sum(1 for check in rec.check_ids)
            else:
                rec.quality_check_count = 0
            # print("rec.quality_check_count", rec.quality_check_count)


    @api.depends('product_category_ids')
    def _get_product_from_category(self):
        for rec in self:
            if rec.product_category_ids and not rec.product_ids:
                rec.product_ids = self.env['product.product'].search([('categ_id', 'in', rec.product_category_ids.ids)])

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
        if not self.name and not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.point.sequence')
            # print("write Success 2 ............", vals.get('name'))
        rtn = super(ElwQualityPoint, self).write(vals)
        # print("write return ............", rtn)
        return rtn

    def action_see_quality_checks(self):
        return {
            'name': _('Quality Check'),
            'res_model': 'elw.quality.check',
            'domain': [('id', '=', self.check_ids.ids)],
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'target': 'current',
        }
