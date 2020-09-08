from odoo import fields, models, api


class ResUsers(models.Model):
    _inherit = "res.users"

    has_password = fields.Boolean(string="Has/Hasn't Password", default=False, compute="_compute_has_password", store=True)

    @api.depends("password")
    def _compute_has_password(self):
        for user in self:
            self.env.cr.execute(
                "SELECT COALESCE(password, '') FROM res_users WHERE id=%s",
                [user.id]
            )
            [hashed] = self.env.cr.fetchone()
            user.has_password = True if hashed != '' else False

    @api.depends('log_ids')
    def on_login_make_attendance(self):
        for user in self:
            print("On login")
            groups_id = user.env['res.users'].search_read([
                ['id', '=', user.id],
            ], ['groups_id'])[0]['groups_id']
            employee = user.employee_id
            is_internal_user = 1 in groups_id
            is_checked_out = self.env['hr.attendance'].search([['employee_id', '=', employee.id]],
                                                                            limit=1).check_out
            if user and is_internal_user and employee and is_checked_out:
                employee.attendance_manual('hr_attendance.hr_attendance_action_my_attendances')['action']

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    attendance_state = fields.Selection(store=True)