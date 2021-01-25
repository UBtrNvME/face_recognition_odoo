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
"""
Multiplayer Services
====================

Set of controllers required to work with access token to the multiplayer services.

Attributes:
-----------

multiplayer_get_token
multiplayer_delete_token
multiplayer_check_token


Notes:
======

All of the endpoints are auth=user, those require user to have active session in odoo,
therefore it is important to authenticate before using above methods.

Bellow are procedures to be taken in order to get cookies for auth=user:
>>> import requests
>>> import json
>>>
>>> odoo_url = "http://localhost:8060"
>>>
>>> data = {'params': {'db': 'db_name', 'login': 'login', 'password': 'pass'}}
>>> headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
>>> session_details = requests.get(
>>>    url=odoo_url + '/web/session/authenticate',
>>>    data=json.dumps(data),
>>>    headers=headers
>>> )
>>> session_id = str(session_details.cookies.get('session_id'))
>>> cookies = {
>>>     'username': "mooiron.k@gmail.com",
>>>     'password': "123",
>>>     'session_id': session_id
>>> }
>>> response = requests.get("/your/desired/endpoint", data=json.dumps(your_json_data), headers=headers, cookies=cookies)
"""


import logging

from odoo import _, http
from odoo.http import request

_logger = logging.getLogger(__name__)
TOKEN_MODEL = "multiplayer.token"


class MultiplayerService(http.Controller):
    @http.route(
        ["/multiplayer/token", "/multiplayer/<int:room>/token"],
        auth="user",
        type="json",
        methods=["GET"],
    )
    def multiplayer_get_token(self, room=None):
        uid = request.session.uid
        token = request.env[TOKEN_MODEL].get_token(uid)
        response = {"success": True}
        if token:
            result = {"token_data": token.token_data, "token_id": token.id}
            response.update(result)
        return response

    @http.route(["/multiplayer/token"], methods=["DELETE"], auth="user", type="json")
    def multiplayer_delete_tokens(self, token_ids=None, token_id=None):
        """ Delete token endpoint

        data = {
            "params": {
                "token_id": id_of_the_token_tobe_deleted,
                    or
                "token_ids": [ids_of_the_toke_to_be_deleted, ...],
            }
        }

        Returns
        -------
        Response {
            "success": bool,
            "result": Unknown
        }

        """
        response = {"success": True, "deleted": False}
        result = request.env["multiplayer.token"].delete_token(token_id or token_ids)
        if result:
            response["deleted"] = result
        else:
            response["success"] = False
        return response

    @http.route(
        ["/multiplayer/token/check", "/multiplayer/<int:room>/token/check"],
        methods=["GET"],
        auth="user",
        type="json",
    )
    def multiplayer_check_token(self, token_data):
        result = request.env[TOKEN_MODEL].check_token(token_data)
        response = {"success": True, "is_valid": result}
        return response

    @http.route(
        "/mp/test", methods=["GET"], auth="none", type="http",
    )
    def test(self):
        model = request.env[TOKEN_MODEL].sudo(True)
        record = model.create_token_if_not_exist(1)
        return "Success"
