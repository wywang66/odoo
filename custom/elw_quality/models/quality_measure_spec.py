from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class QualityMeasureSpec(models.Model):
    _name = 'elw.quality.measure.spec'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'ELW Quality Measure Specification'
    _order = 'name desc'

    active = fields.Boolean(default=True)
    name = fields.Char('Sequence', readonly=True)
    measure_name = fields.Char('Measure Name', required=True, translate=True, tracking=True, store=True)
    target_value = fields.Float(string="Target Value")
    measured_value = fields.Float(string="Measured Value", tracking=True, store=True)
    target_value_unit = fields.Char(string="Unit", tracking=True, required=True, store=True)
    upper_limit = fields.Float(string="Upper Limit", tracking=True, required=True, store=True)
    lower_limit = fields.Float(string="Lower Limit", tracking=True, required=True, store=True)
    within_tolerance = fields.Boolean('Within Tolerance?', default=False, tracking=True, store=True)
    point_id = fields.Many2one('elw.quality.point', 'Control Point Ref#', ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Products", domain="[('type','in',('product','consu'))]",
                                 store=True, related="point_id.product_id")
    date_created = fields.Date(string="Date Created", default=fields.Date.context_today)
    check_id = fields.Many2one('elw.quality.check', string='Check Ref#',
                               store=True)  # check_id is name of quality.check

    @api.depends('point_id', 'check_id')
    def _compute_display_name(self):
        for rec in self:
            if rec.check_id.name:
                rec.display_name = rec.name + ':' + rec.point_id.name + ':' + rec.check_id.name
            else:
                rec.display_name = rec.name + ':' + rec.point_id.name

    @api.onchange('measured_value')
    def onchange_measured_value(self):
        for line in self:
            if line.lower_limit <= line.measured_value <= line.upper_limit:
                line.within_tolerance = True
            else:
                line.within_tolerance = False

    # @api.onchange('measured_value')
    # def onchange_measured_value(self):
    #     for line in self.point_id.measure_spec_ids:
    #         if line.lower_limit <= line.measured_value <= line.upper_limit:
    #             vals = {
    #                 'within_tolerance': True,
    #             }
    #         else:
    #             vals = {
    #                 'within_tolerance': False,
    #             }
    #         line.update(vals)
    # print(line, line.upper_limit, line.measure_name)

    # # below checks both upper and lower limits
    # @api.constrains('upper_limit', 'lower_limit')
    # def _check_upper_limit(self):
    #     # print("checking upper or lower limit")
    #     for rec in self:
    #         if rec.upper_limit < rec.lower_limit:
    #             raise ValidationError(_("The upper_limit must be > lower_limit"))

    # below checks target_value

    @api.onchange('upper_limit', 'lower_limit')
    def onchange_upper_lower_limits(self):
        for line in self.point_id.measure_spec_ids:
            if line.upper_limit < line.lower_limit:
                raise ValidationError(_("The upper_limit must be > lower_limit"))

    @api.model_create_multi
    def create(self, vals):
        for vals in vals:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.measure.spec.sequence')
            rtn = super(QualityMeasureSpec, self).create(vals)
        return rtn

    # #  no decorator needed
    # To Show tracking in chatter Add tracking=True https://www.odoo.com/forum/help-1/how-to-use-track-visibility-onchange-on-order-lines-fields-odoo14-211204
    def write(self, vals):
        if not self.name and not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.measure.spec.sequence')
        # print("write  ............", vals)
        rtn = super(QualityMeasureSpec, self).write(vals)
        return rtn


class QualityMeasureData(models.Model):
    _name = 'elw.quality.measure.data'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'ELW Quality Measure Data'
    _order = 'name desc'

    active = fields.Boolean(default=True)
    name = fields.Char('Sequence', readonly=True)
    # spec_id = fields.Many2one('elw.quality.measure.spec', string="Measure Spec Ref#")
    measure_name = fields.Char('Measure Name', required=True, translate=True, tracking=True, store=True)
    target_value = fields.Float(string="Target Value")
    measured_value = fields.Float(string="Measured Value", tracking=True, store=True)
    target_value_unit = fields.Char(string="Unit", required=True, tracking=True, store=True)
    upper_limit = fields.Float(string="Upper Limit", required=True, tracking=True, store=True)
    lower_limit = fields.Float(string="Lower Limit", required=True, tracking=True, store=True)
    within_tolerance = fields.Boolean('Within Tolerance?', default=False, tracking=True, store=True)
    point_id = fields.Many2one('elw.quality.point', 'Control Point Ref#', ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Products", domain="[('type','in',('product','consu'))]",
                                 store=True, related="point_id.product_id")
    date_created = fields.Date(string="Date Created", default=fields.Date.context_today)
    check_id = fields.Many2one('elw.quality.check', string='Check Ref#',
                               store=True)  # check_id is name of quality.check

    # def _get_spec_id(self):
    #     for line in self:
    #         line.spec_id = self.env['elw.quality.measure.spec'].search([('point_id', '=', line.point_id)])

    # @api.onchange, it just not support one2many
    @api.depends('measured_value', 'lower_limit', 'upper_limit')
    def _recheck_measured_value(self):
        for line in self.check_id.measure_data_ids:
            if line.lower_limit <= line.measured_value <= line.upper_limit:
                vals = {
                    'within_tolerance': True,
                }
            else:
                vals = {
                    'within_tolerance': False,
                }
            line.update(vals)

    # below checks both upper and lower limits
    @api.depends('upper_limit', 'lower_limit')
    def _recheck_upper_lower_limits(self):
        for line in self.check_id.measure_data_ids:
            # print(line.upper_limit, line.lower_limit)
            if line.upper_limit < line.lower_limit:
                raise ValidationError(_("The upper_limit must be > lower_limit"))
                return -1
        return 0

    @api.model_create_multi
    def create(self, vals):
        for vals in vals:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.measure.data.sequence')
            # print("create  ............", vals)
            rtn = super(QualityMeasureData, self).create(vals)
        return rtn

    # #  no decorator needed
    # To Show tracking in chatter Add tracking=True https://www.odoo.com/forum/help-1/how-to-use-track-visibility-onchange-on-order-lines-fields-odoo14-211204
    def write(self, vals):
        if not self.name and not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.measure.data.sequence')
        rtn = super(QualityMeasureData, self).write(vals)
        # print("write  ............", vals)  # write  ............ {'measured_value': 1} one value
        #  if condition is a must for avoiding the max recursion depth exceeded error
        #  write 'measured_value' on all of one2many fields in the existing one record
        if vals.get('measured_value') or vals.get('upper_limit') or vals.get('lower_limit'):
            res = self._recheck_upper_lower_limits()
            if res == 0:
                self._recheck_measured_value()
        return rtn
