# -*- coding: utf-8 -*-

from odoo import api, fields, models
from ..services.img_manipulation import (
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
    mask = fields.Image(string="Mask of the Cad Object Template", readonly=True)

    @staticmethod
    def generate_mask(image):
        image_b64 = image
        ndarray = base64_to_ndarray(image_b64)
        return ndarray_to_base64(
            cv2.threshold(ndarray, 100, 250, cv2.THRESH_BINARY_INV)[1])

    @api.model
    def create(self, vals):
        if vals.get("image_representation"):
            vals['mask'] = self.generate_mask(image=vals['image_representation'])
        return super().create(vals)
