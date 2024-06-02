from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


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
    lot_id = fields.Many2one('stock.lot', string='Lot/Serial', domain="[('product_id', '=', product_id)]", store=True,
                             ondelete='restrict')
    has_lot_id = fields.Boolean(string='Has Lot ids', compute="_compute_has_lot_id")
    user_id = fields.Many2one('res.users', string='Checked By', ondelete="cascade")
    test_type_id = fields.Many2one(related='point_id.test_type_id', string='Test Type', ondelete='Set NULL')
    team_id = fields.Many2one('elw.quality.team', string='Team', store=True, required=True, ondelete='cascade')
    control_date = fields.Date(string='Checked Date', default=fields.Date.context_today)
    quality_state = fields.Selection([('none', 'To Do'), ('pass', 'Passed'), ('fail', 'Failed')], required=True,
                                     default='none', string='Status')
    alert_count = fields.Integer(default=0, compute="_compute_alert_cnt")
    alert_ids = fields.One2many('elw.quality.alert', 'check_id', string="Alerts")
    alert_result = fields.Char(compute="_compute_alert_result", string='Quality Check Result')
    fail_and_not_alert_created = fields.Boolean(string='fail_and_not_alert_created',
                                                compute='_compute_fail_and_not_alert_created', store=True)
    picture = fields.Binary(string="Picture", store=True)
    # for notebook
    additional_note = fields.Text('Note')
    note = fields.Html('Instructions')

    # use related to get measurement settings defined in quality.point, readonly=false so this field is editable
    # commented domain as it report "test_type_id" error
    measure_data_ids = fields.One2many('elw.quality.measure.spec', 'point_id',
                                       readonly=False,
                                       # related='point_id.measure_data_ids')
                                       # domain=[('test_type_id', '=', 'self.test_type_id')],
                                       compute="_compute_measured_data")
    measure_data_count = fields.Integer("Measure Data Count", compute='_compute_measure_data_count')

    # # measure_data_ids must be filled if test_type_id == 5
    # @api.constrains('measure_data_ids')
    # def _check_if_measure_data_ids_empty(self):
    #     for rec in self:
    #         if rec.test_type_id.id == 5:
    #             for each in rec.measure_data_ids:
    #                 if not each.measured_value:
    #                     raise ValidationError(
    #                         _("You have not updated Measured Value on %s in 'Measurement Data' tag", each.measure_name))

    def _compute_measured_data(self):
        for rec in self:
            if rec.test_type_id.id == 5:
                data = self.env['elw.quality.point'].browse(rec.point_id.id)
                measure_ids = []
                # print(data, data.measure_data_ids) #elw.quality.point(4,) elw.quality.measure.spec(7, 6)
                for one_measure_setting in data.measure_data_ids:
                    # print(one_measure_setting.id, one_measure_setting.name, one_measure_setting.measure_name,
                    #       one_measure_setting.upper_limit,
                    #       one_measure_setting.lower_limit)
                    # set the measured_value=0 when loading the measure_data_ids from quality.point
                    # one_measure_setting.measured_value = 0
                    # one_measure_setting.within_tolerance = False
                    # if the quality.point record has 'check_id'
                    # print("one_measure_setting.check_id.name---", one_measure_setting.check_id.name)
                    # if not one_measure_setting.check_id.name:
                    measure_ids.append(one_measure_setting.id)
                    # else:
                    #     id = self.env['elw.quality.measure.spec'].
                    #     measure_ids.append(one_measure_setting.id)
                    #
                    #     line = self.env['elw.quality.measure.spec'].browse(one_measure_setting.id)
                    #     print("line-----", line)
                    #     new_line_id = line.copy()
                    #     new_line_id.measured_value = 0
                    #     measure_ids.append(new_line_id.id)
                rec.measure_data_ids = self.env['elw.quality.measure.spec'].browse(measure_ids)
            else:
                rec.measure_data_ids = None

    @api.depends('measure_data_ids')
    def _compute_measure_data_count(self):
        for rec in self:
            num_data = 0
            if rec.measure_data_ids:
                num_data = sum(1 for data in rec.measure_data_ids if
                               data.measure_name != '' and data.target_value_unit != '')
            rec.measure_data_count = num_data

    # update check_id in elw.quality.measure.spec and save the records, then archived the records
    @api.depends('measure_data_ids')
    def action_measure_data_confirm(self):
        for line in self.measure_data_ids:
            print('line.id, line.name', line.id, line.name, self.id, line.check_id)
            if not line.measured_value:
                raise ValidationError(
                    _("You have not updated Measured Value in Measure name: %s",
                      line.measure_name))
            elif not line.check_id or line.check_id.id != self.id:
                line.check_id = self.id
                print("line", line, line.check_id.id, line.check_id.name)
                copy_id = line.copy()
                copy_id.active = False
                # reset the line value
                # line.measured_value = 0
                line.check_id = None



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

    def _compute_alert_cnt(self):
        for rec in self:
            # print("rec.........", rec, rec.id, rec.name)
            rec.alert_count = self.env['elw.quality.alert'].search_count([('check_id', '=', rec.name)])

    @api.depends('alert_ids', 'quality_state')
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
            self.action_measure_data_confirm()
            rtn = super(ElwQualityCheck, self).create(vals)
        return rtn

    # #  no decorator needed
    def write(self, vals):
        # print("self.name, vals.get('name'), vals", self.name, vals.get('name'), vals) #QC00046 None {'quality_state': 'pass'}
        # IMPORTANT --- without 'not self.name', Reference keeps rolling
        if not self.name and not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.check.sequence')
        self.action_measure_data_confirm()
        rtn = super(ElwQualityCheck, self).write(vals)
        return rtn

    def unlink(self):
        for rec in self:
            if rec.quality_state != 'none' or rec.picking_id:
                raise ValidationError(
                    _("Can not delete the record that is not in 'To Do' or has Deliveries/Receipts order"))
        return super(ElwQualityCheck, self).unlink()

    @api.depends('quality_state')
    def do_pass(self):
        for rec in self:
            if rec.quality_state == 'none':
                rec.quality_state = 'pass'

    @api.depends('quality_state')
    def do_fail(self):
        for rec in self:
            if rec.quality_state == 'none':
                rec.quality_state = 'fail'

    def do_measure(self):
        pass

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
