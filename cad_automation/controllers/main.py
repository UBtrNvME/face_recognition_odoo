# -*- coding: utf-8 -*-
# Copyright 2014 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
CAD AUTOMATION CONTROLLERS
==========================

Developed by QZHUB
"""

from odoo import http
from odoo.http import request
import json
from extra.qzhub_deep_learning.cad_automation.services.img_manipulation import (
    binary_to_base64
)


class CadObjectTemplate(http.Controller):

    @http.route('/cad_object_template', auth='public')
    def cad_object_template(self):
        return request.render('cad_automation.cad_automation')

    @http.route('/cad_object_template/create', auth='public')
    def create(self):
        params = request.params
        template = request.env["cad.object.template"].create(
            {
                "image_representation": params["file_content"][
                                        params['file_content'].find(",") + 1:],
                "name": "Random_name"})
        return template.mask

    @http.route('/cad_object_template/get_list', auth='public')
    def get_list(self):
        templates = request.env["cad.object.template"].search([])
        data = []
        for template in templates:
            data.append({
                "id": template.id,
                "name": template.name,
                "mask": binary_to_base64(template.mask)
            })
        return json.dumps(data)
