import json
import odoo
from odoo import http
from odoo.http import request
from odoo.tools import logging
from odoo.tools.translate import _
from odoo.exceptions import AccessError, UserError, AccessDenied
from odoo.addons.web.controllers.main import Home


_loger = logging.getLogger(__name__)


class FaceRecognitionController(http.Controller):

    @http.route(['/api/v1/employee/<int:user_id>/processImage'], type="json", auth="public",
                methods=['GET', 'POST'], website=False,
                csrf=False)
    def processImage(self, user_id):
        jsondata = json.loads(request.httprequest.data)
        user = request.env["res.users"].search([["id", "=", user_id]])
        res = -1000
        headers = {'Content-Type': 'application/json'}
        body = {'results': {'code': 200, 'message': 'OK'}, 'face_rec_result': 0}
        if user:
            partner = user.partner_id
            # unknown_attachment = partner_id.add_new_face_image_attachment(jsondata["image_in_64encodeDataURL"])
            image_datas = jsondata["image_in_64encodeDataURL"]
            index_to_strip_from = image_datas.find("base64,") + len("base64,")
            striped_image_datas = image_datas[index_to_strip_from:]
            res = request.env["face.recognition"].compare(striped_image_datas, partner.id)

        if res >= 90.0:
            body['face_rec_result'] = 200
        elif res == -1:
            body['face_rec_result'] = 201
        elif res == -2:
            body['face_rec_result'] = 202
        elif res == -3:
            body['face_rec_result'] = 203
        elif res < 90:
            body['face_rec_result'] = 204
        else:
            body['face_rec_result'] = 412
            body['results'] = {'code': 412, 'message': 'Fail'}
        return body

    @http.route(['/api/v1/faceModel/<int:face_model_id>/makeAttachment'], type="json", auth="public",
                methods=['GET', 'POST'], website=False,
                csrf=False)
    def makeAttachment(self, face_model_id):
        jsondata = json.loads(request.httprequest.data)
        face_model = request.env["res.partner.face.model"].search([["id", "=", face_model_id]])
        if face_model:
            # unknown_attachment = partner_id.add_new_face_image_attachment(jsondata["image_in_64encodeDataURL"])
            image_datas = jsondata["image_in_64encodeDataURL"]
            index_to_strip_from = image_datas.find("base64,") + len("base64,")
            striped_image_datas = image_datas[index_to_strip_from:]
            try:
                attachment, response = face_model.add_new_face_image_attachment(striped_image_datas, "face", True)
                return http.Response("Ok", status=200)
            except:
                return http.Response("No Terms Found", status=412)

    @http.route('/web/login/face_recognition', type='http', auth="public", website=True)
    def login_face_recognition(self, **kw):
        # from here you can call
        return request.render('fr_core.face_recognition_page')

    @http.route(['/api/v1/processImage'], type="json", auth="public", methods=['GET', 'POST'], website=False,
                csrf=False)
    def processImageOfUnknownUser(self):
        image_datas = request.params.get('unknown_user_image')
        if not image_datas:
            return http.Response("No Terms Found", status=412)
        unknown_user_image = self.process_image_datas_to_base64(image_datas)
        user = request.env['face.recognition'].find_id_of_the_user_on_the_image(unknown_user_image)
        if not user or user == -1 or user == -2:
            if user == 0:
                return ["NoUser"]
            elif user == -1:
                return ["TooManyFaces"]
            else:
                return ["NoFace"]
        return [user.login, user.has_password, user.name]

    def process_image_datas_to_base64(self, image_datas):
        index_to_strip_from = image_datas.find("base64,") + len("base64,")
        return image_datas[index_to_strip_from:]

    @http.route('/test1', type='http', auth="public", methods=['GET', 'POST'])
    def test1(self):
        print("hello bitch")
        return http.Response('OK', status=200)

    # def _login_redirect(self, uid, redirect=None):
    #     return redirect if redirect else '/web'


class HomeInheritedController(Home):
    @http.route()
    def web_login(self, redirect=None, **kw):
        if request.httprequest.method == 'POST':
            return super(HomeInheritedController, self).web_login(redirect=redirect, **kw)

        if 'login' in request.params:
            return super(HomeInheritedController, self).web_login(redirect=redirect, **kw)

        if 'isRecognised' in request.params:
            return super(HomeInheritedController, self).web_login(redirect=redirect, **kw)
        else:
            return http.redirect_with_hash('/web/login/face_recognition')
    #TODO make more galant  solution
    @http.route("/web/login/admin", type="http", auth="none")
    def web_login_admin(self, redirect=None, **kw):
        qcontext = "?login=admin&hasPassword=true&name=Administrator&isRecognised=true"
        return http.redirect_with_hash('/web/login%s' % qcontext)