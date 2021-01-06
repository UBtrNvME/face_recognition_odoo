"""
CAD AUTOMATION CONTROLLERS
==========================

Developed by QZHUB
"""

import json

from odoo import http
from odoo.http import request

from ..services.cad_extract import extract as cad_extracter, serialize
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

    @http.route("/cad/extract", auth="user", type="http")
    def cad_extract(self):
        image = dataimage_to_base64(request.params.get("file_content"))
        lines, objects, text = cad_extracter(
            image, serialize(request.env["cad.symbol"].search([]))
        )
        return "Result"
