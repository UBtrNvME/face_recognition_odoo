# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import api, fields, models
import base64


class FaceRecognitionMessageWizard(models.TransientModel):
    _name = "face.recognition.message.wizard"

    name = fields.Char(string="Name", readonly=True)
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee")
    image = fields.Binary(string="Image")
    mimetype = fields.Char(string="Mimetype")
    image_name = fields.Char(string="Image name")
    percentage = fields.Float(string="Percentage")
    message = fields.Char(string="Message", compute="_get_message")

    def add_photo(self):
        attachment = self.env['ir.attachment'].create({
            'name': self.image_name,
            'type': 'binary',
            'datas': self.image,
            'datas_fname': self.image_name,
            'res_model': 'hr.employee',
            'mimetype': self.mimetype
        })

        self.env.cr.execute(
            "INSERT INTO face_recognition_hr_employee_ir_attachments_rel (employee_id, attachment_id) VALUES (%d, %d)" %
            (self.employee_id.id, attachment.id))

    @api.one
    @api.depends("percentage", "name")
    def _get_message(self):
        self.message = "This person is %s by %d percent probability" % (self.name, self.percentage)
