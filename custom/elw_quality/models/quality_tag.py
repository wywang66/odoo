from odoo import models, fields, api, _


class QualityTag(models.Model):
    _name = 'elw.quality.tag'
    _description = 'Quality Tag'

    name = fields.Char(string='Tag Name', required=True, trim=True)  # trim the spaces when user entering this field
    active = fields.Boolean(string="Active", default=True)
    color = fields.Integer("Color")

    _sql_constraints = [
        ('uniq_name', 'unique(name, active)', 'name must be unique.'),
    ]