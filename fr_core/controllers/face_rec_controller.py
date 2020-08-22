import json

from PIL import Image
import base64
from io import BytesIO
import pytesseract
from odoo.addons.web.controllers.main import Home

from odoo import http
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import logging
from odoo.tools.translate import _

_loger = logging.getLogger(__name__)


class FaceRecognitionController(http.Controller):

    @http.route(['/api/v1/employee/<int:user_id>/processImage'], type="json", auth="public",
                methods=['GET', 'POST'], website=False,
                csrf=False)
    def process_image(self, user_id):
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
    def make_attachment(self, face_model_id):
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
    def process_image_unknown_user(self):
        image_datas = request.params.get('unknown_user_image')
        if not image_datas:
            return http.Response('No Terms Found', status=412)
        unknown_user_image = self.process_image_datas_to_base64(image_datas)
        face_locations = request.env['face.recognition'].sudo(True).get_face_locations_within_ellipse(unknown_user_image)
        print(f"{face_locations=}")
        if 0 < len(face_locations) <= 1:
            user, model = request.env['face.recognition'].sudo(True).find_id_of_the_user_on_the_image(unknown_user_image, face_locations)

            if not user or user in [-i for i in range(1, 4)]:
                if user == 0:
                    return ['NoUser']
                elif user == -1:
                    return ['TooManyFaces']
                elif user == -3:
                    return [model.id]
                else:
                    return ['NoFace']
            return [user.login, user.has_password, user.name]
        return False


    @http.route(['/api/v1/processUinImage'], type="json", auth="public", methods=['GET', 'POST'], website=False,
                csrf=False)
    def process_image_uin_v1(self):
        image_data = request.params.get('unknown_uin')
        face_model_id = request.params.get('face_model_id')
        if not image_data:
            return http.Response('No Terms Found', status=412)
        image_data = self.process_image_datas_to_base64(image_data)
        img = Image.open(BytesIO(base64.b64decode(image_data)))
        text = pytesseract.image_to_string(img)
        uin = [int(s) for s in text.split() if s.isdigit() and len(s) == 12]

        if len(uin):
            partner = request.env['res.partner'].sudo(True).search([['face_model_id', '=', int(face_model_id)]])
            uin_id = request.env['uin.recognition'].sudo(True).create({
                'name': str(uin[0]),
                'image': image_data
            })

            partner.uin_recognition_id = uin_id.id
        return uin

    @http.route(['/api/processFrontUinImage'], type="json", auth="public", methods=['GET', 'POST'], website=False,
                csrf=False)
    def process_image_uin_front(self):
        image_data = self.process_image_datas_to_base64(request.params.get('unknown_uin_image'))
        img = Image.open(BytesIO(base64.b64decode(image_data)))
        text = pytesseract.image_to_string(img)
        uin = [int(s) for s in text.split() if s.isdigit() and len(s) == 12]

        return uin[0] if len(uin) else -1

    @http.route(['/api/processBackUinImage'], type="json", auth="public", methods=['GET', 'POST'], website=False,
                csrf=False)
    def process_image_uin_back(self):
        image_data = self.process_image_datas_to_base64(request.params.get('unknown_uin_image'))
        img = Image.open(BytesIO(base64.b64decode(image_data)))
        text = pytesseract.image_to_string(img)
        uin = [int(s) for s in text.split() if s.isdigit() and len(s) == 12]

        return uin[0] if len(uin) else -1

    @staticmethod
    def process_image_datas_to_base64(image_datas):
        index_to_strip_from = image_datas.find('base64,') + len('base64,')
        return image_datas[index_to_strip_from:]

    @http.route('/test1', type='http', auth="public", methods=['GET', 'POST'])
    def test1(self):
        print("hello bitch")
        return http.Response('OK', status=200)

    @http.route('/web/signup/<int:model_id>', type='http', auth='public', website=True)
    def web_auth_signup(self, model_id, *args, **kw):
        if request.httprequest.method == 'GET':
            return request.render('fr_core.signup')
        else:
            data = request.params

            res = request.env['res.users'].sudo(True).search([['login', '=', data['login']]])
            if len(res):
                raise UserError(_('User with given email already registered'))
            elif data['password'] != data['confirm_password']:
                raise UserError(_('Passwords do not match'))
            else:
                user = request.env['res.users'].sudo(True).create({
                    'login': data['login'],
                    'groups_id': [(6, 0, [8])],
                    'partner_id': request.env['res.partner'].sudo(True).create({
                        'name': data['name'],
                        'face_model_id': model_id
                    }).id
                })
                user.password = data['password']

                if data['uin']:
                    if kw.get('uin_attachment_front', False):
                        b64_image = base64.b64encode(kw.get('uin_attachment_front').read()).decode('utf-8')
                        uin_id = request.env['uin.recognition'].sudo(True).create({
                            'name': str(data['uin']),
                            'image': b64_image
                        })
                    else:
                        uin_id = request.env['uin.recognition'].sudo(True).create({
                            'name': str(data['uin'])
                        })
                    user.uin_recognition_id = uin_id.id

                    return http.redirect_with_hash('/web/login/face_recognition')

            return request.render('fr_core.face_recognition_page')


class HomeInheritedController(Home):
    @http.route()
    def web_login(self, redirect=None, **kw):

        if request.httprequest.method == 'POST':
            return super(HomeInheritedController, self).web_login(redirect=redirect, **kw)

        if 'login' in request.params or 'isRecognised' in request.params:
            return super(HomeInheritedController, self).web_login(redirect=redirect, **kw)

        return http.redirect_with_hash('/web/login/face_recognition')

    @http.route("/web/login/<string:login>", type="http", auth="none")
    def web_login_user(self, login, redirect=None, **kw):
        if login == 'unrecognized_user':
            s = f'?login=false&hasPassword=true&isRecognised=true'
            return http.redirect_with_hash('/web/login%s' % s)
        user = request.env['res.users'].sudo(True).search([['login', '=', login]])
        if user and user.has_password:
            s = f'?login={login}&hasPassword=true&name={user.partner_id.name}&isRecognised=true'
            return http.redirect_with_hash('/web/login%s' % s)
        return http.redirect_with_hash('/web/login/face_recognition')
