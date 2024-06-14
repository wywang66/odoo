# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, Command
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

    title = fields.Char("Title", store=True)
    product_ids = fields.Many2many('product.product', string="Products", domain="[('type','in',('product','consu'))]",
                                   store=True, required=True, compute="_get_product_from_category", readonly=False,
                                   help="Quality Point will apply to every selected Products.")
    product_id = fields.Many2one('product.product', compute='_compute_product_id_for_measure', store=True)
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
                                   default=_default_test_type_id, ondelete='cascade', store=True, tracking=True,
                                   help="Defines the type of the quality control point.")
    team_id = fields.Many2one('elw.quality.team', string='Team', ondelete='restrict')
    quality_check_count = fields.Integer(string="Check Count", compute="_compute_quality_check_count", store=True)
    check_ids = fields.One2many('elw.quality.check', 'point_id', string="Check IDS")
    #  measure data are child data and put in parent quality.point model
    measure_spec_ids = fields.One2many('elw.quality.measure.spec', 'point_id')

    # for notebook
    note = fields.Html('Note')

    # @api.constrains('product_ids')
    # def _check_if_product_ids_is_single(self):
    #     for rec in self:
    #         if rec.test_type_id.id == 5 and len(rec.product_ids) != 1:
    #             raise ValidationError(_("Set one product for 'Measure' Test Type"))

    # product_ids must be one if test_type_id == 5. measure spec applies to one product
    # below is to sync up product_id on quality.measure.spec. one product for test_type_id=5
    # api.depend or api.onchange run earlier than api.constraints

    # @api.depends('test_type_id')
    # def _compute_measure_spec_ids(self):
    #     for rec in self:
    #         if rec.test_type_id.id == 5:
    #             all_ids = self.env['elw.quality.measure.spec'].sudo().search([])
    #             temp = [each.id for each in all_ids if each.point_id == rec]
    #             rec.measure_spec_ids = self.env['elw.quality.measure.spec'].sudo().browse(temp)
    #             # print("rec.measure_spec_ids...", rec.measure_spec_ids)
    #         else:
    #             rec.measure_spec_ids = None

    @api.depends('product_ids', 'test_type_id')
    def _compute_product_id_for_measure(self):
        for rec in self:
            if rec.test_type_id.id == 5 and len(rec.product_ids) == 1:
                rec.product_id = rec.env['product.product'].browse(rec.product_ids.ids)
            elif rec.test_type_id.id == 5 and len(rec.product_ids) != 1:
                raise ValidationError(_("Set one product for 'Measure' Test Type."))
            else:
                rec.product_id = None

    # measure_spec_ids must be filled if test_type_id == 5
    @api.constrains('measure_spec_ids')
    def _check_if_measure_spec_ids_empty(self):
        for rec in self:
            if rec.test_type_id.id == 5 and not len(rec.measure_spec_ids):
                raise ValidationError(_("Please fill in Measurement Settings Tag."))

    @api.depends('check_ids')
    def _compute_quality_check_count(self):
        for rec in self:
            rec.quality_check_count = self.env['elw.quality.check'].search_count([('point_id', '=', rec.id)])

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
            # print("create Success ............", vals)
            # one2many field include multiple records in vals. vals is a single record
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
            # print("write name ............", vals.get('name'))
        # print("write Success ............", vals)
        rtn = super(ElwQualityPoint, self).write(vals)
        # print("write return ............", rtn)
        return rtn

    def unlink(self):
        for rec in self:
            if rec.quality_check_count:
                raise ValidationError(_("Can not delete the record that links to Quality Check"))
            elif len(rec.measure_spec_ids) > 0:
                # unlink child's records
                rec.measure_spec_ids.unlink()
        return super(ElwQualityPoint, self).unlink()

    def action_see_quality_checks(self):
        return {
            'name': _('Quality Check'),
            'res_model': 'elw.quality.check',
            'domain': [('id', '=', self.check_ids.ids)],
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'target': 'current',
        }

    # https://www.odoo.com/forum/help-1/userwarning-unsupported-operand-type-s-command-update-1-254376
    @api.model
    def default_get(self, fields_list):
        res = super(ElwQualityPoint, self).default_get(fields_list)
        # print("default_get---", fields_list) # all the fields
        # print("res ---", res) # all default value
        if not res.get('picking_type_ids'):
            res['picking_type_ids'] = [Command.set(self.env['stock.picking.type'].search([]).ids)]
        return res
