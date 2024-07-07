from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    maintenance_for = fields.Selection([('equipment', 'Equipment'), ('workcenter', 'Work Center')], string='For', store=True)
    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center', ondelete='cascade')


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center', ondelete='cascade', compute='_get_workcenter_id')

    def _get_workcenter_id(self):
        wc_obj_all = self.env['mrp.workcenter'].search([])
        for rec in self:
            rec.workcenter_id = False
            for wc_obj in wc_obj_all:
                if self in wc_obj.equipment_ids:
                    rec.workcenter_id = wc_obj
                    break

