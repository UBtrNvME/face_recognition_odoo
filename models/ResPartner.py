# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    attachment_ids = fields.Many2many('ir.attachment', 'face_recognition_res_partner_ir_attachments_rel', 'partner_id',
                                      'attachment_id', string='Photos')



