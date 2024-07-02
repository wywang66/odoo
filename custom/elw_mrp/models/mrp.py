from odoo import models, fields, api, SUPERUSER_ID, _


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center', ondelete='cascade')
    # revise required=False to avoid ValidateError when saving 'eq_reference_record'
    name = fields.Char('Equipment Name', required=False, translate=True)


class MaintenanceMixin(models.AbstractModel):
    _inherit = 'maintenance.mixin'

    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment',
                                   help="Specific equipment that is used in this work center.", copy=True)


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    equipment_ids = fields.One2many('maintenance.equipment', 'workcenter_id', string='Equipment', copy=True)
