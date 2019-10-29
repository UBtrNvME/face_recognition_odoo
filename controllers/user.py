# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class User(http.Controller):
    @http.route('/users', auth='public')
    def users(self, **kw):
        users = request.env["res.partner"].search([])
        return request.render("gpodem.frontend_users", {
            "users": users
        })

    @http.route('/user/<int:user_id>', auth='public')
    def user(self, user_id, **kw):
        user = request.env["res.partner"].search([("id", "=", user_id)])
        return request.render("gpodem.frontend_user", {
            "user": user
        })
