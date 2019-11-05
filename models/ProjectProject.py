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
        if self.stage_id.name == "На рассмотрении":
            self.stage_id = self.env["project.type"].search([("name", "=", "Одобрено")], limit=1)
        template = self.env.ref('gpodem.approval_email_template')
        self.env['mail.template'].browse(template.id).send_mail(self.id)

    @api.one
    def send_reject(self):
        if self.stage_id.name == "На рассмотрении":
            self.stage_id = self.env["project.type"].search([("name", "=", "Отменено")], limit=1)
        template = self.env.ref('gpodem.reject_email_template')
        self.env['mail.template'].browse(template.id).send_mail(self.id)

    @api.model
    def get_default_company(self):
        return self.env['res.company'].browse(1)

    @api.model
    def get_default_partner(self):
        return self.env['res.users'].browse(self.env.uid).partner_id

    @api.model
    def get_default_stage_id(self):
        return self.env["project.type"].search([("name", "=", "На рассмотрении")], limit=1)

    stage_id = fields.Many2one(comodel_name="project.type", string='Стадия', default=get_default_stage_id)
    manager_id = fields.Many2one(comodel_name="res.partner", string="Менеджер", default=get_default_partner)
    description = fields.Text(string='Описание проекта')
    creator_email = fields.Char(string='Email создателя', compute="_get_creator_email")
    partner_id = fields.Many2one(comodel_name="res.partner", default=get_default_partner)
    company_id = fields.Many2one(comodel_name="res.company", string="Ответственная компания",
                                 default=get_default_company)
