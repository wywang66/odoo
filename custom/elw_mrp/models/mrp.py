from odoo import models, fields, api, _


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center', ondelete='cascade')
    # revise required=False to avoid ValidateError when saving 'eq_reference_record'
    name = fields.Char('Equipment Name', required=False, translate=True)


class MaintenanceMixin(models.AbstractModel):
    _inherit = 'maintenance.mixin'

    @api.returns('self')
    def _default_equipment(self):
        return self.env['maintenance.equipment'].search([], limit=1)

    eq_reference_record = fields.Reference(selection=[('maintenance.equipment', 'Equipment')], string="Equipment", default=_default_equipment,
                                           help='User should select the equipment', required=True)


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    equipment_ids = fields.One2many('maintenance.equipment', 'workcenter_id', string='Equipment',
                                    help="Specific equipment that is used in this work center.", copy=True)

