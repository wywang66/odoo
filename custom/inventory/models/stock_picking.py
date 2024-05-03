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

    show_quality_check_btn = fields.Boolean(default=False)
    # show_quality_check_btn = fields.Boolean(default=False, compute='_compute_show_quality_check_btn')

    # picking_id is 1st defined in stock.move and define in elw.quality.check
    check_ids = fields.Many2many('elw.quality.check', 'picking_id', string="Checks")
    qa_check_product_ids = fields.Many2many('product.product', string="QA Checking Products",
                                            compute='_compute_qa_check_product_ids',
                                            help="List of Quality-Check products")

    @api.depends('state', 'move_ids.product_id', 'picking_type_id')
    def _compute_qa_check_product_ids(self):
        """
        This function returns qa_check_product_ids that display the pending quality check products
        among the products in the delivery order. If the pending quality check products and delivery types
        are matched those the quality check points view, Btn "Quality Check" is visible and the pending
        quality check products are shown. It does not create record for quality.check.
        """
        qa_checkpoint_lists = self.env['elw.quality.point'].search([])
        for rec in self:
            rec.show_quality_check_btn = False
            rec.qa_check_product_ids = None
            vals = {}
            qa_check_product_ids_buf = []  # product_ids.ids
            qa_check_point_ids_buf = []
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
                                vals['picking_id'] = rec.id
                                vals['quality_state'] = 'none'
                                vals['partner_id'] = rec.partner_id.id
                                qa_check_product_ids_buf.append(qa_product_id)
                                qa_check_point_ids_buf.append(qa_product_ids_obj.id)
                                # print("Found: qa_product_id, partner_id, rec.picking_type_id.id----------",
                                #       qa_product_id, rec.partner_id, rec.id, rec.name, rec.picking_type_id.id,
                                #       rec.picking_type_id.name)
                                # len(qa_check_product_ids) can be >1
                                vals['product_id'] = qa_check_product_ids_buf
                                vals['point_id'] = qa_check_point_ids_buf

                rec.qa_check_product_ids = self.env['product.product'].browse(qa_check_product_ids_buf)
                return vals

    # parse vals and return result list consisting of new_val elements
    def _parse_vals(self):
        vals = self._compute_qa_check_product_ids()
        results = []
        # print("vals-------", vals)#vals------- {'picking_id': 24, 'quality_state': 'none', 'partner_id': 47, 'product_id': [5, 31], 'point_id': [2, 1]}
        for i in range(max(len(vals['product_id']), len(vals['point_id']))):
            new_val = {}
            for key, value in vals.items():
                if isinstance(value, list):
                    new_val[key] = value[i] if i < len(value) else None
                else:
                    new_val[key] = value
            results.append(new_val)
        return results

    # Create a record in quality.check
    def _create_qa_check_record(self, vals):
        self.ensure_one()
        qa_check_rec = self.env['elw.quality.check'].create(vals)
        print("created qa_check_rec--------", qa_check_rec, qa_check_rec.id, qa_check_rec.name)
        return qa_check_rec

    def _create_qa_check_wizard_record(self, vals):
        self.ensure_one()
        qa_check_wizard_rec = self.env['elw.quality.check.wizard'].create(vals)
        print("created qa_check_rec wizard--------", qa_check_wizard_rec, qa_check_wizard_rec.id)
        return qa_check_wizard_rec

    def _create_qa_check_popup_record(self, vals):
        self.ensure_one()
        qa_check_popup_rec = self.env['elw.quality.check.popup'].create(vals)
        print("created qa_check_rec--------", qa_check_popup_rec, qa_check_popup_rec.id, qa_check_popup_rec.name)
        return qa_check_popup_rec

    # call quality check wizard form
    @api.depends('picking_type_id')
    def action_quality_check(self):
        # vals = self._get_vals_then_create_qa_check_records()
        results = self._parse_vals()
        print("---------", results)

        # create the elw.quality.check records
        # assign vals_wizard
        # vals_wizard = {'product_ids': [], 'check_ids': [], 'quality_state': 'none', 'picking_id': ''}
        vals_wizard = {}
        vals_popup = {'product_ids': [], 'check_ids': [], 'quality_state': 'none', 'partner_id': ''}
        for val in results:
            # print("val =========", val)
            qa_check_rec = self._create_qa_check_record(val)

            # # vals_wizard['product_ids'].append(val['product_id'])
            # vals_wizard['product_id'] = (val['product_id'])
            # # vals_wizard['check_ids'].append(qa_check_rec.id)
            # vals_wizard['picking_id'] = val['picking_id']

            vals_popup['product_ids'].append(val['product_id'])
            vals_popup['check_ids'].append(qa_check_rec.id)
            vals_popup['quality_state'] = 'none'
            vals_popup['partner_id'] = (val['partner_id'])

            # print("val wiz =========", vals_wizard)
            # qa_check_wizard_rec = self._create_qa_check_wizard_record(vals_wizard)

        print("val popup =========", vals_popup)
        qa_check_popup = self._create_qa_check_popup_record(vals_popup)
        print("val popup =========", qa_check_popup, qa_check_popup.id, qa_check_popup.name)

            # below works. commented as it display one form
            # return {
            #     'name': _('Quality Check'),
            #     'res_model': 'elw.quality.check',
            #     'res_id': qa_check_rec.id,  # open the corresponding form
            #     'type': 'ir.actions.act_window',
            #     'view_mode': 'form',
            #     'view_id': self.env.ref('elw_quality.elw_quality_check_form_view').id,
            #     # 'view_id': self.env.ref('elw_quality.elw_quality_check_tree_view').id,
            #     'target': 'new',
            # }

        # action = self.env.ref('elw_quality.qa_quality_check_wizard_action_window').read()[0]
        # print("action ------", action)  # wo 'read()[0]' ir.actions.act_window(445,)
        # print("action ------", action)  # w 'read()[0]' {'id': 445, 'name': 'Quality Check', 'type': 'ir.actions.act_window', 'xml_id':
        # print("self.check_ids", self.check_ids) # no data self.check_ids elw.quality.check()
        show_name = 'Quality Check on Delivery: ' + self.name
        return {
            # 'name': _('Quality Check'),
            'name': show_name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'elw.quality.check.popup',
            'view_type': 'form',
            'res_id': qa_check_popup.id,
            # 'domain': [('check_ids', '=', self.check_ids)],
            # 'views': [(view.id, 'form')],
            # 'view_id': view.id,
            'target': 'new',

            'context': dict(
                self.env.context,
            ),
        }

    def button_eval(self):
        print("eval btn ------")

        # self._compute_qa_check_product_ids()
