from odoo import models, fields, api


class ProjectType(models.Model):
    _name = 'project.type'
    _description = 'Стадия проекта'
    _order = 'sequence, id'

    name = fields.Char(string='Название стадии', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
