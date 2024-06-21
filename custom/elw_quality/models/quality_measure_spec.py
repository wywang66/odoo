from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class QualityMeasureSpec(models.Model):
    _name = 'elw.quality.measure.spec'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'ELW Quality Measure Specification'
    _order = 'name desc'

    active = fields.Boolean(default=True)
    name = fields.Char('Sequence', readonly=True)
    measure_name = fields.Char('Measure Name', required=True, tracking=True, store=True)
    target_value = fields.Float(string="Target Value")
    target_value_unit = fields.Char(string="Unit", tracking=True, required=True, store=True)
    upper_limit = fields.Float(string="Upper Limit", tracking=True, required=True, store=True)
    lower_limit = fields.Float(string="Lower Limit", tracking=True, required=True, store=True)
    # within_tolerance = fields.Boolean('Within Tolerance?', default=False, tracking=True, store=True)
    point_id = fields.Many2one('elw.quality.point', 'Control Point Ref#', ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Products", domain="[('type','in',('product','consu'))]",
                                 store=True, related="point_id.product_id", ondelete='cascade')
    date_created = fields.Date(string="Date Created", default=fields.Date.context_today)
    check_id = fields.Many2one('elw.quality.check', string='Check Ref#', ondelete='cascade',
                               store=True)  # check_id is name of quality.check

    @api.depends('point_id', 'product_id')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = str(rec.point_id.name) + ':' + str(rec.product_id.name)

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
    spec_id = fields.Many2one('elw.quality.measure.spec', string="Measure Spec Ref#", ondelete='cascade')
    measure_name = fields.Char('Measure Name', related="spec_id.measure_name", translate=True, tracking=True, store=True)
    target_value = fields.Float(string="Target Value", related="spec_id.target_value",)
    measured_value = fields.Float(string="Measured Value", tracking=True, store=True)
    target_value_unit = fields.Char(string="Unit", related="spec_id.target_value_unit", tracking=True, store=True)
    upper_limit = fields.Float(string="Upper Limit", related="spec_id.upper_limit", tracking=True, store=True)
    lower_limit = fields.Float(string="Lower Limit", related="spec_id.lower_limit", tracking=True, store=True)
    within_tolerance = fields.Boolean('Pass?', default=False, tracking=True, store=True)
    point_id = fields.Many2one('elw.quality.point', 'Control Point Ref#', ondelete='cascade', related="spec_id.point_id")
    product_id = fields.Many2one('product.product', string="Products", domain="[('type','in',('product','consu'))]",
                                 store=True, related="spec_id.product_id", ondelete='cascade')
    date_created = fields.Date(string="Date Created", default=fields.Date.context_today)
    check_id = fields.Many2one('elw.quality.check', string='Check Ref#', ondelete='cascade',
                               store=True)  # check_id is name of quality.check

    # @api.onchange, it just not support one2many
    @api.onchange('measured_value')
    def onchange_measured_value(self):
        # print("measured_value", self.measured_value, self.upper_limit, self.lower_limit )
        if self.measured_value and self.upper_limit and self.lower_limit:
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

    @api.model_create_multi
    def create(self, vals):
        for vals in vals:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.measure.data.sequence')
            # print("create  ............", vals)
            rtn = super(QualityMeasureData, self).create(vals)
        return rtn

    # #  no decorator needed
    def write(self, vals):
        if not self.name and not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.measure.data.sequence')
        rtn = super(QualityMeasureData, self).write(vals)
        return rtn

