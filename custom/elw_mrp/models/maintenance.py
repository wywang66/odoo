from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    maintenance_for = fields.Selection([('equipment', 'Equipment'), ('workcenter', 'Work Center')], string='For', store=True)
    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center', ondelete='cascade')


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center', ondelete='cascade', store=True)

    def write(self, vals):
        if 'workcenter_id' in vals:
            # print('in write', vals, vals['workcenter_id'], self._origin.id) # in write {'workcenter_id': 2} 2 5
            equipment = self.env['maintenance.equipment'].browse(self._origin.id)
            # print('equipment', equipment, self)  # maintenance.equipment(5,) maintenance.equipment(<NewId origin=5>,)
            res = super(MaintenanceEquipment, equipment).write({'workcenter_id': vals['workcenter_id']})
        else:
            res = super(MaintenanceEquipment, self).write(vals)
        return res