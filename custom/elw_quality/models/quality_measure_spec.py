from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class QualityMeasureSpec(models.Model):
    _name = 'elw.quality.measure.spec'
    _description = 'ELW Quality Measure Specification'
    _order = 'name desc'

    name = fields.Char('Sequence', size=6)
    measure_name = fields.Char('Measure Name', required=True, translate=True)
    target_value = fields.Float(string="Target Value", store=True)
    measured_value = fields.Float(string="Measured Value", store=True)
    target_value_unit = fields.Char(string="Unit", store=True, size=8)
    upper_limit = fields.Float(string="Upper Limit", store=True)
    lower_limit = fields.Float(string="Lower Limit", store=True)
    within_tolerance = fields.Boolean('Within Tolerance?')
    point_id = fields.Many2one('elw.quality.point', 'Quality Control Point')

    # below checks both upper and lower limits
    @api.constrains('upper_limit')
    def _check_upper_limit(self):
        print("checking")
        for rec in self:
            if rec.upper_limit < rec.lower_limit:
                raise ValidationError(_("The upper_limit must be > lower_limit"))

    @api.model_create_multi
    def create(self, vals):
        for vals in vals:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.measure.spec.sequence')
            rtn = super(QualityMeasureSpec, self).create(vals)
            return rtn

    # #  no decorator needed
    def write(self, vals):
        if not self.name and not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.measure.spec.sequence')
        rtn = super(QualityMeasureSpec, self).write(vals)
        return rtn
