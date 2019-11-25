# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.depends("partner_id")
    def _get_creator_email(self):
        self.creator_email = self.partner_id.email

    def send_approval(self):
        if self.stage_id.name == "На рассмотрении":
            self.stage_id = self.env["project.type"].search([("name", "=", "Одобрено")], limit=1)
            self.date_start = datetime.now()
        template = self.env.ref('gpodem.approval_email_template')
        self.env['mail.template'].browse(template.id).send_mail(self.id)

    def send_reject(self):
        if self.stage_id.name == "На рассмотрении":
            self.stage_id = self.env["project.type"].search([("name", "=", "Отменено")], limit=1)
        template = self.env.ref('gpodem.reject_email_template')
        self.env['mail.template'].browse(template.id).send_mail(self.id)

    def get_default_company(self):
        return self.env['res.company'].browse(1)

    def get_default_partner(self):
        return self.env['res.users'].browse(self.env.uid).partner_id

    @api.model
    def get_default_stage_id(self):
        return self.env["project.type"].search([("name", "=", "На рассмотрении")], limit=1)

    @api.depends("stage_id")
    def _compute_editable_by_user(self):
        if self.stage_id.name in ["Отменено", "Одобрено"]:
            self.editable_by_user = "no"
        else:
            self.editable_by_user = "yes"

    @api.depends("date_start", "date_end")
    def _compute_duration(self):
        if self.date_end and self.date_start:
            self.duration = (self.date_end - self.date_start).total_seconds()

    stage_id = fields.Many2one(comodel_name="project.type", string='Стадия', default=get_default_stage_id)
    manager_id = fields.Many2one(comodel_name="res.partner", string="Менеджер", default=get_default_partner)
    description = fields.Text(string='Описание проекта')
    creator_email = fields.Char(string='Email создателя', compute="_get_creator_email")
    partner_id = fields.Many2one(comodel_name="res.partner", default=get_default_partner)
    company_id = fields.Many2one(comodel_name="res.company", string="Ответственная компания",
                                 default=get_default_company)
    editable_by_user = fields.Selection(selection=[('yes', 'Возможно'), ('no', 'Невозможно')], default='yes',
                                        string="Внесение правок", readonly=True, compute="_compute_editable_by_user")
    url_name = fields.Char(string="Название URL", default="Вебсайт")
    url_field = fields.Char(string="URL на вебсайте")
    category = fields.Selection(string="Категория проекта",
                                selection=[("0", "Здания"), ("1", "Уличное освещение"), ("2", "Центральное теплоснабжение"),
                                           ("3", "Водоснабжение / Канализация"), ("4", "Транспорт"),
                                           ("5", "Энергоменеджмент"),
                                           ("6", "Другое")])
    events_description = fields.Text(string="Описание мероприятии")
    date_start = fields.Datetime(string='Дата начала', index=True)
    date_end = fields.Datetime(string='Дата завершения', index=True)
    duration = fields.Integer(string="Длительность", compute="_compute_duration", readonly=True)
    invested_money = fields.Monetary(string="Инвестиции (₸)")
    energy_type = fields.Selection(string="Тип энергии",
                                   selection=[(0, "Электричество"), (1, "Тепло"),
                                              (2, "Топливо")])
    energy_efficiency = fields.Float(string="Энергоэффективность (%)")
    result_description = fields.Text(string="Как был установлен результат?")
    saved_money = fields.Monetary(string="Сэкомонлено денег (₸)")
    payback_period = fields.Float(string="Простой срок окупаемости (лет)")


    @api.model
    def create(self, values):
        project = super(ProjectProject, self).create(values)
        project.url_field = "/project/" + str(project.id)
        return project
