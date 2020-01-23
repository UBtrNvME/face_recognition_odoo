# -*- coding: utf-8 -*-

from odoo import models, fields, api


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.multi
    def set_avatar(self):
        self.env["hr.employee"].browse(self.res_id).image = self.datas
