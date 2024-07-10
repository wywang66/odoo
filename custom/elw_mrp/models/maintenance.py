from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
import json

class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    maintenance_for = fields.Selection([('equipment', 'Equipment'), ('workcenter', 'Work Center')], string='For', store=True)
    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center', ondelete='cascade')
    # workcenter_equipment_id_domain = fields.Char(compute="_compute_workcenter_equipment_id_domain", store=True)
    workcenter_equipment_id_domain = fields.Char()
    # to do: it is not known to link block_workcenter to work_state of mrp.workcenter
    block_workcenter = fields.Boolean(string='Block Workcenter', store=True, copy=True)

    # below is to add a dynamic domain on product_id
    @api.onchange('workcenter_id', 'maintenance_for')
    def _onchange_workcenter_equipment_id_domain(self):
        if self.maintenance_for == 'workcenter' and self.workcenter_id:
            self.equipment_id = False
            equipment_ids = self.workcenter_id.equipment_ids.ids
            domain = [('id', 'in', equipment_ids)]
        else:
            self.workcenter_id = False
            self.equipment_id = False
            all_equipment_ids = self.env['maintenance.equipment'].search([]).ids
            domain = [('id', 'in', all_equipment_ids)]

        self.workcenter_equipment_id_domain = json.dumps(domain)
        # print('rec.workcenter_equipment_id_domain', self.workcenter_equipment_id_domain)


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
        # return self._get_action_view_see_alert(self.alert_ids)
        self.ensure_one()
        return {
            'name': _('Work Center'),
            'res_model': 'mrp.workcenter',
            'res_id': self.workcenter_id.id,  # open the corresponding form
            'domain': [('workcenter_id', '=', self.workcenter_id)],
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'current',
        }

    def _get_action_view_see_alert(self, alerts):
        """ This function returns an action that display existing alert of given check_id. it shows the associated alert
                """
        self.ensure_one()
        result = self.env["ir.actions.actions"]._for_xml_id('elw_quality.elw_quality_alert_action_window')
        # print("result--------", result)
        # override the context to get rid of the default filtering on operation type
        result['context'] = {'default_partner_id': self.partner_id.id, 'default_origin': self.name,
                             'default_check_id': self.id}
        # print("result--------", result) # 'context': {'default_partner_id': 14, 'default_origin': 'QC00040', 'default_check_id': 37}, 'res_id': 0,
        # # choose the view_mode accordingly
        if not alerts or len(alerts) > 1:
            result['domain'] = [('id', 'in', alerts.ids)]
        elif len(alerts) == 1:
            res = self.env.ref('elw_quality.elw_quality_alert_form_view', False)
            # print("res-------", res) #res------- ir.ui.view(1952,)
            form_view = [(res and res.id or False, 'form')]
            # print("form_view-------", form_view)  #form_view------- [(1952, 'form')]
            result['views'] = form_view + [(state, view) for state, view in result.get('views', []) if
                                           view != 'form']
            result['res_id'] = alerts.id
            # print("result--------", result)
        return result