from odoo import models, fields, api, _


class QualityMeasureSpec(models.Model):
    _name = 'elw.quality.measure.spec'
    _description = 'ELW Quality Measure Specification'
    _order = 'sequence, id'

    name = fields.Char('Measure Name', required=True, translate=True)
    sequence = fields.Integer('Sequence')
    target_value = fields.Float(string="Target Value", store=True)
    target_value_unit = fields.Char(string="Target Value Unit", store=True)
    tolerance_max = fields.Float(string="Tolerance Max", store=True)
    tolerance_min = fields.Float(string="Tolerance Min", store=True)
    within_tolerance = fields.Boolean('Within Tolerance?')
    point_id = fields.Many2one('elw.quality.point', 'Quality Control Point')
