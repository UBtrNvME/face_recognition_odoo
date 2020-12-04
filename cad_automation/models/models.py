import json
import logging

from odoo import api, fields, models

import cv2

from ..services.img_manipulation import base64_to_ndarray, ndarray_to_base64

_logger = logging.getLogger(__name__)

COLOR_RED = (0, 0, 255)
COLOR_BLUE = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)


class CadSymbol(models.Model):
    _name = "cad.symbol"

    name = fields.Char(string="Name of the Cad Object Template", required=True)
    preview = fields.Binary(string="Preview", compute="_compute_preview")
    template = fields.Image(string="Image representation of the Cad Object")
    mask = fields.Image(string="Mask of the Cad Object Template", readonly=True)
    threshold = fields.Integer(string="Threshold")
    origin = fields.Char(string="Origin")
    connections = fields.Text(string="Json Repr of Connections")
    width = fields.Integer(string="Width of the Template")
    height = fields.Integer(string="Height of the Template")

    @staticmethod
    def generate_mask(image):
        image_b64 = image
        ndarray = base64_to_ndarray(image_b64)
        return ndarray_to_base64(
            cv2.threshold(ndarray, 100, 250, cv2.THRESH_BINARY_INV)[1]
        )

    @api.model
    def create(self, vals):
        if vals.get("image_representation"):
            vals["mask"] = self.generate_mask(image=vals["image_representation"])
        return super().create(vals)

    @api.depends("template", "connection", "origin")
    def _compute_preview(self):
        ndarray = base64_to_ndarray(self.template)
        origin = json.loads(self.origin)
        connections = json.loads(self.connections)
        cv2.circle(ndarray, origin, 2, COLOR_RED, -1)
        for connection in connections:
            cv2.circle(ndarray, connection["pos"], 2, COLOR_GREEN, -1)
        self.preview = ndarray
