from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class QualityMeasureSpec(models.Model):
    _name = 'elw.quality.measure.spec'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'ELW Quality Measure Specification'
    _order = 'name desc'

    name = fields.Char('Sequence', size=6)
    measure_name = fields.Char('Measure Name', required=True, translate=True, tracking=True, store=True)
    target_value = fields.Float(string="Target Value")
    measured_value = fields.Float(string="Measured Value", tracking=True, store=True)
    target_value_unit = fields.Char(string="Unit", size=8, tracking=True, store=True)
    upper_limit = fields.Float(string="Upper Limit", tracking=True, store=True)
    lower_limit = fields.Float(string="Lower Limit", tracking=True, store=True)
    within_tolerance = fields.Boolean('Within Tolerance?', size=4, default=False, tracking=True, store=True)
    point_id = fields.Many2one('elw.quality.point', 'Quality Control Point')

    @api.onchange('measured_value')
    def onchange_measured_value(self):
        for line in self.point_id.measure_data_ids:
            if line.lower_limit <= line.measured_value <= line.upper_limit:
                vals = {
                    'within_tolerance': True,
                }
            else:
                vals = {
                    'within_tolerance': False,
                }
            line.update(vals)
            # print(line, line.upper_limit, line.measure_name)

    # below checks both upper and lower limits
    @api.constrains('upper_limit')
    def _check_upper_limit(self):
        # print("checking upper or lower limit")
        for rec in self:
            if rec.upper_limit < rec.lower_limit:
                raise ValidationError(_("The upper_limit must be > lower_limit"))

    @api.model_create_multi
    def create(self, vals):
        for vals in vals:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.measure.spec.sequence')
            rtn = super(QualityMeasureSpec, self).create(vals)
            return rtn

    # #  no decorator needed
    # To Show tracking in chatter Add tracking=True https://www.odoo.com/forum/help-1/how-to-use-track-visibility-onchange-on-order-lines-fields-odoo14-211204
    def write(self, vals):
        if not self.name and not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.measure.spec.sequence')
        rtn = super(QualityMeasureSpec, self).write(vals)
        # Error on _get_tracked_fields
        # if set(vals) & set(self._get_tracked_fields(vals)):
        #     self._track_changes(self.point_id)
        return rtn

    def _track_changes(self, field_to_track):
        if self.message_ids:
            message_id = field_to_track.message_post(
                body=f'{self._description}: {self.display_name}').id
            trackings = self.env['mail.tracking.value'].sudo().search(
                [('mail_message_id', '=', self.message_ids[0].id)])
            for tracking in trackings:
                tracking.copy({'mail_message_id': message_id})