from odoo import models, fields, api, _


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
    point_id = fields.Many2one('elw.quality.point', string='Control Point ID', ondelete='set null')

    partner_id = fields.Many2one('res.partner', string='Partner', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', store=True,
                                 domain="[('type', 'in', ['product', 'consu'])]", ondelete='set null')
    picking_id = fields.Many2one('stock.picking', string='Picking', store=True, ondelete='set null')
    measure_on = fields.Selection(related='point_id.measure_on', string='Control per')
    lot_id = fields.Many2one('stock.lot', string='Lot/Serial', domain="[('product_id', '=', product_id)]", store=True,
                             ondelete='restrict')
    has_lot_id = fields.Boolean(string='Has Lot ids', compute="_compute_has_lot_id")
    user_id = fields.Many2one('res.users', string='Checked By', ondelete="cascade")
    test_type_id = fields.Many2one(related='point_id.test_type_id', string='Test Type', ondelete='Set NULL')
    team_id = fields.Many2one('elw.quality.team', string='Team', store=True, required=True, ondelete='cascade')
    control_date = fields.Date(string='Checked Date', default=fields.Date.context_today)
    quality_state = fields.Selection([('none', 'To Do'), ('pass', 'Passed'), ('fail', 'Failed')], required=True,
                                     default='none', string='Status')
    test_type = fields.Char(related='point_id.test_type', string="Test Type Name")
    alert_count = fields.Integer(default=0, compute="_compute_alert_cnt")
    alert_ids = fields.One2many('elw.quality.alert', 'check_id', string="Alerts")
    alert_result = fields.Char(compute="_compute_alert_result", string='Quality Check Result')
    fail_and_not_alert_created = fields.Boolean(string='fail_and_not_alert_created',
                                                compute='_compute_fail_and_not_alert_created', store=True)

    # check if an alert is created on 'fail' record
    def _compute_fail_and_not_alert_created(self):
        for rec in self:
            rec.fail_and_not_alert_created = True if rec.quality_state == 'fail' and not rec.alert_ids else False
            print("----------", rec.fail_and_not_alert_created)

    # for notebook
    additional_note = fields.Text('Note')
    note = fields.Html('Instructions')

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

    @api.depends('alert_ids')
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

    def do_pass(self):
        for rec in self:
            if rec.quality_state == 'none':
                rec.quality_state = 'pass'

    def do_fail(self):
        for rec in self:
            if rec.quality_state == 'none':
                rec.quality_state = 'fail'

    def do_measure(self):
        pass

    def _create_qa_alert_record(self, vals):
        self.ensure_one()
        qa_alert_rec = self.env['elw.quality.alert'].create(vals)
        print("created qa_alert_rec--------", qa_alert_rec, qa_alert_rec.id, qa_alert_rec.name)
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
        print("vals in quality.check---------", vals)
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
            result['views'] = form_view + [(state, view) for state, view in result.get('views', []) if view != 'form']
            result['res_id'] = alerts.id
            # print("result--------", result)
        return result

