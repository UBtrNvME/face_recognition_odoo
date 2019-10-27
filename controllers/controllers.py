# -*- coding: utf-8 -*-
from odoo import http

# class Gpodem(http.Controller):
#     @http.route('/gpodem/gpodem/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/gpodem/gpodem/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('gpodem.listing', {
#             'root': '/gpodem/gpodem',
#             'objects': http.request.env['gpodem.gpodem'].search([]),
#         })

#     @http.route('/gpodem/gpodem/objects/<model("gpodem.gpodem"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('gpodem.object', {
#             'object': obj
#         })