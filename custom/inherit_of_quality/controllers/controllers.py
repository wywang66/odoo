# -*- coding: utf-8 -*-
# from odoo import http


# class Inheritence(http.Controller):
#     @http.route('/inheritence/inheritence', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/inheritence/inheritence/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('inheritence.listing', {
#             'root': '/inheritence/inheritence',
#             'objects': http.request.env['inheritence.inheritence'].search([]),
#         })

#     @http.route('/inheritence/inheritence/objects/<model("inheritence.inheritence"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('inheritence.object', {
#             'object': obj
#         })

