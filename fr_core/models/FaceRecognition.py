# -*- coding: utf-8 -*-

import base64
import json
import os
from io import BytesIO
import face_recognition
import numpy as np
from PIL import Image
from ..scripts import fr_scripts as frs
import math
from odoo import api, fields, models
import cv2


class FaceRecognition(models.AbstractModel):
    _name = 'face.recognition'

    path = ""
    if os.getenv("IS_DOCKER"):
        path = "/var/lib/odoo/"
    loaded_image = fields.Binary(string='Loaded image', attachment=True)
    loaded_image_name = fields.Char(string="Loaded image name")
    partner_id = fields.Many2one(comodel_name="res.partner", string="Partner", readonly=True)
    run_from_rn = fields.Boolean(string="Run from React Native")
    percentage = fields.Float(string="Percentage")

    @api.model
    def create(self, vals):
        if vals.get("run_from_rn"):
            vals = self.calculate_percentage(vals)
            fr = super(FaceRecognition, self).create(vals)
        else:
            fr = super(FaceRecognition, self).create(vals)
            fr.compare()
        return fr

    def calculate_percentage(self, vals):
        image_path = self.path + vals["loaded_image_name"]
        with open(image_path, "wb") as unknown_image_file:
            unknown_image_file.write(base64.b64decode(vals["loaded_image"]))
        unknown_encoding = face_recognition.face_encodings(
            face_recognition.load_image_file(image_path))
        if not unknown_encoding:
            return
        if len(unknown_encoding) > 1:
            return
        known_encodings = []
        for attachment in self.env["hr.employee"].browse(vals["partner_id"]).attachment_ids:
            known_encodings.append(face_recognition.face_encodings(
                face_recognition.load_image_file(attachment._full_path(attachment.store_fname)))[0])
        results = face_recognition.compare_faces(known_encodings, unknown_encoding[0], 0.4)
        vals["percentage"] = len(list(filter(lambda x: x, results))) / len(results) * 100

        unknown_image_file.close()
        os.remove(image_path)

        return vals

    def load_image_base64(self, base64string):
        image = Image.open(BytesIO(base64.b64decode(base64string)))
        return np.array(image.convert("RGB"))

    @api.model
    def compare(self, unknown_image, partner_id):
        partner = self.env["res.partner"].browse(partner_id)[0]
        if not partner.face_model_id or not partner.face_model_id.face_encodings or \
                partner.face_model_id.face_encodings == "{}":
            return -3
        unknown_encoding = face_recognition.face_encodings(self.load_image_base64(unknown_image), None, 20, "large")
        if not unknown_encoding:
            return -1
        if len(unknown_encoding) > 1:
            return -2
        face_encodings = json.loads(str(partner.face_model_id.face_encodings))
        known_encodings_of_partner = [np.array(face_encodings[attach_id]) for attach_id in face_encodings]
        results = face_recognition.compare_faces(known_encodings_of_partner, unknown_encoding[0], 0.4)
        percentage = len(list(filter(lambda x: x, results))) / len(results) * 100
        return percentage

    @api.model
    def find_id_of_the_user_on_the_image(self, face_image: str, face_location):
        encoding, result = self._check_image_for_face_and_return_if_only_one_encoding(face_image, face_location)
        if not result:
            return -1, None
        if result == -2:
            return -2, None
        user = self.env['res.partner.face.model'].sudo(True).compare_with_unknown(encoding)
        if not user:
            face_model = self.env['res.partner.face.model'].sudo(True).create_temporary_face_model({
                "image_in_base64": face_image,
                "face_encoding": encoding,
            })
            return -3, face_model
        return user, None

    @staticmethod
    def _is_face_on_encoding(encoding):
        return bool(encoding)

    @staticmethod
    def _is_only_one_face(encoding):
        return not len(encoding) > 1

    def _check_image_for_faces_and_return_encodings(self, image, face_location):
        encoding = face_recognition.face_encodings(self.load_image_base64(image), face_location, 20, "large")
        if not self._is_face_on_encoding(encoding):
            return [], False
        return encoding, True

    def _check_image_for_face_and_return_if_only_one_encoding(self, image, face_location):
        encodings, result = self._check_image_for_faces_and_return_encodings(image, face_location)
        if not result:
            return [], -2
        if self._is_only_one_face(encodings):
            return encodings, True
        else:
            return [], False

    def get_face_locations_within_ellipse(self, image, image_dimensions=None):
        if image_dimensions is None:
            image_dimensions = dict(x=400, y=300)

        def _checkpoint(h, k, x, y, a, b):
            # checking the equation of
            # ellipse with the given point
            p = ((math.pow((x - h), 2) // math.pow(a, 2)) +
                 (math.pow((y - k), 2) // math.pow(b, 2)))

            return p

        image_arr = self.load_image_base64(image)
        bound_tuples = face_recognition.face_locations(image_arr)
        rectangles = []
        for tuple in bound_tuples:
            rect_points = [(tuple[3], tuple[0]), (tuple[1], tuple[0]),
                           (tuple[3], tuple[2]), (tuple[1], tuple[2])]
            rectangles.append(rect_points)

        center_by_x = image_dimensions['x'] / 2
        center_by_y = image_dimensions['y'] / 2 + (image_dimensions['y']//10)
        radius_x = int(image_dimensions['x'] * 0.20)
        radius_y = int(image_dimensions['y'] * 0.35)
        res = []
        for i in range(len(rectangles)):
            is_inside = True
            for x, y in rectangles[i]:
                inside_outer_ellipse = _checkpoint(center_by_x, center_by_y, x, y, radius_y, radius_x) < 1
                inside_inner_ellipse = _checkpoint(center_by_x, center_by_y, x, y, radius_y / 2, radius_x / 2) < 1
                if not inside_outer_ellipse or inside_inner_ellipse:
                    is_inside = False
                    break
            if is_inside:
                res.append(bound_tuples[i])
        return res

    def determine_face_raccourcir(self, face_landmarks):
        if face_landmarks:
            raccourcirs = {(-5.000, 5.000): 'en_face', (-45.000, -20.000): 'left_profile',
                           (20.000, 45.000): 'right_profile'}
            angle = frs.compute_face_angle(face_landmarks=face_landmarks)
            for bleft, bright in raccourcirs:
                if bright > angle > bleft:
                    return raccourcirs[(bleft, bright)]
        return False

    def get_face_landmarks(self, image):
        image_arr = self.load_image_base64(image)
        return face_recognition.face_landmarks(face_image=image_arr)

    def is_face_smiling(self, image, face_location):
        image_arr = self.load_image_base64(image)
        if len(face_location) > 1 or len(face_location) < 1:
            return False
        for top, right, bottom, left in face_location:
            return frs.are_faces_smiling(image_arr, face_location)
