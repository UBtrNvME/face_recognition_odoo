"""
CAD AUTOMATION CONTROLLERS
==========================

Developed by QZHUB
"""

import json

from odoo import http
from odoo.http import request

from ..services.img_manipulation import binary_to_base64


class CadObjectTemplate(http.Controller):
    @http.route("/cad_object_template", auth="public")
    def cad_object_template(self):
        return request.render("cad_automation.cad_automation")

    @http.route("/cad_object_template/create", auth="public")
    def create(self):
        # pylint: disable=method-required-super
        # No need in controller
        params = request.params
        template = request.env["cad.object.template"].create(
            {
                "image_representation": params["file_content"][
                    params["file_content"].find(",") + 1 :
                ],
                "name": "Random_name",
            }
        )
        return template.mask

    @http.route("/cad_object_template/get_list", auth="public")
    def get_list(self):
        templates = request.env["cad.object.template"].search([])
        data = []
        for template in templates:
            data.append(
                {
                    "id": template.id,
                    "name": template.name,
                    "mask": binary_to_base64(template.mask),
                }
            )
        return json.dumps(data)
