import json
import logging

from odoo import _, api, fields, models

import cv2
import numpy as np

from ..services.img_manipulation import base64_to_ndarray, ndarray_to_base64

_logger = logging.getLogger(__name__)

COLOR_RED = (0, 0, 255)
COLOR_BLUE = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
MASK_THROUGH = 255
MASK_BLOCK = 0


class CadSymbol(models.Model):
    _name = "cad.symbol"

    name = fields.Char(string="Name of the Cad Object Template", required=True)
    preview = fields.Image(string="Preview", compute="_compute_preview")
    template = fields.Binary(string="Image representation of the Cad Object")
    template_b64 = fields.Text(string="base64")
    mask = fields.Binary(string="Mask of the Cad Object Template", readonly=True)
    threshold = fields.Float(string="Threshold")
    origin = fields.Char(string="Origin")
    connections = fields.Text(string="Json Repr of Connections")
    width = fields.Integer(string="Width of the Template")
    height = fields.Integer(string="Height of the Template")
    ignore_regions = fields.Text(string="Region to Mask")
    mirror = fields.Selection(
        string="Mirror",
        selection=[
            ("none", "None"),
            ("vertical", "Vertical"),
            ("horizontal", "Horizontal"),
        ],
        default="none",
    )

    @api.onchange("template")
    def onchange_template(self):
        for rec in self:
            rec.template_b64 = rec.template

    @api.model
    def create(self, vals):
        template = vals.get("template")
        if template:
            vals.update(self._initialize_template(template))

        ignore = vals.get("ignore_regions") or "[]"
        if template:
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
                        np.where(mask == MASK_THROUGH, ndarray, (0, 255, 0)),
                        dtype=np.uint8,
                    )

                if rec.origin:
                    origin = json.loads(rec.origin)
                    cv2.circle(ndarray, tuple(origin), 2, COLOR_RED, -1)

                if rec.connections:
                    connections = json.loads(rec.connections)

                    for connection in connections:
                        if (
                            isinstance(connection["pos"]["x"], str)
                            or isinstance(connection["pos"]["y"], str)
                            or isinstance(connection["dir"]["x"], str)
                            or isinstance(connection["dir"]["y"], str)
                        ):
                            continue

                        cv2.circle(
                            img=ndarray,
                            center=(connection["pos"]["x"], connection["pos"]["y"]),
                            radius=2,
                            color=COLOR_GREEN,
                            thickness=-1,
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
        template = vals.get("template")
        if template:
            vals.update(self._initialize_template(template))

        ignore = vals.get("ignore_regions")
        if ignore and self.template_b64:
            mask = self._generate_mask(self.template_b64, json.loads(ignore))
            vals["mask"] = ndarray_to_base64(mask)

        return super().write(vals)

    def calculate_threshold(self):
        return {"model": "ir.action"}

    @api.model
    def get_template(self, rid=-1):
        if rid:
            template = (
                self.env["ir.attachment"]
                .sudo(True)
                .search(
                    [
                        ["res_model", "=", "cad.symbol"],
                        ["res_id", "=", rid],
                        ["res_field", "=", "template"],
                    ]
                )
            )
            return template.datas
        return None

    # ----------------------------------------------------------------------------------
    # Wizards

    def open_calculate_threshold(self):
        return {
            "view_mode": "form",
            "res_model": "cad.wizard.threshold.calculator",
            "type": "ir.actions.act_window",
            "name": _("Calculate Threshold"),
            "context": {
                "default_cad_object_id": self.id,
                "default_template": self.template_b64,
                "default_template_mask": self.mask,
            },
            "target": "new",
        }
