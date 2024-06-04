from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, RedirectWarning


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
    # state = fields.Selection(selection_add=[('quality_check', 'Quality Check')])

    # picking_id is 1st defined in stock.move and define in elw.quality.check
    check_ids = fields.Many2many('elw.quality.check', 'picking_id', string="Quality Checks References", store=True)

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
    quality_check_count = fields.Integer(string="Check Count", compute="_compute_quality_check_count")

    @api.depends('check_ids')
    def _compute_quality_check_count(self):
        for rec in self:
            if rec.check_ids.ids:
                rec.quality_check_count = sum(1 for check in rec.check_ids)
            else:
                rec.quality_check_count = 0

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
    # loop over the check_ids, True - all fail
    @api.depends('check_ids')
    def _compute_quality_check_fail(self):
        for rec in self:
            if rec.check_ids:
                quality_state_list = [check.quality_state for check in rec.check_ids] if rec.check_ids else []
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

    # @api.onchange('check_id')
    # def onchange_check_id(self):
    #     if self.check_id:
    #         print("2 stock.picking onchange trigger", self.check_id)
    #         if self.check_id.quality_state == 'fail':
    #             self.quality_check_fail = True
    #             print("3 stock.picking onchange trigger", self.check_id.quality_state)
    #         else:
    #             print("3 stock.picking onchange trigger", self.check_id.quality_state)
    #             self.quality_check_fail = False

    @api.depends('move_ids.product_id', 'picking_type_id')
    def _compute_qa_check_product_ids(self):
        """
        This function returns qa_check_product_ids that display the pending quality check products
        among the products in the delivery order. If the pending quality check products and delivery types
        are matched those the quality check points view, Btn "Quality Check" is visible and the pending
        quality check products are shown. It does not create record for quality.check.
        """
        qa_checkpoint_lists = self.env['elw.quality.point'].sudo().search([])
        for rec in self:
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
                                qa_check_product_ids_buf.append(qa_product_id)
                                qa_check_point_ids_buf.append(qa_product_ids_obj.id)
                                # print("Found: qa_product_id, partner_id, rec.picking_type_id.id----------",
                                #       qa_product_id, rec.partner_id, rec.id, rec.name, rec.picking_type_id.id,
                                #       rec.picking_type_id.name)
                                # len(qa_check_product_ids) can be >1
                                vals['product_id'] = qa_check_product_ids_buf
                                vals['point_id'] = qa_check_point_ids_buf

                rec.qa_check_product_ids = self.env['product.product'].sudo().browse(qa_check_product_ids_buf)
                return vals

    # parse vals and return result list consisting of new_val elements
    @api.depends('qa_check_product_ids')
    def _parse_vals(self):
        vals = self._compute_qa_check_product_ids()
        results = []
        # print("vals-------", vals)#vals------- {'picking_id': 24, 'quality_state': 'none', 'partner_id': 47, 'product_id': [5, 31], 'point_id': [2, 1]}
        if vals is None:
            raise ValidationError(_("Sorry, No Quality Control Point found for this product! Please create it first! "))

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
        # print("created qa_check_rec--------", qa_check_rec, qa_check_rec.id, qa_check_rec.name)
        return qa_check_rec

    def _create_qa_check_popup_wizard_record(self, vals):
        self.ensure_one()
        qa_check_popup_wizard_rec = self.env['elw.quality.check.popup.wizard'].create(vals)
        # print("created qa_check_popup_wizard rec--------", qa_check_popup_wizard_rec, qa_check_popup_wizard_rec.id,
        #       qa_check_popup_wizard_rec.name)
        return qa_check_popup_wizard_rec

    @api.depends('qa_check_product_ids', 'check_ids', 'partner_id', 'quality_state')
    def _fill_in_vals_popup_after_popup(self):
        self.ensure_one()
        vals_popup = {'product_ids': self.qa_check_product_ids,
                      'check_ids': self.check_ids,
                      'quality_state': self.quality_state,
                      'partner_id': self.partner_id.id,
                      # 'quality_alert_ids': self.quality_alert_ids,
                      # 'quality_alert_open_count': self.quality_alert_open_count,
                      'is_all_quality_fails_resolved': self.is_all_quality_fails_resolved,
                      }
        return vals_popup

    @api.model
    def find_team_id(self):
        team_obj = self.env['elw.quality.team']
        team_search = team_obj.sudo().search([])
        if len(team_search):
            return team_search[0].id
        else:
            raise ValidationError(_("Sorry, Please Create a Quality Team First at 'Configurations|Quality Teams'! "))

    # def find_lot_id(self):
    #     lot_obj = self.env['stock.lot']
    #     lot_search = lot_obj.sudo().search([])
    #     if len(lot_search):
    #         return lot_search[0].id
    #     else:
    #         raise ValidationError(_("Sorry, Please Create a Lot ID First at 'Products|Lot/Serial Numbers'! "))

    @api.depends('check_ids', 'qa_check_product_ids')
    def action_create_quality_check(self):
        self.ensure_one()
        # avoid creating duplicated records
        # first time condition do, create records and popup
        if not self.check_ids and self.qa_check_product_ids:
            vals_popup = {'product_ids': [], 'check_ids': [], 'quality_state': 'none', 'partner_id': ''}
            results = self._parse_vals()
            # print("---------", results)

            # create the elw.quality.check records, and assign vals_popup
            for val in results:
                # print("val =========", val.get('product_id'), val.get('team_id'))#val ========= 31 None
                team_id = self.find_team_id()
                val['team_id'] = team_id
                # print("val =========", val)
                qa_check_rec = self._create_qa_check_record(val)
                vals_popup['product_ids'].append(val['product_id'])
                vals_popup['check_ids'].append(qa_check_rec.id)
                vals_popup['quality_state'] = 'none'
                vals_popup['partner_id'] = (val['partner_id'])

            self.check_ids = self.env['elw.quality.check'].sudo().browse(vals_popup['check_ids'])
            qa_check_popup_wizard = self._create_qa_check_popup_wizard_record(vals_popup)

            # print("self.check_ids, =========", self.check_ids, self.check_ids.id)
            # print("val popup =========", qa_check_popup_wizard, qa_check_popup_wizard.id, qa_check_popup_wizard.name)
            show_name = 'Created Quality Check on Delivery: ' + self.name
            return {
                # 'name': _('Quality Check'),
                'name': show_name,
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'elw.quality.check.popup.wizard',
                'view_type': 'form',
                'res_id': qa_check_popup_wizard.id,
                # 'domain': [('check_ids', '=', self.check_ids)],
                # 'views': [(view.id, 'form')],
                # 'view_id': view.id,
                'target': 'new',
                'context': dict(
                    self.env.context,
                ),
            }

    # display the created quality.check record
    @api.depends('check_ids')
    def action_quality_check(self):
        self.ensure_one()
        if self.check_ids:
            vals_popup = self._fill_in_vals_popup_after_popup()

            # print("action_quality_check vals_popup ", vals_popup)
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
            raise ValidationError(_("Sorry, Please Click 'Quality Check' First! "))

    @api.depends('check_ids', 'quality_state', 'qa_check_product_ids', 'is_all_quality_fails_resolved')
    def button_validate(self):
        self.ensure_one()
        # print("trigger here-----self.quality_alert_open_count----", self.quality_alert_open_count)
        if not self.check_ids and self.qa_check_product_ids:  # before getting the 1st popup
            raise ValidationError(
                _("Sorry, Quality Records have not been created! Please Click 'Create QA Check Record'."))
        # after 1st popup window
        elif self.check_ids and not self.is_all_quality_fails_resolved:
            vals_popup = self._fill_in_vals_popup_after_popup()
            # print("vals_popup ", vals_popup)
            qa_check_popup_wizard = self._create_qa_check_popup_wizard_record(vals_popup)
            # print("self.check_ids.quality_state", self.quality_state)  # self.check_ids.quality_state pass

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

    # display a message with product_ids, check_ids do_alert, to reminder the user to create QA alert
    @api.depends('check_ids', 'quality_check_fail')
    def do_alert(self):
        self.ensure_one()
        if self.check_ids and self.quality_check_fail:
            vals_popup = self._fill_in_vals_popup_after_popup()
            print("do_alert vals_popup ", vals_popup)
            qa_check_popup_wizard = self._create_qa_check_popup_wizard_record(vals_popup)
            # print("self.check_ids.quality_state", self.quality_state)  # self.check_ids.quality_state pass

            show_name = 'Create Quality Alert. Status of Quality Check on Delivery: ' + self.name
            return {
                'name': show_name,
                'res_model': 'elw.quality.check.popup.wizard',
                'res_id': qa_check_popup_wizard.id,
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': self.env.ref('elw_quality.elw_quality_check_popup_form_view').id,
                'target': 'new',
            }

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
