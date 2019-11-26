from odoo import models, fields, api


class ProjectRegion(models.Model):
    _name = 'project.region'
    _description = 'Регион проекта'
    _order = 'sequence, id'

    name = fields.Char(string='Название региона', required=True, translate=True)
    code = fields.Integer(stirng='Код региона')
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
