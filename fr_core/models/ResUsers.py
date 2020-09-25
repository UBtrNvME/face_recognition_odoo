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

    @classmethod
    def authenticate(cls, db, login, password, user_agent_env):
        user_id = super().authenticate(db, login, password, user_agent_env)
        with cls.pool.cursor() as cr:
            env = api.Environment(cr, user_id, {})

            employee = env.user['employee_id']
            groups_id = [group.id for group in env.user.groups_id]
            is_internal_user = 1 in groups_id

            is_checked_out = env['hr.attendance'].search([['employee_id', '=', employee.id]],
                                                                            limit=1)
            is_checked_out = is_checked_out.check_out if is_checked_out else True
            if user_id and is_internal_user and employee and is_checked_out:
                employee.attendance_manual('hr_attendance.hr_attendance_action_my_attendances')
        return user_id