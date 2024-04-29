# -*- coding: utf-8 -*-
# from odoo import http


# class ElwQuality(http.Controller):
#     @http.route('/elw_quality/elw_quality', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/elw_quality/elw_quality/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('elw_quality.listing', {
#             'root': '/elw_quality/elw_quality',
#             'objects': http.request.env['elw_quality.elw_quality'].search([]),
#         })

#     @http.route('/elw_quality/elw_quality/objects/<model("elw_quality.elw_quality"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('elw_quality.object', {
#             'object': obj
#         })

