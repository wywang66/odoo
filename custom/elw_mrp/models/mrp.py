from odoo import models, fields, api


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center', ondelete='cascade')


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    equipment_ids = fields.One2many('maintenance.equipment', 'workcenter_id', string='Equipment',
                                    help="Specific equipment that is used in this work center.", copy=True)
