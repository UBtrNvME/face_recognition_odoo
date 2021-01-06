from odoo import fields, models


class NextcloudConfigWizardInherit(models.TransientModel):
    _inherit = "res.config.settings"

    cad_parsing_destination_path = fields.Char(
        string="Nextcloud Parsing Destination Path",
        config_parameter="cad.nextcloud_parse_destination",
    )
    cad_parsing_source_path = fields.Char(
        string="Nextcloud Parsing Source Path",
        config_parameter="cad.nextcloud_parse_source",
    )
