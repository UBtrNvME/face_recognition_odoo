# -*- coding: utf-8 -*-
from odoo import api, models, fields


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.model
    def _cron_check_out_all_attendances(self):
        for attendance in self.search([['check_out', '=', False]]):
            attendance.check_out = fields.Datetime.now()
