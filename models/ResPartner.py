# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    project_ids = fields.One2many(comodel_name="project.project", inverse_name="partner_id", string='Проекты')
