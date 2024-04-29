from odoo import models, fields, api


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

    state = fields.Selection(selection_add=[('quality_check', 'Quality Check')])
    show_quality_check_btn = fields.Boolean(default=False, compute='_compute_show_quality_check_btn')
    # show_quality_check_btn = fields.Boolean(default=False)

    show_qa_check = fields.Integer(default=0)

    qa_check_product_ids = fields.Many2many('product.product', string="QA Checking Products",
                                            # compute='_compute_qa_check_products',
                                            help="List of Products used in the Quality Check")
    qa_check_point_name = fields.Char()

    @api.depends('state')
    def _compute_show_qa_check(self):
        self.ensure_one()
        qa_control_lists = self.env['elw.quality.point'].search([])
        self.show_qa_check = 0
        quality_check_product_ids = []
        # get all products in the delivery order
        delivery_product_ids = []
        picking_obj = self.filtered(lambda p: p.state == 'assigned')  # assigned = Ready
        for move in picking_obj.move_ids:
            delivery_product_ids.append(move.product_id.id)
        print("=========delivery_product_ids", delivery_product_ids)

        if len(qa_control_lists) and self.picking_type_id.id is not None:
            # qa_check_ids is a many2many field
            for qa_control_list in qa_control_lists:
                #  first check if picking_type_id is found in qa check point picking_type_ids
                if self.picking_type_id.id in qa_control_list.picking_type_ids.ids:  # picking_type_ids.ids : [1,2]
                    qa_product_ids_obj = self.env['elw.quality.point'].browse(qa_control_list.id)
                    print("elw.quality.point id, qa_product_ids, self.picking_type_id ========", qa_control_list.id,
                          qa_product_ids_obj.product_ids.ids, self.picking_type_id)
                    # then check if each qa_product_id is found in delivery_product_ids
                    for qa_product_id in qa_product_ids_obj.product_ids.ids:
                        print("qa_product_id ========", qa_product_id)
                        if qa_product_id in delivery_product_ids:
                            # self.show_qa_check = 1
                            self.state = 'quality_check'
                        #     quality_check_product_ids.append(qa_product_id)
                        #     print("-----------", quality_check_product_ids)
                        #     rec.qa_check_product_ids = rec.env['product.product'].browse(
                        #         quality_check_product_ids)

    @api.depends('state', 'move_ids.product_id', 'picking_type_id')
    def _compute_qa_check_products(self):
        for pro in self:
            pro.qa_check_product_ids = self.env['product.product'].browse([5, 6])
            print("-----------", self.qa_check_product_ids)

    @api.depends('state', 'move_ids.product_id', 'picking_type_id')
    def _compute_show_quality_check_btn(self):
        """
        This function returns qa_check_product_ids that display the pending quality check products
        among the products in the delivery order. If the pending quality check products and delivery types
        are matched those the quality check points view, Btn "Quality Check" is visible and the pending
        quality check products are shown.
        """
        # for rec in self:
        #     picking_obj = rec.filtered(lambda p: p.state == 'assigned')  # assigned = Ready
        #     if picking_obj:
        #         # rec.show_quality_check_btn = True
        #         print("rec.show_quality_check_btn", rec.show_quality_check_btn)
        qa_checkpoint_lists = self.env['elw.quality.point'].search([])
        for rec in self:
            rec.show_quality_check_btn = False
            quality_check_product_ids = []
            # get all products in the delivery order
            delivery_product_ids = []
            picking_obj = rec.filtered(lambda p: p.state == 'assigned')  # assigned = Ready
            for move in picking_obj.move_ids:
                delivery_product_ids.append(move.product_id.id)
            print("=========delivery_product_ids", delivery_product_ids)

            if len(qa_checkpoint_lists) and rec.picking_type_id.id is not None:
                # qa_check_ids is a many2many field
                for qa_checkpoint_list in qa_checkpoint_lists:
                    #  first check if picking_type_id is found in picking_type_ids of elw.quality.point
                    if rec.picking_type_id.id in qa_checkpoint_list.picking_type_ids.ids:  # picking_type_ids.ids : [1,2]
                        qa_product_ids_obj = rec.env['elw.quality.point'].browse(qa_checkpoint_list.id)
                        print("qa_product_ids ========", qa_product_ids_obj.product_ids.ids, qa_checkpoint_list.id, qa_checkpoint_list.name)
                        # then check if each qa_product_id of elw.quality.point is found in delivery_product_ids
                        for qa_product_id in qa_product_ids_obj.product_ids.ids:
                            print("qa_product_id rec.show_quality_check_btn ========", qa_product_id, rec.show_quality_check_btn)
                            if qa_product_id in delivery_product_ids:
                                rec.show_quality_check_btn = True
                                # rec.state = 'quality_check'
                                quality_check_product_ids.append(qa_product_id)
                                print("quality_check_product_ids-----------", quality_check_product_ids)
        #                 item.qa_check_product_ids = item.env['product.product'].browse(
        #                     quality_check_product_ids)

    def button_quality_check(self):
        return

    def button_eval(self):
        self._compute_show_quality_check_btn()
