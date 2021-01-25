#  Copyright (c)  2021, QZHub LLP
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

import logging
import secrets

from odoo import api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class MultiplayerAccessToken(models.Model):
    _name = "multiplayer.token"
    _sql_constraints = [
        (
            "user_id_unique",
            "UNIQUE(user_id)",
            "User already has multiplayer access token",
        )
    ]
    NUMBER_OF_BYTES = 50

    def _generate_token_data(self):
        token = secrets.token_hex(nbytes=self.NUMBER_OF_BYTES)
        return token

    user_id = fields.Many2one(comodel_name="res.users", string="User ID", required=True)
    token_data = fields.Text(
        string="Token data", readonly=True, default=_generate_token_data
    )
    room_id = fields.Integer(string="Multiplayer Room")

    @api.model
    def check_token(self, candidate):
        for token in self.search(
            [("token_data", "like", f"{candidate[:self.NUMBER_OF_BYTES//8]}%")]
        ):
            if token._compare_with_candidate_token(candidate):
                return True
        return False

    @api.model
    def get_token(self, uid):
        token = self.search([("user_id", "=", uid)])
        if not token:
            token = self.create({"user_id": uid})
        return token

    @api.model
    def delete_token(self, ids):
        if isinstance(ids, int):
            ids = [ids]
        tokens = self.search([("id", "in", ids)])
        if tokens:
            return tokens.unlink()
        return False

    def _compare_with_candidate_token(self, candidate):
        return secrets.compare_digest(self.token_data, candidate)
