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




class CadAutomation(http.Controller):

    @http.route('/cad_automation/', auth='public')
    def cad_automation(self):
        return request.render('cad_automation.cad_automation')

    @http.route('/cad_automation/process_image', auth='public')
    def cad_automation_process_image(self):
        params = request.params
        return params
