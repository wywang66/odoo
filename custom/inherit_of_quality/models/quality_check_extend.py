from odoo import models, fields, api


class QualityExtend(models.Model):
    _inherit = 'elw.quality.check'
    _description = 'inheritance of elw quality'

    # res.users is db table of users, all users in the APP
    # add a new field in the inheritted model
    so_comfirmed_user_id = fields.Many2one('res.users', string='SO Confirmed User')   

