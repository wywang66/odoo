from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError


class ElwQualityPoint(models.Model):
    _inherit = 'elw.quality.point'

    def _default_test_type_id(self):
        return self.env['elw.quality.test.type'].search([('name', '=', 'Pass - Fail')], limit=1).id

    product_ids = fields.Many2many('product.product', string="Products",
                                   domain="[('type','in',('product','consu')), '|',('company_id','=', False),('company_id','=', company_id)]",
                                   store=True, required=True, compute="_get_product_from_category", readonly=False,
                                   help="Quality Point will apply to every selected Products.")
    operation_id = fields.Many2one('mrp.routing.workcenter', string='Manu Step', ondelete='set null', store=True, copy=True)
    # component_id = fields.Many2one('product.product', string='Product To Register', ondelete='set null', store=True, copy=True)
    # component_ids = fields.One2many('product.product', string='Component', )
    is_workorder_step = fields.Boolean(string='Is Workorder Step', compute="_compute_is_wordorder_step", default=False)
    test_type_id = fields.Many2one('elw.quality.test.type', required=True, string='Test Type',
                                   default=_default_test_type_id, ondelete='cascade', store=True, tracking=True,
                                   # domain="[('allow_registration', '=', True)]",
                                   help="Defines the type of the quality control point.")
    # test_report_type = fields.Selection(store=True, copy=True)
    # source_document = fields.Selection(string='Step Document', store=True, copy=True)
    worksheet_page = fields.Integer(string='Worksheet Page', store=True, copy=True)
    worksheet_document = fields.Binary(string='Image/PDF', store=True, copy=True)
    worksheet_url = fields.Char(string='Google doc URL', store=True, copy=True)
    # bom_id = fields.Many2one('mrp.bom', string='Bill of Material', compute='_compute_bom_id')
    # bom_active = fields.Boolean(string='Related Bill of Material Active')
    # bom_product_id = fields.Many2one('product.product', string='Bom Product', related='bom_id.product_tmpl_id.product_variant_id')

    @api.depends('operation_id.quality_point_count')
    def _compute_is_wordorder_step(self):
        for rec in self:
            rec.is_workorder_step = True if rec.operation_id.quality_point_count else False

    @api.model
    def default_get(self, fields_list):
        res = super(ElwQualityPoint, self).default_get(fields_list)
        # print("default_get---", fields_list) # all the fields
        # print("res ---", res) # all default value
        # print("qa point- context.......", self.env.context)
        #context....... {'lang': 'en_US', 'tz': 'Asia/Singapore', 'uid': 2, 'allowed_company_ids': [1], 'params': {'id': 3, 'cids': 1, 'menu_id': 354, 'action': 543, 'model': 'mrp.bom', 'view_type': 'form'},
        # 'bom_id_invisible': True, 'active_model': 'mrp.routing.workcenter', 'active_id': 1, 'active_ids': [1]}
        stock_type_obj = self.env['stock.picking.type'].search([])
        if self.env.context.get('active_model') == 'mrp.routing.workcenter' and self.env.context.get('active_id'):
            routing_obj = self.env['mrp.routing.workcenter'].browse(self.env.context.get('active_id'))
            if not res.get('product_ids'):
                res['product_ids'] = [(6, 0, [routing_obj.bom_id.product_tmpl_id.product_variant_id.id])]
                res['operation_id'] = routing_obj.id
                if routing_obj.bom_id.type == 'normal':
                    res['picking_type_ids'] = [(6, 0, [stock_type_obj[len(stock_type_obj) - 1].id])]
        elif not res.get('picking_type_ids'):
            res['picking_type_ids'] = [(6, 0, [stock_type_obj.ids])]
        return res
