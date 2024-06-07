# -*- coding: utf-8 -*-
# from odoo import http


# class MaterialManagement(http.Controller):
#     @http.route('/material_management/material_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/material_management/material_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('material_management.listing', {
#             'root': '/material_management/material_management',
#             'objects': http.request.env['material_management.material_management'].search([]),
#         })

#     @http.route('/material_management/material_management/objects/<model("material_management.material_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('material_management.object', {
#             'object': obj
#         })

