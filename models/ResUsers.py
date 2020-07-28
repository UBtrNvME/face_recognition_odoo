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