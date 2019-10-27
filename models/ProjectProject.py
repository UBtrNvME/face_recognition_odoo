# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectProject(models.Model):
    _inherit = 'project.project'

    stage_id = fields.Many2one(comodel_name="project.task.type")
