from typing import Dict, List

from odoo import models, fields, api, SUPERUSER_ID, _
import logging
_logger = logging.getLogger(__name__)

class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'
    # _inherit = ['mail.thread', 'mail.activity.mixin',]  # add a chatter

    # equipment_ids = fields.Many2many('maintenance.equipment', string='Equipment', store=True)
    equipment_ids = fields.One2many('maintenance.equipment', 'workcenter_id', string='Equipment', store=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    maintenance_ids = fields.One2many('maintenance.request', 'workcenter_id', string='Maintenance', store=True)
    maintenance_count = fields.Integer(compute='_compute_maintenance_count', string="Maintenance Count", store=True)
    maintenance_open_count = fields.Integer(compute='_compute_maintenance_count', string="Current Maintenance", store=True)
    maintenance_team_id = fields.Many2one('maintenance.team', string='Maintenance Team', compute='_compute_maintenance_team_id', store=True, readonly=False,
                                          check_company=True)
    technician_user_id = fields.Many2one('res.users', string='Technician')

    # Update the workcenter_id in maintenance.equipment using the original object ID.
    @api.onchange('equipment_ids')
    def onchange_equipment_ids(self):
        # print('equipment_ids', self.equipment_ids, self.equipment_ids.ids, self, self.id)  # maintenance.equipment(<NewId origin=8>, <NewId origin=13>)
        # Onchange triggers with a new temporary object; the original object is accessible via self._origin.
        # eq_obj is a dummy obj which cannot create a record. direct the call to 'write' method in maintenance.equipment to update the record
        for eq_obj in self.equipment_ids:
            eq_obj.write({'workcenter_id': self._origin.id})
            # print('eq_obj info1: ', eq_obj, eq_obj.id, eq_obj.workcenter_id)  # maintenance.equipment(<NewId origin=3>,) NewId_3 mrp.workcenter()

    @api.depends('company_id')
    def _compute_maintenance_team_id(self):
        for record in self:
            if record.maintenance_team_id.company_id and record.maintenance_team_id.company_id.id != record.company_id.id:
                record.maintenance_team_id = False

    @api.depends('maintenance_ids.stage_id.done', 'maintenance_ids.archive')
    def _compute_maintenance_count(self):
        for record in self:
            record.maintenance_count = len(record.maintenance_ids)
            record.maintenance_open_count = len(record.maintenance_ids.filtered(lambda mr: not mr.stage_id.done and not mr.archive))


