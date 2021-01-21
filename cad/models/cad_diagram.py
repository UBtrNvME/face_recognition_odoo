import json

from odoo import _, api, fields, models

from ..services import cad_helpers
from ..services.cad_extract import extract, serialize
from ..services.img_manipulation import (
    base64_pdf_to_base64_image,
    base64_to_ndarray,
    ndarray_to_base64,
)


class CadDiagram(models.Model):
    _name = "cad.diagram"
    _inherit = ["image.mixin", "nextcloud.wrapper.mixin"]

    DIAGRAM_STATES = [("draft", "Draft"), ("unsync", "Unsynced"), ("sync", "Synced")]

    name = fields.Char(string="P&ID name")
    cad_project_id = fields.Many2one(
        string="Cad Project ID", comodel_name="cad.project"
    )
    diagram_type = fields.Selection(
        string="Diagram Type", selection=[("pandid", "P&ID"), ("scheme", "Scheme")]
    )
    attachment = fields.Binary(string="File attachment", public=True)
    content_data = fields.Text(string="Content Data")
    state = fields.Selection(
        string="State of Diagram", selection=DIAGRAM_STATES, default="draft"
    )
    image_1920 = fields.Image(string="Resulting Image", max_height=7680, max_width=7680)
    nextcloud_path = fields.Char(string="Nextcloud path")

    @api.model
    def parse_to_data(self, id):
        symbols = serialize(self.env["cad.symbol"].search([("active", "=", True)]))
        Attachment = self.env["ir.attachment"].sudo(True)
        attachment = Attachment.search(
            [
                ("res_model", "=", "cad.diagram"),
                ("res_field", "=", "attachment"),
                ("res_id", "=", id),
            ]
        )
        datas = attachment.datas
        if attachment.mimetype == "application/pdf":
            datas = base64_pdf_to_base64_image(datas)
        if attachment:
            result = extract(datas, symbols)
            if result:
                ndarray = base64_to_ndarray(datas)
                diagram = self.env["cad.diagram"].browse(id)
                resulting_image = cad_helpers.draw_objects_on_image(
                    ndarray, result.objects
                )
                diagram.image_1920 = ndarray_to_base64(resulting_image)
                diagram.content_data = result
                return "Success"
            else:
                return "No Active Templates"
        else:
            return "False"

    def delayed_task(self):
        delayed = (
            self.env["cad.diagram"]
            .with_delay(channel="root", description="parse data")
            .parse_to_data(self.id)
        )
