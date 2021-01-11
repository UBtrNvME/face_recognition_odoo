from odoo import api, fields, models


class CadProject(models.Model):
    _name = "cad.project"

    name = fields.Char(string="Cad Project Name")
    diagram_ids = fields.One2many(
        string="Diagrams", comodel_name="cad.diagram", inverse_name="cad_project_id"
    )
