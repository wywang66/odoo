from typing import Dict, List

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import json


class ElwQualityCheck(models.Model):
    _name = 'elw.quality.check'
    _inherit = ['mail.thread',
                'mail.activity.mixin',

                ]  # add a chatter
    _description = 'elw quality check'
    _order = 'id desc, name desc'

    name = fields.Char(
        string='Reference', default='New', copy=False, readonly=True)
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        readonly=True, required=True,
        help='The company is automatically set from your user preferences.')
    active = fields.Boolean(default=True)
    title = fields.Char("Title")
    point_id = fields.Many2one('elw.quality.point', string='Control Point ID', ondelete='cascade', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner', ondelete='cascade', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', required=True, store=True,
                                 domain="[('type', 'in', ['product', 'consu'])]", ondelete='cascade')
    picking_id = fields.Many2one('stock.picking', string='Picking', store=True, ondelete='set null')
    measure_on = fields.Selection(related='point_id.measure_on', string='Control per', store=True,
                                  help='Product = A quality check is requested per product.'
                                       ' Operation = One quality check is requested at the operation level.'
                                       ' Quantity = A quality check is requested for each new product quantity registered,'
                                       'with partial quantity checks also possible.')
    lot_ids = fields.Many2many('stock.lot', string='Lots/Serials', compute='_get_lot_name',
                               readonly=False, domain="[('product_id', '=', product_id)]", store=True)
    lot_name = fields.Char(string='Lots/Serials', compute='_get_lot_name', readonly=False, store=True)
    has_lot_id = fields.Boolean(string='Has Lot ids', compute="_compute_has_lot_id", store=True)
    #  this for doing check by pass inventory
    lot_info = fields.Char(string='Lot Info', store=True)
    picking_code = fields.Selection(related='picking_id.picking_type_id.code', readonly=True)
    user_id = fields.Many2one('res.users', string='Checked By', ondelete="cascade")
    test_type_id = fields.Many2one(related='point_id.test_type_id', string='Test Type', ondelete='Set NULL', store=True)
    team_id = fields.Many2one('elw.quality.team', string='Team', store=True, required=True, ondelete='cascade')
    control_date = fields.Date(string='Checked Date', default=fields.Date.context_today)
    quality_state = fields.Selection([('none', 'To Do'), ('pass', 'Passed'), ('fail', 'Failed')], required=True,
                                     default='none', string='Status', tracking=True)
    alert_count = fields.Integer(default=0, compute="_compute_alert_cnt", store=True)
    alert_ids = fields.One2many('elw.quality.alert', 'check_id', string="Alerts")
    alert_result = fields.Char(compute="_compute_alert_result", string='Quality Check Result', store=True)
    fail_and_not_alert_created = fields.Boolean(string='fail_and_not_alert_created',
                                                compute='_compute_fail_and_not_alert_created', store=True)
    picture = fields.Binary(string="Picture", store=True)
    copy_record_id = fields.Many2one('elw.quality.check', string='Duplicate Quality Check ref#', store=True)
    original_id = fields.Many2one('elw.quality.check', string="Original Ref#", store=True)
    # for notebook
    additional_note = fields.Text('Note')
    note = fields.Html('Instructions')
    measure_spec_ids = fields.One2many('elw.quality.measure.spec', 'point_id',
                                       readonly=False,
                                       compute="_compute_measured_spec", store=False)
    measure_data_count = fields.Integer("Measure Data Count", compute='_compute_measure_data_count', store=True)
    measure_data_ids = fields.One2many('elw.quality.measure.data', 'check_id', readonly=False,
                                       compute="", store=True)
    product_id_domain = fields.Char(compute="_compute_product_id_domain", store=True)

    @api.depends('has_lot_id', 'picking_id', 'picking_id.move_line_ids.lot_id', 'picking_id.move_line_ids.lot_name')
    def _get_lot_name(self):
        for rec in self:
            if rec.has_lot_id and rec.picking_id:
                stock_move_lines = self.env['stock.move.line'].sudo().search([('picking_id', '=', rec.picking_id.id)])
                # print('stock_move_lines', stock_move_lines, stock_move_lines.mapped('lot_id'),
                #       stock_move_lines.mapped('lot_name'))
                if not all(name == False for name in stock_move_lines.mapped('lot_name')):
                    # Get the lot names from the stock move lines, filtering out any non-string values (e.g.,False)
                    # print('stock_move_lines.mapped name', stock_move_lines.mapped('lot_name'))
                    lot_names = [line.lot_name for line in stock_move_lines if line.lot_name]
                    # print('lot_names', lot_names)
                    rec.lot_name = ', '.join(lot_names)
                elif len(stock_move_lines.mapped('lot_id').mapped('id')):
                    # print('stock_move_lines.mapped', stock_move_lines.mapped('lot_id').mapped('id'))
                    lot_ids = stock_move_lines.mapped('lot_id').ids
                    rec.lot_ids = self.env['stock.lot'].browse(lot_ids)
            # else:
            #     raise UserError(
            #         _('Not delivery and receipt order! Please provide Lot/Serial for %s .',
            #           rec.product_id.display_name))

    @api.depends('measure_data_ids', 'test_type_id')
    def _check_if_measure_data_ids_empty(self):
        for rec in self:
            if rec.test_type_id.id == 5 and not len(rec.measure_data_ids):
                raise ValidationError(_("Please fill in Measurement Data Tag."))

    @api.depends('test_type_id', 'point_id')
    def _compute_measured_spec(self):
        for rec in self:
            if rec.test_type_id.id == 5:
                data = self.env['elw.quality.measure.spec'].search([('point_id', '=', rec.point_id.id)])
                rec.measure_spec_ids = data
                # print("rec.measure_spec_ids---", rec.measure_spec_ids)
            else:
                rec.measure_spec_ids = None

    @api.depends('measure_data_ids.measured_value')
    def _compute_measure_data_count(self):
        for rec in self:
            rec.measure_data_count = self.env['elw.quality.measure.data'].search_count(
                [('check_id', '=', rec.id)])
            # print("rec.measure_data_count   : ", rec.measure_data_count)

    # if manually creating a qa check by selecting qa.point, make sure the product is in qa.point
    @api.constrains('product_id')
    def _check_if_product_in_quality_point(self):
        for rec in self:
            if rec.product_id.id not in rec.point_id.product_ids.ids:
                raise ValidationError(
                    _("Current product is not found in Control Point ID %s that has %s. Please reselect the product.",
                      rec.point_id.name, rec.point_id.product_ids.mapped('name')))

    # check if an alert is created on 'fail' record
    @api.depends('alert_ids', 'quality_state')
    def _compute_fail_and_not_alert_created(self):
        for rec in self:
            rec.fail_and_not_alert_created = True if rec.quality_state == 'fail' and not rec.alert_ids else False
            # print("----------", rec.fail_and_not_alert_created)

    # Check if this product has lot or serial
    @api.depends('product_id')
    def _compute_has_lot_id(self):
        for rec in self:
            rec.has_lot_id = rec.product_id.tracking != 'none'
            # print("rec.has_lot_id---------", rec.has_lot_id)

    @api.depends('alert_ids')
    def _compute_alert_cnt(self):
        alert_data = self.env['elw.quality.alert']._read_group([('check_id', 'in', self.ids)],
                                                               ['check_id'], ['__count'])
        # print('alert_data:', alert_data) # alert_data: [(elw.quality.check(3,), 1)]
        # dictionary comprehension to map the IDs to their corresponding counts
        mapped_data = {check.id: count for check, count in alert_data}
        #  defaulting to 0 if the check.id is not found in mapped_data.
        for check in self:
            check.alert_count = mapped_data.get(check.id, 0)

    @api.depends('alert_ids.stage_id', 'quality_state')
    def _compute_alert_result(self):
        for rec in self:
            if rec.quality_state == 'fail':
                rec.alert_result = 'Unsolved'
                alert_result_list = [alert_res.stage_id.name for alert_res in
                                     rec.alert_ids] if rec.quality_state == 'fail' else []
                # print("alert_result_list=========", alert_result_list)
                if len(alert_result_list):
                    if all(res == 'Solved' for res in alert_result_list):
                        rec.alert_result = 'Solved'
            elif rec.quality_state == 'pass':
                rec.alert_result = 'Passed'
            else:
                rec.alert_result = ''

    @api.model_create_multi
    def create(self, vals):
        for vals in vals:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.check.sequence')
            # print("before create vals", vals)
            rtn = super(ElwQualityCheck, self).create(vals)
        return rtn

    # #  no decorator needed
    def write(self, vals):
        # print("self.name, vals.get('name'), vals", self.name, vals.get('name'), vals) #QC00046 None {'quality_state': 'pass'}
        # IMPORTANT --- without 'not self.name', Reference keeps rolling
        if not self.name and not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.check.sequence')
        rtn = super(ElwQualityCheck, self).write(vals)
        return rtn

    def unlink_alert_ids(self):
        for alert_id in self.alert_ids:
            alert_id.write({
                'check_id': False,
                'picking_id': False,
                'product_id': self.product_id,
            })
            # print(self.env['elw.quality.alert'].browse(alert_id.id).read(['name','picking_id','check_id','product_id']))
            alert_id.unlink()

    def unlink(self):
        for rec in self:
            if rec.quality_state != 'none':
                raise ValidationError(
                    _("Can not delete the record that is not in 'To Do'. \nPlease cancel it to reset to 'To Do' state"))
            elif rec.picking_id:
                raise ValidationError(
                    _("Can not delete the record that has Deliveries/Receipts order. \nPlease cancel it to in Inventory"))
            elif len(rec.measure_data_ids) > 0:
                # unlink child's records
                rec.measure_data_ids.unlink()
            rec.unlink_alert_ids()
            return super(ElwQualityCheck, self).unlink()

    @api.depends('quality_state')
    def do_pass(self):
        self.ensure_one()
        if self.quality_state == 'none':
            self.quality_state = 'pass'

    @api.depends('quality_state')
    def do_cancel(self):
        self.ensure_one()
        if self.quality_state != 'none':
            self.quality_state = 'none'

    @api.depends('quality_state')
    def do_fail(self):
        self.ensure_one()
        if self.quality_state == 'none':
            self.quality_state = 'fail'

    @api.depends('quality_state', 'has_lot_id', 'original_id')
    def do_split_lot(self):
        # copy the record so users can split passed and failed lot on the product with lot id
        if self.has_lot_id:
            if self.quality_state == 'none':
                # keep one original_id
                if not self.original_id:
                    self.copy_record_id = self.copy({'original_id': self.id,})
                else:
                    self.copy_record_id = self.copy()
                if not self.copy_record_id:
                    raise ValidationError(_("Failed to duplicate the record %s", self.name))
            else:
                raise UserError(_("You can split the lot in 'To Do' state"))
        else:
            raise UserError(_("You can only split the lot if it has a lot ID"))

    def action_see_split_record(self):
        self.ensure_one()
        return {
            'name': _('Quality Check Split Record'),
            'res_model': 'elw.quality.check',
            'res_id': self.copy_record_id.id,  # open the corresponding form
            'domain': [('id', '=', self.copy_record_id)],
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'current',
        }

    def action_see_original_record(self):
        self.ensure_one()
        return {
            'name': _('Quality Check Original Record'),
            'res_model': 'elw.quality.check',
            'res_id': self.original_id.id,  # open the corresponding form
            # 'domain': [('id', '=', self.copy_record_id)],
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'current',
        }

    @api.depends('measure_data_ids')
    def do_measure(self):
        qa_measure_state = []
        measure_names = []
        if self.measure_data_ids:
            for line in self.measure_data_ids:
                if line.point_id.id != self.point_id.id:
                    raise ValidationError(
                        _("Selected Control Point Ref# %s does not match with the current: %s",
                          line.point_id.name, self.point_id.name))
                elif not line.measured_value:
                    raise ValidationError(
                        _("You have not updated Measured Value in %s",
                          line.measure_name))
                else:
                    qa_measure_state.append(line.within_tolerance)
                    measure_names.append(line.measure_name)
            # print("measure_names", measure_names, qa_measure_state)
            # check if the total measurement count id correct
            cnt = len(self.measure_spec_ids.ids)
            if cnt != len(self.measure_data_ids):
                raise ValidationError(
                    _("Selected %d measurement items, not matching with the %d items in Quality Control Point",
                      len(self.measure_data_ids), cnt))
            # check if any measure_name duplication
            elif len(measure_names) != len(set(measure_names)):
                raise ValidationError(
                    _("Duplicated Measure Name found !"))
            else:
                # print("qa_measure_state", qa_measure_state)
                if False in qa_measure_state:
                    self.quality_state = 'fail'
                else:
                    self.quality_state = 'pass'
        else:
            raise ValidationError(_("Please fill up the Measurement Data"))

    @api.depends('point_id', 'measure_spec_ids')
    def do_add_records(self):
        """
        This function first gets the matching measure_spec_ids by function _compute_measured_spec.
        It then creates measure.data records. Via spec_id, measure.data records are populated.
        So these records are popping up in quality.check Measurement Data Tag
        """
        self.ensure_one()
        for item in self.measure_spec_ids:
            # print("item", item) #item elw.quality.measure.spec(6,)
            vals = {
                'spec_id': item.id,
                'point_id': item.point_id.id,
                'check_id': self.id,
            }
            # print("vals----------", vals) #vals---------- {'spec_id': 6, 'point_id': 6, 'check_id': 23}
            data_obj = self.env['elw.quality.measure.data']
            data_obj.create(vals)

    @api.model
    def _create_qa_alert_record(self, vals):
        self.ensure_one()
        qa_alert_rec = self.env['elw.quality.alert'].create(vals)
        # print("created qa_alert_rec--------", qa_alert_rec, qa_alert_rec.id, qa_alert_rec.name)
        return qa_alert_rec

    def do_alert(self):
        self.ensure_one()
        # get vals to create a quality.alert record
        vals = {
            'product_id': self.product_id.id,
            'check_id': self.id,
            'picking_id': self.picking_id.id,
            'partner_id': self.partner_id.id,
            'team_id': self.team_id.id,
            'user_id': self.user_id.id,
            'lot_name': self.lot_name,
            'lot_info': self.lot_info,
        }
        # print("vals in quality.check---------", vals)
        qa_alert_rec = self._create_qa_alert_record(vals)
        return {
            'name': _('Quality Alert'),
            'res_model': 'elw.quality.alert',
            'res_id': qa_alert_rec.id,  # open the corresponding form
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('elw_quality.elw_quality_alert_form_view').id,
            # 'target': 'new',
        }

    def action_see_alerts(self):
        return self._get_action_view_see_alert(self.alert_ids)
        # Below works and return the matching tree view
        # print("self.alert_ids.id", self.alert_ids.id) #self.alert_ids.id 15
        # return {
        #     'name': _('Quality Alert'),
        #     'res_model': 'elw.quality.alert',
        #     'res_id': self.alert_ids.id,  # open the corresponding form
        #     # 'domain': [('id', '=', self.alert_ids.ids)],
        #     'type': 'ir.actions.act_window',
        #     'view_mode': 'form',
        #     # 'view_mode': 'tree,form',
        #     'target': 'current',
        # }

    def _get_action_view_see_alert(self, alerts):
        """ This function returns an action that display existing alert of given check_id. it shows the associated alert
                """
        self.ensure_one()
        result = self.env["ir.actions.actions"]._for_xml_id('elw_quality.elw_quality_alert_action_window')
        # print("result--------", result)
        # override the context to get rid of the default filtering on operation type
        result['context'] = {'default_partner_id': self.partner_id.id, 'default_origin': self.name,
                             'default_check_id': self.id}
        # print("result--------", result) # 'context': {'default_partner_id': 14, 'default_origin': 'QC00040', 'default_check_id': 37}, 'res_id': 0,
        # # choose the view_mode accordingly
        if not alerts or len(alerts) > 1:
            result['domain'] = [('id', 'in', alerts.ids)]
        elif len(alerts) == 1:
            res = self.env.ref('elw_quality.elw_quality_alert_form_view', False)
            # print("res-------", res) #res------- ir.ui.view(1952,)
            form_view = [(res and res.id or False, 'form')]
            # print("form_view-------", form_view)  #form_view------- [(1952, 'form')]
            result['views'] = form_view + [(state, view) for state, view in result.get('views', []) if
                                           view != 'form']
            result['res_id'] = alerts.id
            # print("result--------", result)
        return result

    def action_see_quality_measure_data(self):
        self.ensure_one()
        return {
            'name': _('Quality Measurement Data'),
            'res_model': 'elw.quality.measure.data',
            'domain': [('id', '=', self.measure_data_ids.ids)],
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'target': 'current',
        }

    @api.model
    def default_get(self, fields_list):
        res = super(ElwQualityCheck, self).default_get(fields_list)
        # print("default_get---", fields_list) # all the fields
        # print("res ---", res) # all default value
        if not res.get('team_id'):
            res['team_id'] = self.env['elw.quality.team'].browse(1).id
            # res['test_type_id'] = 5
        #     print("res 5 ---", res)
        #     unsupported operand type(s) for "==": 'elw.quality.measure.data()' == '<Command.UPDATE: 1>'
        #     res['measure_data_ids'] =self.env['elw.quality.measure.data'].browse(3)
        # print("res ---", res)
        return res

    # auto load product for Measure test type
    @api.onchange('point_id')
    def onchange_point_id(self):
        self.ensure_one()
        if self.point_id:
            if self.test_type_id.id == 5:
                self.product_id = self.point_id.product_id.id

    # below is to add a dynamic domain on product_id
    @api.depends('point_id')
    def _compute_product_id_domain(self):
        for rec in self:
            data_obj = self.env['elw.quality.point'].search([('id', '=', rec.point_id.id)])
            # print("product_range", data_obj, data_obj.product_ids.ids)
            rec.product_id_domain = json.dumps([('id', 'in', data_obj.product_ids.ids)])
            # print("product_range", rec.product_id_domain) #[["id", "in", [38, 18]]] this format works too

    # TypeError: ElwQualityCheck.name_search() got an unexpected keyword argument 'args'
    # @api.model
    # def name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
    #     domain = domain or []
    #     if name:
    #         domain = ['|', ('name', operator, name), ('test_type_id', operator, name)]
    #
    #     return super()._name_search(name, domain, operator, limit, order)

    @api.constrains('measure_data_ids')
    def _check_number_of_line_in_measure_data_ids(self):
        for rec in self:
            if rec.test_type_id.id == 5 and len(rec.measure_data_ids.ids):
                if len(rec.measure_data_ids.ids) != len(rec.measure_spec_ids.ids):
                    raise ValidationError(
                        _('Warning! Number of measurement data (%d) is not equal to number of measurement spec (%d).',
                          len(rec.measure_data_ids.ids), len(rec.measure_spec_ids.ids)))
