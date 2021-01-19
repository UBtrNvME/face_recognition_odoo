import json
import logging
from typing import Optional, NewType
from collections import namedtuple
import cv2
import numpy as np
from lxml import html

from odoo import _, api, fields, models
from ..services.img_manipulation import base64_to_ndarray, ndarray_to_base64

_logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------
COLOR_RED = (0, 0, 255)
COLOR_BLUE = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
MASK_THROUGH = 255
MASK_BLOCK = 0
ORIGIN_HTML_TEMPLATE = (
    "<div>"
    '<p><b>x</b> = <span class="value">%s</span><p/>'
    '<p><b>y</b> = <span class="value">%s</span><p/>'
    "</div>"
)

Base64 = NewType("Base64", str)


def _origin_parse_from_html(html_string):
    tree = html.fromstring(html_string)
    span_with_class_value = tree.xpath("//span[@class='value']")
    point = tuple(int(span.text) for span in span_with_class_value)
    assert (
        len(point) == 2
    ), "Length of the tuple is not equal 2, cannot be interpreted as a Point"
    return point


def _apply_difference_on(point, diff):
    if not diff:
        return point
    return (int(diff * point[0]), int(diff * point[1]))

def _calculate_dsize(shape, multiplier):
    return (int(shape[1]*multiplier), int(shape[0]*multiplier))

class CadSymbol(models.Model):
    _name = "cad.symbol"

    name = fields.Char(string="Name of the Cad Object Template", required=True)
    preview = fields.Image(string="Preview", compute="_compute_preview")
    template = fields.Binary(string="Image representation of the Cad Object")
    template_b64 = fields.Text(string="base64")
    mask = fields.Binary(string="Mask of the Cad Object Template", readonly=True)
    threshold = fields.Float(string="Threshold")
    origin = fields.Html(string="Origin")
    connections = fields.Text(string="Json Repr of Connections")
    width = fields.Integer(string="Width of the Template")
    height = fields.Integer(string="Height of the Template")
    ignore_regions = fields.Char(string="Region to Mask", default="[]")
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
    def _onchange_template(self):
        if self.template:
            updated_values = self._initialize_template(self.template)
            self.write(updated_values)

    @api.onchange("ignore_regions", "connections")
    def _onchange_spec_values(self):
        updated_values = {
            "ignore_regions": self.ignore_regions,
            "connections": self.connections,
        }
        self.write(updated_values)

    @api.model
    def create(self, vals):
        template = vals.get("template", None)
        ignore = vals.get("ignore_regions")
        name = vals.get("name", None)

        if name:
            vals.update(name=name.title())

        if template:
            vals.update(self._initialize_template(template))
            mask = self._generate_mask(template, json.loads(ignore))
            vals["mask"] = ndarray_to_base64(mask)

        return super().create(vals)

    def write(self, vals):
        template = vals.get("template")
        if template:
            vals.update(self._initialize_template(template))

        ignore = vals.get("ignore_regions")
        if ignore and self.template_b64:
            mask = self._generate_mask(self.template_b64, json.loads(ignore))
            vals["mask"] = ndarray_to_base64(mask)

        return super().write(vals)

    @api.depends("template_b64", "connections", "ignore_regions")
    def _compute_preview(self):
        for rec in self:
            if rec.template_b64:
                rec.preview = self._generate_preview(
                    rec.template_b64, rec.origin, rec.ignore_regions, rec.connections, 2
                )
            else:
                rec.preview = None

    def _generate_preview(
        self,
        template_b64,
        origin: Optional[str] = None,
        ignore_regions: Optional[str] = None,
        connections: Optional[str] = None,
        scale_ratio: Optional[float] = None,
    ) -> Base64:
        # Assert that template_b64 has been provided,
        # because it is the most important parameter
        assert (
            template_b64 is not None
        ), "Required argument `template_b64` was not provided"

        ndarray = base64_to_ndarray(template_b64)
        new_size = ndarray.shape
        if scale_ratio:
            new_size = _calculate_dsize(new_size, scale_ratio)
            ndarray = cv2.resize(ndarray, new_size, interpolation=cv2.INTER_NEAREST)

        if ignore_regions:
            mask = self._generate_mask(template_b64, json.loads(ignore_regions))
            resized_mask = cv2.resize(mask, new_size, interpolation=cv2.INTER_NEAREST)
            ndarray = np.array(
                np.where(resized_mask == MASK_THROUGH, ndarray, COLOR_BLUE), dtype=np.uint8
            )

        if origin:
            parsed_origin = _origin_parse_from_html(origin)
            cv2.circle(ndarray, _apply_difference_on(parsed_origin, scale_ratio), 2, COLOR_RED, -1)

        if connections:
            connections = json.loads(connections)
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
                    center=_apply_difference_on((connection["pos"]["x"], connection["pos"]["y"]), scale_ratio),
                    radius=2,
                    color=COLOR_GREEN,
                    thickness=-1,
                )
        return ndarray_to_base64(ndarray)

    @staticmethod
    def _initialize_template(template):
        shape = base64_to_ndarray(template).shape
        return {
            "template_b64": template,
            "width": shape[1],
            "height": shape[0],
            "origin": ORIGIN_HTML_TEMPLATE % (shape[1] // 2, shape[0] // 2),
        }

    @staticmethod
    def _generate_mask(template, ignore):
        template = base64_to_ndarray(template)

        mask = np.full(template.shape, MASK_THROUGH, dtype=np.uint8)
        for contour in ignore:
            cv2.fillPoly(mask, pts=[np.array(contour)], color=MASK_BLOCK)
        return mask

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
