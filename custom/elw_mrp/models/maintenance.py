from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    maintenance_for = fields.Selection([('equipment', 'Equipment'), ('workcenter', 'Work Center')], string='For', store=True)
    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center', ondelete='cascade')


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center', ondelete='cascade', compute='_get_workcenter_id', inverse='_inverse_workcenter_id', store=True)

    @api.depends('workcenter_id.equipment_ids')
    def _get_workcenter_id(self):
        wc_obj_all = self.env['mrp.workcenter'].search([])
        for rec in self:
            rec.workcenter_id = False
            for wc_obj in wc_obj_all:
                if rec in wc_obj.equipment_ids:
                    rec.workcenter_id = wc_obj
                    break

    def _inverse_workcenter_id(self):
        for rec in self:
            wc_obj_all = self.env['mrp.workcenter'].search([('equipment_ids', 'in', rec.id)])
            # print('set: wc_obj_all', wc_obj_all)
            if rec.workcenter_id:
                # remove equipment from other work centers if there is
                for wc_obj in wc_obj_all:
                    if rec in wc_obj.equipment_ids and wc_obj != rec.workcenter_id:
                        wc_obj.equipment_ids = [(3, rec.id)]  # remove
                    # add equipment to the selected work center if not present
                if rec not in rec.workcenter_id.equipment_ids:
                    rec.workcenter_id.equipment_ids = [(4, rec.id)] # add
                    # print('not in', rec.workcenter_id.equipment_ids, rec.id, rec.workcenter_id)
            # else:
            #     print("no wc")
            #     for wc_obj in wc_obj_all:
            #         if rec in wc_obj.equipment_ids:
            #             wc_obj.equipment_ids = [(3, rec.id)]  # remove

    def write(self, vals):
        if 'workcenter_id' in vals:
            # print('in write', vals, vals['workcenter_id'], self._origin.id) # in write {'workcenter_id': 2} 2 5
            equipment = self.env['maintenance.equipment'].browse(self._origin.id)
            # print('equipment', equipment, self)  # maintenance.equipment(5,) maintenance.equipment(<NewId origin=5>,)
            res = super(MaintenanceEquipment, equipment).write({'workcenter_id': vals['workcenter_id']})
        else:
            res = super(MaintenanceEquipment, self).write(vals)
        return res