# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.one
    @api.depends("partner_id")
    def _get_creator_email(self):
        self.creator_email = self.partner_id.email

    @api.one
    def send_approval(self):
        template = self.env.ref('gpodem.approval_email_template')
        self.env['mail.template'].browse(template.id).send_mail(self.id)

    @api.model
    def get_default_company(self):
        return self.env['res.company'].browse(1)

    @api.model
    def get_default_partner(self):
        return self.env['res.users'].browse(self.env.uid).partner_id

    @api.model
    def get_default_stage_id(self):
        return self.env["project.task.type"].search([("name", "=", "Новые")], limit=1)

    stage_id = fields.Many2one(comodel_name="project.task.type", string='Стадия', default=get_default_stage_id)
    manager_id = fields.Many2one(comodel_name="res.partner", string="Менеджер", default=get_default_partner)
    description = fields.Text(string='Описание проекта')
    creator_email = fields.Char(string='Email создателя', compute="_get_creator_email")
    partner_id = fields.Many2one(comodel_name="res.partner", default=get_default_partner)
    company_id = fields.Many2one(comodel_name="res.company", string="Ответственная компания",
                                 default=get_default_company)
