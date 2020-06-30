# -*- coding: utf-8 -*-

import base64
import os

import cv2
import face_recognition
import magic
from vidgear.gears import VideoGear

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FaceRecognition(models.TransientModel):
    _name = 'face.recognition'

    path = ""
    if os.getenv("IS_DOCKER"):
        path = "/var/lib/odoo/"
    loaded_image = fields.Binary(string='Loaded image', attachment=True)
    loaded_image_name = fields.Char(string="Loaded image name")
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", readonly=True)
    run_from_rn = fields.Boolean(string="Run from React Native")
    percentage = fields.Float(string="Percentage")

    def camera_capture(self):
        # enable enablePiCamera boolean flag to access PiGear API backend
        stream = VideoGear().start()
        # loop over
        while True:
            # read frames from stream
            frame = stream.read()
            # check for frame if Nonetype
            if frame is None:
                break
            # {do something with the frame here}
            key = cv2.waitKey(1) & 0xFF
            if key == ord("s"):
                is_success, im_buff_file = cv2.imencode('.jpg', frame)
                image = im_buff_file
                # close output window
                cv2.destroyAllWindows()
                # safely close video stream
                stream.stop()
                print(image, type(image), sep="\n")
                return ("image_eid%d_%d.jpg" % (
                    self.employee_id.id, len(self.employee_id.attachment_ids) + 1), base64.b64encode(image))

            # Show output window
            cv2.imshow("Output Frame", frame)
            # check for 'q' key if pressed
            if key == ord("q"):
                break
        # close output window
        cv2.destroyAllWindows()
        # safely close video stream
        stream.stop()

    @api.model
    def create(self, vals):
        if vals.get("run_from_rn"):
            vals = self.calculate_percentage(vals)
        fr = super(FaceRecognition, self).create(vals)
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
        for attachment in self.env["hr.employee"].browse(vals["employee_id"]).attachment_ids:
            known_encodings.append(face_recognition.face_encodings(
                face_recognition.load_image_file(attachment._full_path(attachment.store_fname)))[0])
        results = face_recognition.compare_faces(known_encodings, unknown_encoding[0], 0.4)
        vals["percentage"] = len(list(filter(lambda x: x, results))) / len(results) * 100

        unknown_image_file.close()
        os.remove(image_path)

        return vals

    def compare(self):
        image_path = self.path + self.loaded_image_name
        with open(image_path, "wb") as unknown_image_file:
            unknown_image_file.write(base64.b64decode(self.loaded_image))
        unknown_encoding = face_recognition.face_encodings(face_recognition.load_image_file(image_path))
        if not unknown_encoding:
            print("This picture has no faces")
            raise ValidationError("This picture has no faces")
        if len(unknown_encoding) > 1:
            print("This picture has more than 1 face")
            raise ValidationError("This picture has more than 1 face")
        known_encodings = []
        for attachment in self.employee_id.attachment_ids:
            known_encodings.append(face_recognition.face_encodings(
                face_recognition.load_image_file(attachment._full_path(attachment.store_fname)))[0])
        results = face_recognition.compare_faces(known_encodings, unknown_encoding[0], 0.4)
        percentage = len(list(filter(lambda x: x, results))) / len(results) * 100
        view = self.env.ref('face_recognition.face_recognition_message_wizard')
        context = dict(self._context or {})
        context["default_name"] = self.employee_id.user_id.name
        context["default_percentage"] = percentage
        context["default_message"] = "This employee is %s by %d percent probability" % (
            self.employee_id.name, percentage)
        context["default_image"] = self.loaded_image
        context["default_employee_id"] = self.employee_id.id
        context["default_mimetype"] = magic.Magic(mime=True).from_file(image_path)
        context["default_image_name"] = image_path

        unknown_image_file.close()
        os.remove(image_path)

        return {
            "name"     : "Result",
            "type"     : "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "face.recognition.message.wizard",
            "views"    : [(view.id, "form")],
            # "view_id": view.id,
            "target"   : "new",
            "context"  : context
        }
