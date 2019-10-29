# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class Project(http.Controller):
    @http.route('/projects', auth='public')
    def projects(self, **kw):
        projects = request.env["project.project"].search([])
        return request.render("gpodem.frontend_projects", {
            "projects": projects
        })

    @http.route('/project/<int:project_id>', auth='public')
    def project(self, project_id, **kw):
        project = request.env["project.project"].search([("id", "=", project_id)])
        return request.render("gpodem.frontend_project", {
            "project": project
        })
