from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    maintenance_for = fields.Selection([('equipment', 'Equipment'), ('workcenter', 'Work Center')], string='For', store=True)
    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center', ondelete='cascade')
