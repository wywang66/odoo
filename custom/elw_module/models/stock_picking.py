from odoo import models, fields, api, _, Command
from odoo.exceptions import ValidationError, RedirectWarning, UserError


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

    qa_check_product_ids = fields.Many2many('product.product', string="QA Checking Products",
                                            compute='_compute_qa_check_product_ids',
                                            help="List of Quality-Check products", store=True)

    quality_alert_ids = fields.One2many('elw.quality.alert', 'picking_id', string="Alerts", store=True)
    quality_alert_count = fields.Integer(string="Quality Alert Count", compute="_compute_quality_alert_count")
    quality_alert_open_count = fields.Integer(string="Quality Alert Open Count", compute="_compute_quality_alert_count")
    is_all_quality_fails_resolved = fields.Boolean(compute="_compute_is_all_quality_fails_resolved")

    quality_check_fail = fields.Boolean(string="Quality Check Fail", compute="_compute_quality_check_fail")
    quality_state = fields.Selection([('none', 'To Do'), ('pass', 'Passed'), ('fail', 'Failed')], )
    quality_check_ids = fields.One2many('elw.quality.check', 'picking_id', string="Quality Status", store=True)
    quality_check_count = fields.Integer(string="Check Count", compute="_compute_quality_check_count", default=0)
    has_lot_tracking = fields.Boolean(string='has Lot tracking?', default=False)

    @api.depends('quality_check_ids')
    def _compute_quality_check_count(self):
        for rec in self:
            rec.quality_check_count = len(rec.quality_check_ids)
            # print('rec.quality_check_count ', len(rec.quality_check_ids))

    @api.depends('quality_check_ids')
    def _compute_is_all_quality_fails_resolved(self):
        for rec in self:
            if rec.quality_check_ids:
                rec.is_all_quality_fails_resolved = False
                quality_result_list = [res.alert_result for res in
                                       rec.quality_check_ids] if rec.quality_check_ids else []
                # print("quality_result_list .........", quality_result_list)
                # returns True if at least one element in the iterable (such as a list, tuple, or set) is True.
                # False if ['Passed', 'Unsolved', '']
                if '' in quality_result_list or 'Unsolved' in quality_result_list:
                    rec.is_all_quality_fails_resolved = False
                elif all(res == 'Solved' or 'Passed' for res in quality_result_list):
                    rec.is_all_quality_fails_resolved = True
            else:
                rec.is_all_quality_fails_resolved = False

    @api.depends('quality_alert_ids')
    def _compute_quality_alert_count(self):
        for rec in self:
            # list.quality_alert_ids.id = False if no quality_alert_ids
            if rec.quality_alert_ids.ids:
                rec.quality_alert_count = len(rec.quality_alert_ids)
                rec.quality_alert_open_count = len(
                    rec.quality_alert_ids.filtered(lambda st: st.stage_id.id != 4))
                # print("rec.quality_alert_open_count .........", rec.quality_alert_open_count)
            else:
                rec.quality_alert_count = 0
                rec.quality_alert_open_count = -1

    # logic: if 'none' in quality_state_list: quality_state = 'none'
    # logic: if 'fail' in all quality_state_list: quality_state = 'fail', quality_check_fail = True
    # logic: if 'pass' in all quality_state_list: quality_state = 'pass', quality_check_fail = False
    # logic: if 'fail' and 'pass' quality_state_list: quality_state = 'fail', quality_check_fail = True
    # loop over the quality_check_ids, True - all fail
    @api.depends('quality_check_ids')
    def _compute_quality_check_fail(self):
        for rec in self:
            if rec.quality_check_ids:
                quality_state_list = [check.quality_state for check in
                                      rec.quality_check_ids] if rec.quality_check_ids else []
                # print("quality_state_list=========", quality_state_list)
                if 'none' in quality_state_list:
                    rec.quality_state = 'none'
                    rec.quality_check_fail = False
                elif all(state == 'fail' for state in quality_state_list):
                    rec.quality_state = 'fail'
                    rec.quality_check_fail = True
                elif all(state == 'pass' for state in quality_state_list):
                    rec.quality_state = 'pass'
                    rec.quality_check_fail = False
                else:
                    rec.quality_state = 'fail'
                    rec.quality_check_fail = True
            else:
                rec.quality_check_fail = False

    @api.depends('move_ids.product_id', 'picking_type_id')
    def _compute_qa_check_product_ids(self):
        """
        This function returns qa_check_product_ids that display the pending quality check products
        among the products in the delivery order. at ththe e same time, It creates record for 'quality.check' model.
        If the pending quality check products and delivery types
        are matched those the quality check points view, Btn "Quality Check" is visible and the pending
        quality check products are shown.
        """
        qa_checkpoint_lists = self.env['elw.quality.point'].sudo().search([])
        for rec in self:
            rec.qa_check_product_ids = None
            vals = {}
            qa_check_product_ids_buf = []  # product_ids.ids
            qa_check_point_ids_buf = []
            qa_product_tracking_buf = []
            # get all products in the delivery order
            delivery_product_ids = []
            picking_obj = rec.filtered(lambda p: p.state == 'assigned')  # assigned = Ready
            for move in picking_obj.move_ids:
                delivery_product_ids.append(move.product_id.id)
            # print("=========delivery_product_ids", delivery_product_ids)

            if len(qa_checkpoint_lists) and rec.picking_type_id.id is not None:
                for qa_checkpoint_list in qa_checkpoint_lists:
                    #  first check if picking_type_id is found in picking_type_ids of elw.quality.point
                    if rec.picking_type_id.id in qa_checkpoint_list.picking_type_ids.ids:  # picking_type_ids.ids : [1,2]
                        qa_product_ids_obj = rec.env['elw.quality.point'].sudo().browse(qa_checkpoint_list.id)
                        # print("qa_product_ids ========", qa_product_ids_obj.product_ids.ids, qa_checkpoint_list.id,
                        #       qa_checkpoint_list.name)
                        # then check if each qa_product_id of elw.quality.point is found in delivery_product_ids
                        for qa_product_id in qa_product_ids_obj.product_ids.ids:
                            # print("qa_product_id ========", qa_product_id,
                            #        qa_product_ids_obj.id, qa_product_ids_obj.name,
                            #       rec.picking_type_id.id, rec.picking_type_id.name)
                            if qa_product_id in delivery_product_ids:
                                vals['picking_id'] = rec.id
                                vals['quality_state'] = 'none'
                                vals['partner_id'] = rec.partner_id.id
                                vals['product_id'] = qa_product_id  #
                                vals['point_id'] = qa_product_ids_obj.id
                                # create quality.check record for no tracking product
                                if self.env['product.product'].browse(qa_product_id).tracking == 'none':
                                    # print("vals ", vals)#
                                    # special cmd to create child record. must use []
                                    rec.quality_check_ids = [Command.create(vals)]
                                    # print("Command.create(vals) ", Command.create(vals)) #(<Command.CREATE: 0>, 0, {'picking_id': 40, 'quality_state': 'none', 'partner_id': 26, 'product_id': 19, 'point_id': 4})
                                else:
                                    rec.has_lot_tracking = True
                                qa_product_tracking_buf.append(self.env['product.product'].browse(qa_product_id).tracking)
                                qa_check_product_ids_buf.append(qa_product_id)
                                qa_check_point_ids_buf.append(qa_product_ids_obj.id)
                                # print("Found: qa_product_id, partner_id, rec.picking_type_id.id----------",
                                #       qa_product_id, rec.partner_id, rec.id, rec.name, rec.picking_type_id.id,
                                #       rec.picking_type_id.name)
                                # len(qa_check_product_ids) can be >1
                                vals['product_id'] = qa_check_product_ids_buf
                                vals['point_id'] = qa_check_point_ids_buf
                                vals['tracking'] = qa_product_tracking_buf

                rec.qa_check_product_ids = self.env['product.product'].sudo().browse(qa_check_product_ids_buf)
                return vals

    def action_create_qa_check_record_with_tracking_product(self):
        self.ensure_one()
        vals = self._compute_qa_check_product_ids()
        print('vals in action create record', vals)
        pass

    def _create_qa_check_popup_wizard_record(self, vals):
        self.ensure_one()
        qa_check_popup_wizard_rec = self.env['elw.quality.check.popup.wizard'].create(vals)
        # print("created qa_check_popup_wizard rec--------", qa_check_popup_wizard_rec, qa_check_popup_wizard_rec.id,
        #       qa_check_popup_wizard_rec.name)
        return qa_check_popup_wizard_rec

    @api.depends('qa_check_product_ids', 'quality_check_ids', 'partner_id', 'quality_state')
    def _fill_in_vals_popup_after_popup(self):
        self.ensure_one()
        vals_popup = {'product_ids': self.qa_check_product_ids,
                      'check_ids': self.quality_check_ids,
                      'quality_state': self.quality_state,
                      'partner_id': self.partner_id.id,
                      # 'quality_alert_ids': self.quality_alert_ids,
                      # 'quality_alert_open_count': self.quality_alert_open_count,
                      'is_all_quality_fails_resolved': self.is_all_quality_fails_resolved,
                      }
        return vals_popup

    @api.depends('quality_check_ids', 'quality_state', 'qa_check_product_ids', 'is_all_quality_fails_resolved')
    def button_validate(self):
        self.ensure_one()
        # after 1st popup window
        if self.quality_check_ids and not self.is_all_quality_fails_resolved:
            # Remind the user to enter lot ID if the product is set to track lot id
            # entering 2 lot_name in purchase order creates 2 line
            for line in self.move_line_ids:
                # print("line.product_id", line.product_id.name, line.product_id.tracking, line.lot_name, line.lot_id.id, line.lot_id)
                if line.product_id in self.qa_check_product_ids and line.product_id.tracking != 'none' and not (
                        line.lot_name or line.lot_id):
                    raise UserError(
                        _("Please enter lot information for %s before proceed to Quality Check",
                          line.product_id.display_name))
                    # else:
                    #     print("line.product_id", line.lot_name, line.lot_id)

            vals_popup = self._fill_in_vals_popup_after_popup()
            # print("vals_popup ", vals_popup)
            qa_check_popup_wizard = self._create_qa_check_popup_wizard_record(vals_popup)

            show_name = 'Status of Quality Check on Delivery: ' + self.name
            return {
                'name': show_name,
                'res_model': 'elw.quality.check.popup.wizard',
                'res_id': qa_check_popup_wizard.id,
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': self.env.ref('elw_quality.elw_quality_check_popup_form_view').id,
                'target': 'new',
            }

        else:
            return super(Picking, self).button_validate()

    @api.depends('quality_check_ids.ids')
    def action_open_quality_check_picking(self):
        return {
            'name': _('Quality Check'),
            'res_model': 'elw.quality.check',
            # 'res_id': qa_check_rec.id,  # open the corresponding form
            'domain': [('id', 'in', self.quality_check_ids.ids)],
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'target': 'current',
        }

    @api.depends('quality_alert_ids.ids')
    def open_quality_alert_picking(self):
        return {
            'name': _('Quality Alerts'),
            'res_model': 'elw.quality.alert',
            'domain': [('id', 'in', self.quality_alert_ids.ids)],
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            # commented the following as it will show tree, and form views
            # 'view_id': self.env.ref('elw_quality.elw_quality_alert_form_view').id,
            'target': 'current',
        }
