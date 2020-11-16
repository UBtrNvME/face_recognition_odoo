# -*- coding: utf-8 -*-

from odoo import api, fields, models
from extra.qzhub_deep_learning.cad_automation.services.img_manipulation import (
    base64_to_ndarray, ndarray_to_base64
)
import cv2
import logging

_logger = logging.getLogger(__name__)

class CadObjectTemplate(models.Model):
    _name = "cad.object.template"

    name = fields.Char(string="Name of the Cad Object Template", required=True)
    image_representation = fields.Image(string="Image representation of the Cad Object",
                                        required=True)
    mask = fields.Image(string="Mask of the Cad Object Template", compute="generate_mask")

    @api.depends("image_representation")
    def generate_mask(self):
        for cot in self:
            image_b64 = cot.image_representation
            ndarray = base64_to_ndarray(image_b64)
            cot.mask = ndarray_to_base64(
                cv2.threshold(ndarray, 100, 250, cv2.THRESH_BINARY_INV)[1])
