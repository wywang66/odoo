from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
import json

class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    maintenance_for = fields.Selection([('equipment', 'Equipment'), ('workcenter', 'Work Center')], string='For', store=True)
    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center', ondelete='cascade')
    workcenter_equipment_id_domain = fields.Char(compute="_compute_workcenter_equipment_id_domain", store=True)
    block_workcenter = fields.Boolean(string='Block Workcenter', store=True, copy=True)

    # below is to add a dynamic domain on product_id
    @api.depends('workcenter_id')
    def _compute_workcenter_equipment_id_domain(self):
        for rec in self:
            data_obj = self.env['mrp.workcenter'].browse(rec.workcenter_id.id)
            rec.workcenter_equipment_id_domain = json.dumps([('id', 'in', data_obj.equipment_ids.ids)])

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

    def button_see_elw_mrp_workcenter(self):
        self.ensure_one()
        return {
            'name': _('Work Center'),
            'res_model': 'mrp.workcenter',
            'res_id': self.workcenter_id.id,  # open the corresponding form
            # 'domain': [('id', '=', self.workcenter_id)],
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'current',
        }