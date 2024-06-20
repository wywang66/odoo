from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class QualityAlert(models.Model):
    _name = 'elw.quality.alert'
    _description = 'elw quality alert'
    _inherit = ['mail.thread',
                'mail.activity.mixin',
                ]  # add a chatter
    _order = 'id desc, name desc'

    @api.returns('self')
    def _default_stage(self):
        return self.env['elw.quality.alert.stage'].search([], order="sequence asc", limit=1)

    name = fields.Char(
        string='Reference', default='New', copy=False, readonly=True)
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        readonly=True, required=True,
        help='The company is automatically set from your user preferences.')
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one('res.partner', string='Vendor', store=True, ondelete="set null")
    product_id = fields.Many2one('product.product', string='Product Variant', store=True, ondelete="set null",
                                 related="check_id.product_id", readonly=False, required=True)
    product_tmpl_id = fields.Many2one('product.template', string='Product', related='product_id.product_tmpl_id',
                                      store=True, ondelete="set null")
    picking_id = fields.Many2one('stock.picking', string='Picking', store=True, ondelete="set null")
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Very High')], string="Priority", tracking=True, store=True,
        help="1 star: Low, 2 stars: High, 3 stars: Very High")
    check_id = fields.Many2one('elw.quality.check', string='Check Ref#', readonly=False, ondelete='cascade',
                               store=True,
                               domain="[('quality_state', '=', 'fail')]")  # check_id is name of quality.check
    point_id = fields.Many2one('elw.quality.point', related='check_id.point_id', string='Control Point ID',
                               ondelete='set null')
    lot_ids = fields.Many2many('stock.lot', string='Lots/Serials', compute='_get_lot_ids', inverse='_inverse_lot_ids',
                               store=True)
    lot_name = fields.Char(string='Lots/Serials', store=True, compute='_get_lot_ids', inverse='_inverse_lot_ids')
    has_lot_id = fields.Boolean(string='Has Lot ids', related='check_id.has_lot_id', store=True)
    stage_id = fields.Many2one('elw.quality.alert.stage', string='Stage', default=_default_stage, store=True, copy=True,
                               ondelete='set null', tracking=True)
    picking_code = fields.Selection(related='picking_id.picking_type_id.code', readonly=True)
    user_id = fields.Many2one('res.users', string='Responsible', store=True, ondelete='set null')
    team_id = fields.Many2one('elw.quality.team', string='Team', compute="_get_team_id", store=True, readonly=False)
    date_assign = fields.Date(string='Date Assigned', default=fields.Date.context_today)
    date_close = fields.Date(string='Date Closed')
    tag_ids = fields.Many2many('elw.quality.tag', string='Tags', ondelete='restrict')
    reason_id = fields.Many2one('elw.quality.reason', string='Root Cause')
    email_cc = fields.Char(string="Email cc", store=True, copy=True)

    title = fields.Char(string='Title', store=True)

    # for notebook
    # additional_note = fields.Text('Note')
    # note = fields.Html('Instructions')
    description = fields.Html('Description')
    action_preventive = fields.Html('Preventive Action', store=True, copy=True)
    action_corrective = fields.Html('Corrective Action', store=True, copy=True)

    # select the same team_id from quality.check
    @api.depends('check_id')
    def _get_team_id(self):
        for rec in self:
            team_id_ = self.env['elw.quality.check'].browse(rec.check_id.id)
            # print("team_id_------", team_id_, rec.check_id.id)
            rec.team_id = team_id_.team_id if team_id_ else None

    # select the same lot_id from quality.check
    @api.depends('check_id')
    def _get_lot_ids(self):
        for rec in self:
            lot_ids_ = self.env['elw.quality.check'].browse(rec.check_id.id)
            # print("lot_id_------", lot_ids_.lot_name, lot_ids_.lot_ids.ids, rec.check_id.id)
            rec.lot_ids = lot_ids_.lot_ids if lot_ids_.lot_ids else None
            rec.lot_name = lot_ids_.lot_name if lot_ids_.lot_name else None

    def _inverse_lot_ids(self):
        for rec in self:
            if rec.check_id:
                check_lot_ids_ = self.env['elw.quality.check'].browse(rec.check_id.id)
                # print("lot_id_------", rec.lot_ids, rec.lot_name, rec.check_id.id)
                if rec.picking_code == 'outgoing':
                    check_lot_ids_ = rec.lot_ids if rec.lot_ids else None
                if rec.picking_code == 'incoming':
                    check_lot_name = rec.lot_name if rec.lot_name else None

    @api.depends('title')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.name} {record.title}"

    @api.model_create_multi
    def create(self, vals):
        for vals in vals:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.alert.sequence')
            rtn = super(QualityAlert, self).create(vals)
        return rtn

    # #  no decorator needed
    def write(self, vals):
        if not self.name and not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'elw.quality.alert.sequence')
        rtn = super(QualityAlert, self).write(vals)
        return rtn

    def unlink(self):
        for rec in self:
            if rec.check_id or rec.picking_id:
                raise ValidationError(_("Can not delete the record that links to Quality Check or Deliveries/Receipts"))
        return super(QualityAlert, self).unlink()

    def action_see_alerts(self):
        pass

    # this return to the correct ID in quality.check. not sure why
    def action_see_check(self):
        pass
