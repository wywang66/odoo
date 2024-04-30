from odoo import models, fields, api, _


# https://www.odoo.com/forum/help-1/pass-a-many2one-field-from-purchase-module-to-inventory-module-249828


class StockMove(models.Model):
    _inherit = "stock.move"

    # 'stock.move.line' defines picking_id picking_id = fields.Many2one('stock.picking', 'Transfer',)
    # 'stock.picking' defines purchase_id = fields.Many2one('purchase.order', related='move_ids.purchase_line_id.order_id',)
    # \addons\product\models\product_template.py 'product.template' defines 
    # categ_id = fields.Many2one('product.category', 'Product Category', related = 'picking_id.purchase_id.categ_id', required=True)
    # below works too
    categ_id = fields.Many2one('product.category', 'Product Category', related='product_id.categ_id', required=True)


class Picking(models.Model):
    _inherit = "stock.picking"

    # Seen in categ_id = technical|Fields|inherit stock picking
    # categ_id = fields.Many2one('product.category', 'Product Category', related = 'purchase_id.categ_id',)
    # below works too
    categ_id = fields.Many2one('product.category', 'Product Category', related='product_id.categ_id', store=True)
    # to do, delete this field when using a new db

    # may delete 'state'
    state = fields.Selection(selection_add=[('quality_check', 'Quality Check')])

    show_quality_check_btn = fields.Boolean(default=False, compute='_compute_show_quality_check_btn')

    # picking_id is 1st defined in stock.move and define in elw.quality.check
    check_ids = fields.Many2many('elw.quality.check', 'picking_id',string="Checks")
    # current_check_id = fields.Many2many('elw.quality.check', 'picking_id', string="Checks")

    # can be deleted
    show_qa_check = fields.Integer(default=0)

    # can be hidden
    qa_check_product_ids = fields.Many2many('product.product', string="QA Checking Products",
                                            # compute='_compute_qa_check_products',
                                            help="List of Products used in the Quality Check")
    # can be deleted
    qa_check_point_name = fields.Char()

    # The error cannot duplicate now. Do not know the root cause of the issue.
    # missed this "# rec.show_quality_check_btn = False"
    # https://www.odoo.com/forum/help-1/odoo-17-uncaught-promise-an-error-occured-in-the-owl-lifecycle-see-this-error-s-cause-property-251142
    @api.depends('state', 'move_ids.product_id', 'picking_type_id')
    def _compute_show_quality_check_btn(self):
        """
        This function returns qa_check_product_ids that display the pending quality check products
        among the products in the delivery order. If the pending quality check products and delivery types
        are matched those the quality check points view, Btn "Quality Check" is visible and the pending
        quality check products are shown.
        """
        qa_checkpoint_lists = self.env['elw.quality.point'].search([])
        for rec in self:
            rec.show_quality_check_btn = False
            vals = {}
            # get all products in the delivery order
            delivery_product_ids = []
            picking_obj = rec.filtered(lambda p: p.state == 'assigned')  # assigned = Ready
            for move in picking_obj.move_ids:
                delivery_product_ids.append(move.product_id.id)
            # print("=========delivery_product_ids", delivery_product_ids)

            if len(qa_checkpoint_lists) and rec.picking_type_id.id is not None:
                # qa_check_ids is a many2many field
                for qa_checkpoint_list in qa_checkpoint_lists:
                    #  first check if picking_type_id is found in picking_type_ids of elw.quality.point
                    if rec.picking_type_id.id in qa_checkpoint_list.picking_type_ids.ids:  # picking_type_ids.ids : [1,2]
                        qa_product_ids_obj = rec.env['elw.quality.point'].browse(qa_checkpoint_list.id)
                        # print("qa_product_ids ========", qa_product_ids_obj.product_ids.ids, qa_checkpoint_list.id,
                        #       qa_checkpoint_list.name)
                        # then check if each qa_product_id of elw.quality.point is found in delivery_product_ids
                        for qa_product_id in qa_product_ids_obj.product_ids.ids:
                            # print("qa_product_id rec.show_quality_check_btn ========", qa_product_id,
                            #       rec.show_quality_check_btn, qa_product_ids_obj.id, qa_product_ids_obj.name,
                            #       rec.picking_type_id.id, rec.picking_type_id.name)
                            if qa_product_id in delivery_product_ids:
                                rec.show_quality_check_btn = True
                                # rec.state = 'quality_check'
                                vals['product_id'] = qa_product_id
                                vals['point_id'] = qa_product_ids_obj.id
                                vals['picking_id'] = rec.picking_type_id.id
                                vals['quality_state'] = 'none'
                                vals['partner_id'] = rec.partner_id.id
                                print("Found: qa_product_id, partner_id----------", qa_product_id, rec.partner_id)
                                self._create_qa_check(vals)

    # Create a record in quality.check
    def _create_qa_check(self, vals):
        self.ensure_one()
        qa_check_rec = self.env['elw.quality.check'].create(vals)
        # print("qa_check_rec--------", qa_check_rec)

    # call quality check wizard form
    @api.depends('picking_type_id')
    def action_quality_check(self):
        # qa_check_obj = self.env['elw.quality.check']
        action = self.env.ref('elw_quality.qa_quality_check_wizard_action_window').read()[0]
        # print("action ------", action)  # wo 'read()[0]' ir.actions.act_window(445,)
        # print("action ------", action)  # w 'read()[0]' {'id': 445, 'name': 'Quality Check', 'type': 'ir.actions.act_window', 'xml_id':
        # print("self.check_ids", self.check_ids) # no data self.check_ids elw.quality.check()
        return {
            'name': _('Quality Check'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'elw.quality.check.wizard',
            'view_type': 'form',
            # 'domain': [('check_ids', '=', self.check_ids)],
            # 'views': [(view.id, 'form')],
            # 'view_id': view.id,
            'target': 'new',
            # 'res_id': appointment_rec.id,
            # 'context': dict(
            #     self.env.context,
            # ),
        }

    def button_eval(self):
        self._compute_show_quality_check_btn()
