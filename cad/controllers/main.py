"""
CAD AUTOMATION CONTROLLERS
==========================

Developed by QZHUB
"""

import json

from odoo import http
from odoo.http import request

from ..services.cad_extract import main as cad_extracter, serialize
from ..services.cad_helpers import _render_mask_with_points
from ..services.img_manipulation import (
    base64_to_ndarray,
    binary_to_base64,
    dataimage_to_base64,
    ndarray_to_base64,
)


class CadObjectTemplate(http.Controller):
    @http.route("/cad_object_template", auth="user")
    def cad_object_template(self):
        return request.render("cad.cad")

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

    @http.route("/cad/mask/edit", auth="public", type="json")
    def image_edit(self):
        image = request.params.get("template")
        points = request.params.get("points")
        if points and len(points):
            image = base64_to_ndarray(image)
            image = _render_mask_with_points(image, points)
            image = ndarray_to_base64(image)

        result = f"data:image/png;base64, {image.decode('utf-8') if isinstance(image, bytes) else image}"
        return result

    @http.route("/cad/extract", auth="user")
    def cad_extract(self):
        image = dataimage_to_base64(request.params.get("file_content"))
        lines, objects, text = cad_extracter(
            image, serialize(request.env["cad.symbol"].search([]))
        )
        return f"<div><h1>OBJECTS</h1><p>{objects}</p></div><div><h1>LINES</h1><p>{lines}</p></div><div><h1>TEXT</h1><p>{text}</p></div>"
