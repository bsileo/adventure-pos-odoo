# -*- coding: utf-8 -*-
# from odoo import http


# class AdventurePos(http.Controller):
#     @http.route('/adventure_pos/adventure_pos', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/adventure_pos/adventure_pos/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('adventure_pos.listing', {
#             'root': '/adventure_pos/adventure_pos',
#             'objects': http.request.env['adventure_pos.adventure_pos'].search([]),
#         })

#     @http.route('/adventure_pos/adventure_pos/objects/<model("adventure_pos.adventure_pos"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('adventure_pos.object', {
#             'object': obj
#         })

