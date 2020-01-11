# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HR(models.Model):
    _inherit = 'hr.employee'

    attachment_ids = fields.Many2many('ir.attachment', 'face_recognition_hr_employee_ir_attachments_rel', 'employee_id',
                                      'attachment_id', string='Photos')

    def compare_with_image(self):
        return {
            'res_model': 'face.recognition',
            'type': 'ir.actions.act_window',
            'context': {
                "default_employee_id": self.id
            },
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref("face_recognition.face_recognition_compare_form").id,
            'target': 'new'
        }