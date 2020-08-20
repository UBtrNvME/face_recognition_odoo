# -*- coding: utf-8 -*-

import base64
import json
import os
from io import BytesIO

import face_recognition
import numpy as np
from PIL import Image

from odoo import api, fields, models


class FaceRecognition(models.TransientModel):
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
            print("This picture has no faces")
            return
        if len(unknown_encoding) > 1:
            print("This picture has more than 1 face")
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
        print(base64string)
        image = Image.open(BytesIO(base64.b64decode(base64string)))
        print(image)
        return np.array(image.convert("RGB"))

    @api.model
    def compare(self, unknown_image, partner_id):
        partner = self.env["res.partner"].browse(partner_id)[0]
        print(partner.face_model_id.face_encodings)
        if not partner.face_model_id or not partner.face_model_id.face_encodings or \
                partner.face_model_id.face_encodings == "{}":
            return -3
        unknown_encoding = face_recognition.face_encodings(self.load_image_base64(unknown_image), None, 20, "large")
        if not unknown_encoding:
            print("This picture has no faces")
            return -1
        if len(unknown_encoding) > 1:
            print("This picture has more than 1 face")
            return -2
        face_encodings = json.loads(str(partner.face_model_id.face_encodings))
        known_encodings_of_partner = [np.array(face_encodings[attach_id]) for attach_id in face_encodings]
        results = face_recognition.compare_faces(known_encodings_of_partner, unknown_encoding[0], 0.4)
        print(results)
        percentage = len(list(filter(lambda x: x, results))) / len(results) * 100
        return percentage

    @api.model
    def find_id_of_the_user_on_the_image(self, face_image: str):
        encoding, result = self._check_image_for_face_and_return_if_only_one_encoding(face_image)
        if not result:
            return -1, None
        if result == -2:
            return -2, None
        user = self.env['res.partner.face.model'].sudo(True).compare_with_unknown(encoding)
        print(3)
        if not user:
            print(3.2)
            face_model = self.env['res.partner.face.model'].sudo(True).create_temporary_face_model({
                "image_in_base64": face_image,
                "face_encoding"  : encoding,
            })
            print(3.3, face_model)
            return -3, face_model
        print(4)
        return user, None

    @staticmethod
    def _is_face_on_encoding(encoding):
        return bool(encoding)

    @staticmethod
    def _is_only_one_face(encoding):
        return not len(encoding) > 1

    def _check_image_for_faces_and_return_encodings(self, image):
        encoding = face_recognition.face_encodings(self.load_image_base64(image), None, 20, "large")
        if not self._is_face_on_encoding(encoding):
            return [], False
        return encoding, True

    def _check_image_for_face_and_return_if_only_one_encoding(self, image):
        encodings, result = self._check_image_for_faces_and_return_encodings(image)
        if not result:
            return [], -2
        if self._is_only_one_face(encodings):
            return encodings, True
        else:
            return [], False

# # =====================================
# #   Face Recognition Changed Functions
# # =====================================
# def _face_encodings(face_image, known_face_locations=None, num_jitters=1, model="small"):
#     """
#     Given an image, return the 128-dimension face encoding for each face in the image.
#
#     :param face_image: The image that contains one or more faces
#     :param known_face_locations: Optional - the bounding boxes of each face if you already know them.
#     :param num_jitters: How many times to re-sample the face when calculating encoding. Higher is more accurate,
#     but slower (i.e. 100 is 100x slower)
#     :return: A list of 128-dimensional face encodings (one for each face in the image)
#     """
#     raw_landmarks = face_recognition._raw_face_landmarks(face_image, known_face_locations, model)
#     return [np.array(face_recognition.face_encoder.compute_face_descriptor(face_image, raw_landmark_set,
#     num_jitters)) for raw_landmark_set in raw_landmarks]
