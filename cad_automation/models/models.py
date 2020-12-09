import json
import logging

from odoo import api, fields, models

import cv2
import numpy as np

from ..services.img_manipulation import base64_to_ndarray, ndarray_to_base64

_logger = logging.getLogger(__name__)

COLOR_RED = (0, 0, 255)
COLOR_BLUE = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
MASK_THROUGH = 210
MASK_BLOCK = 0


class CadSymbol(models.Model):
    _name = "cad.symbol"

    name = fields.Char(string="Name of the Cad Object Template", required=True)
    preview = fields.Binary(string="Preview", compute="_compute_preview")
    template = fields.Binary(string="Image representation of the Cad Object")
    template_b64 = fields.Text(string="base64")
    mask = fields.Binary(string="Mask of the Cad Object Template", readonly=True)
    threshold = fields.Float(string="Threshold")
    origin = fields.Char(string="Origin")
    connections = fields.Text(string="Json Repr of Connections")
    width = fields.Integer(string="Width of the Template")
    height = fields.Integer(string="Height of the Template")
    ignore_regions = fields.Text(string="Region to Mask")
    active = fields.Boolean(string="Boolean")

    @api.onchange("template")
    def onchange_template(self):
        for rec in self:
            rec.template_b64 = rec.template

    @api.model
    def create(self, vals):
        if template := vals.get("template"):
            vals.update(self._initialize_template(template))

        ignore = vals.get("ignore_regions")
        if ignore and template:
            mask = self._generate_mask(template, json.loads(ignore))
            vals["mask"] = ndarray_to_base64(mask)

        return super().create(vals)

    @api.depends("template_b64", "connections", "ignore_regions")
    def _compute_preview(self):
        for rec in self:
            if rec.template_b64:
                ndarray = base64_to_ndarray(rec.template_b64)

                if rec.ignore_regions:
                    mask = self._generate_mask(
                        rec.template_b64, json.loads(rec.ignore_regions)
                    )
                    ndarray = np.array(
                        np.where(mask == MASK_THROUGH, ndarray, COLOR_BLUE),
                        dtype=np.uint8,
                    )

                if rec.origin:
                    origin = json.loads(rec.origin)
                    cv2.circle(ndarray, tuple(origin), 2, COLOR_RED, -1)

                if rec.connections:
                    connections = json.loads(rec.connections)
                    print(connections)
                    for connection in connections:
                        cv2.circle(
                            ndarray, (connection["pos"]["x"], connection["pos"]["y"]), 2, COLOR_GREEN, -1
                        )

                rec.preview = ndarray_to_base64(ndarray)
            else:
                rec.preview = None

    @staticmethod
    def _initialize_template(template):
        shape = base64_to_ndarray(template).shape
        return {
            "template_b64": template,
            "width": shape[1],
            "height": shape[0],
            "origin": f"[{shape[1] // 2},{shape[0] // 2}]",
        }

    @staticmethod
    def _generate_mask(template, ignore):
        template = base64_to_ndarray(template)

        mask = np.full(template.shape, MASK_THROUGH, dtype=np.uint8)
        for contour in ignore:
            cv2.fillPoly(mask, pts=[np.array(contour)], color=MASK_BLOCK)
        return mask

    def write(self, vals):
        if template := vals.get("template"):
            vals.update(self._initialize_template(template))

        ignore = vals.get("ignore_regions")
        if ignore and self.template_b64:
            mask = self._generate_mask(self.template_b64, json.loads(ignore))
            vals["mask"] = ndarray_to_base64(mask)

        return super().write(vals)
