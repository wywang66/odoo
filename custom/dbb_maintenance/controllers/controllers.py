# -*- coding: utf-8 -*-
# from odoo import http


# class DbbMaintenance(http.Controller):
#     @http.route('/dbb_maintenance/dbb_maintenance', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dbb_maintenance/dbb_maintenance/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('dbb_maintenance.listing', {
#             'root': '/dbb_maintenance/dbb_maintenance',
#             'objects': http.request.env['dbb_maintenance.dbb_maintenance'].search([]),
#         })

#     @http.route('/dbb_maintenance/dbb_maintenance/objects/<model("dbb_maintenance.dbb_maintenance"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dbb_maintenance.object', {
#             'object': obj
#         })

