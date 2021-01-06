from odoo import api, fields, models

import cv2
import numpy as np

from ..services.cad_helpers import base64_to_ndarray, calculate_threshold


class CadWizardThresholdCalculator(models.TransientModel):
    _name = "cad.wizard.threshold.calculator"

    def _load_default_image(self):
        return (
            self.env["cad.defaults"]
            .search([["name", "=", "DEFAULT_TEST_IMAGE"]])
            .get_value()
        )

    cad_object_id = fields.Integer(string="Cad Object ID")
    test_image = fields.Text(string="Test Image", default=_load_default_image)
    template = fields.Text(string="Template")
    template_mask = fields.Text(string="Template Mask")
    occurrence_on_test_image = fields.Integer(string="Occurrence on test image")

    def calculate(self):
        result = calculate_threshold(self.test_image, self.template, self.template_mask)
        thresh = 1
        upper = 1

        occurrence = np.count_nonzero(np.where(result.copy() >= thresh))
        while occurrence <= self.occurrence_on_test_image:
            occurrence = np.count_nonzero(np.where(result.copy() >= thresh),)
            if upper == 0 and occurrence == self.occurrence_on_test_image:
                upper = thresh
            thresh -= 0.05
        lower = thresh
        self.env["cad.symbol"].browse(self.cad_object_id).threshold = (
            upper + lower
        ) / 2
        return
