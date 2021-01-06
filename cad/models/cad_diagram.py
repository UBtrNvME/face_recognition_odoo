from odoo import _, api, fields, models

from ..services.cad_extract import extract, serialize
from ..services.img_manipulation import base64_pdf_to_base64_image, base64_to_ndarray


class CadDiagram(models.Model):
    _name = "cad.diagram"

    name = fields.Char(string="P&ID name")
    diagram_type = fields.Selection(
        string="Diagram Type", selection=[("pandid", "P&ID"), ("scheme", "Scheme")]
    )
    attachment = fields.Binary(string="File attachment", public=True)
    content_data = fields.Text(string="Content Data")
    is_parsed_to_nextcloud = fields.Boolean(
        string="Is Parsed to Nextcloud", default=False
    )

    @api.model
    def parse_to_data(self, id):
        symbols = serialize(self.env["cad.symbol"].search([]))
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
            return extract(datas, symbols)

    def delayed_task(self):
        delayed = (
            self.env["cad.diagram"]
            .with_delay(channel="root", description="parse data")
            .parse_to_data(self.id)
        )
