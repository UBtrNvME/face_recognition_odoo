# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError
import face_recognition
import base64
import magic
import os


class FaceRecognition(models.Model):
    _name = 'face.recognition'

    loaded_image = fields.Binary(string='Loaded image', attachment=True)
    loaded_image_name = fields.Char(string="Loaded image name")
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", readonly=True)
    run_from_rn = fields.Boolean(string="Run from React Native")
    percentage = fields.Float(string="Percentage")

    @api.model
    def create(self, vals):
        if vals.get("run_from_rn"):
            vals = self.calculate_percentage(vals)
        fr = super(FaceRecognition, self).create(vals)
        return fr

    def calculate_percentage(self, vals):
        with open(vals["loaded_image_name"], "wb") as unknown_image_file:
            unknown_image_file.write(base64.b64decode(vals["loaded_image"]))
        unknown_encoding = face_recognition.face_encodings(face_recognition.load_image_file(vals["loaded_image_name"]))
        if not unknown_encoding:
            print("This picture has no faces")
            return
        if len(unknown_encoding) > 1:
            print("This picture has more than 1 face")
            return
        known_encodings = []
        for attachment in self.env["hr.employee"].browse(vals["employee_id"]).attachment_ids:
            known_encodings.append(face_recognition.face_encodings(
                face_recognition.load_image_file(attachment._full_path(attachment.store_fname)))[0])
        results = face_recognition.compare_faces(known_encodings, unknown_encoding[0])
        vals["percentage"] = len(list(filter(lambda x: x, results))) / len(results) * 100

        unknown_image_file.close()
        os.remove(vals["loaded_image_name"])

        return vals

    def compare(self):
        with open(self.loaded_image_name, "wb") as unknown_image_file:
            unknown_image_file.write(base64.b64decode(self.loaded_image))
        unknown_encoding = face_recognition.face_encodings(face_recognition.load_image_file(self.loaded_image_name))
        if not unknown_encoding:
            print("This picture has no faces")
            raise ValidationError("This picture has no faces")
            return
        if len(unknown_encoding) > 1:
            print("This picture has more than 1 face")
            raise ValidationError("This picture has more than 1 face")
            return
        known_encodings = []
        for attachment in self.employee_id.attachment_ids:
            known_encodings.append(face_recognition.face_encodings(
                face_recognition.load_image_file(attachment._full_path(attachment.store_fname)))[0])
        results = face_recognition.compare_faces(known_encodings, unknown_encoding[0])
        percentage = len(list(filter(lambda x: x, results))) / len(results) * 100
        view = self.env.ref('face_recognition.face_recognition_message_wizard')
        context = dict(self._context or {})
        context["default_name"] = self.employee_id.user_id.name
        context["default_percentage"] = percentage
        context["default_message"] = "This employee is %s by %d percent probability" % (
            self.employee_id.user_id.name, percentage)
        context["default_image"] = self.loaded_image
        context["default_employee_id"] = self.employee_id.id
        context["default_mimetype"] = magic.Magic(mime=True).from_file(self.loaded_image_name)
        context["default_image_name"] = self.loaded_image_name

        unknown_image_file.close()
        os.remove(self.loaded_image_name)

        return {
            "name": "Result",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "face.recognition.message.wizard",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "context": context
        }
