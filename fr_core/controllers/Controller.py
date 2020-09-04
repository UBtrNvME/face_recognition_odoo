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


_logger = logging.getLogger(__name__)


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
    def web_login_face_recognition(self, **kw):
        # from here you can call
        return request.render('fr_core.face_recognition_page')

    @http.route(['/api/v1/processImage'], type="json", auth="public", methods=['GET', 'POST'], website=False,
                csrf=False)
    def process_image_of_unknown_user(self):
        image_datas = request.params.get('unknown_user_image')
        response = {}
        if not image_datas:
            response['status'] = {
                'success': True,
                'code'   : 400,
                'message': "Bad Request"
            }
            return response
        unknown_user_image = self.process_image_datas_to_base64(image_datas)
        face_locations = request.env['face.recognition'].sudo(True).get_face_locations_within_ellipse(
            unknown_user_image)
        print(face_locations)
        if len(face_locations) and len(face_locations) <= 1:
            try:
                user, model = request.env['face.recognition'].sudo(True).find_id_of_the_user_on_the_image(
                    unknown_user_image, face_locations)
            except TimeoutError:
                return {
                    'status': {
                        'success': False,
                        'code'   : 408,
                        'message': "Request Timeout"
                    }
                }

            if not user or user in [-i for i in range(1, 4)]:
                if user == -3:
                    response['status'] = {
                        'success': True,
                        'code'   : 301,
                        'message': "No User With Such Encoding In Database"
                    }
                    response['route'] = "/web/login"
                    response['payload'] = {
                        'isRecognised': False,
                        'model'       : model.id,
                    }
                else:
                    response['status'] = {
                        'success': False,
                        'code'   : 402,
                        'message': "No Face On The Image"
                    }
            else:
                response['status'] = {
                    'success': True,
                    'code'   : 300,
                    'message': "Successfully Recognised User"
                }
                response['payload'] = {
                    'isRecognised': True,
                    'login'       : user.login,
                    'name'        : user.name,
                    'hasPassword' : user.has_password,
                    'id': user.id
                }
                response['route'] = "/web/login"
        else:
            response['status'] = {
                'success': False,
                'code'   : 401,
                'message': "Too Many Faces On The Image"
            }
        return response

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
                'name' : str(uin[0]),
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
                    'login'     : data['login'],
                    'groups_id' : [(6, 0, [8])],
                    'partner_id': request.env['res.partner'].sudo(True).create({
                        'name'         : data['name'],
                        'face_model_id': model_id
                    }).id
                })
                user.password = data['password']

                if data['uin']:
                    if kw.get('uin_attachment_front', False):
                        b64_image = base64.b64encode(kw.get('uin_attachment_front').read()).decode('utf-8')
                        uin_id = request.env['uin.recognition'].sudo(True).create({
                            'name' : str(data['uin']),
                            'image': b64_image
                        })
                    else:
                        uin_id = request.env['uin.recognition'].sudo(True).create({
                            'name': str(data['uin'])
                        })
                    user.uin_recognition_id = uin_id.id

                    return http.redirect_with_hash('/api/v1/face_model/%d/fill' % (model_id))

            return request.render('fr_core.face_recognition_page')

    @http.route(['/api/v1/face_model/checkImageType'], type='json', auth='public', website=True)
    def face_model_check_image_type(self):
        data = request.params
        image_type = data['image_type']
        image_data = self.process_image_datas_to_base64(data['image_data'])
        face_location = request.env['face.recognition'].get_face_locations_within_ellipse(image_data)
        if len(face_location) >= 1 and len(face_location):
            if image_type == 'face_with_smile':
                is_face_smiling = request.env['face.recognition'].is_face_smiling(image_data, face_location)
                if is_face_smiling and len(is_face_smiling) and len(is_face_smiling) <= 1:
                    for value in is_face_smiling.values():
                        return {
                            'status' : {
                                'success': True,
                                'code'   : 200,
                                'message': "Successful request",
                            },
                            'payload': {
                                'requested_image_type': image_type,
                                'is_correct_type'     : value,
                                'actual_image_type'   : 'face_with_smile' if value else 'other',
                            }
                        }
                else:
                    return {
                        'status': {
                            'success': False,
                            'code'   : 400,
                            'message': "Bad request",
                        },
                    }
            else:
                image_raccourcir = request.env['face.recognition'].determine_face_raccourcir(
                    request.env['face.recognition'].get_face_landmarks(image_data))
                print(image_raccourcir)
                if not image_raccourcir:
                    return {
                        'status': {
                            'success': False,
                            'code'   : 400,
                            'message': "Bad request",
                        },
                    }
                is_correct_raccoursir = image_raccourcir == image_type
                return {
                    'status' : {
                        'success': True,
                        'code'   : 200,
                        'message': "Successful request",
                    },
                    'payload': {
                        'requested_image_type': image_type,
                        'is_correct_type'     : is_correct_raccoursir,
                        'actual_image_type'   : image_raccourcir,
                    }
                }
        else:
            return {
                'status': {
                    'success': False,
                    'code'   : 400,
                    'message': "Bad request",
                },
            }

    @http.route(['/api/v1/face_model/<int:model_id>/fill'], type='http', auth='public', website=True)
    def face_model_fill(self, model_id):
        if request.httprequest.method == 'POST':
            data = json.loads(request.httprequest.data)
            images_to_attach = data['images_to_attach']
            face_model = request.env['res.partner.face.model'].search(
                [['id', '=', model_id]])
            try:
                for key in images_to_attach:
                    face_model.add_new_face_image_attachment(
                        image_datas=self.process_image_datas_to_base64(images_to_attach[key]),
                        image_name='new',
                        with_encoding=True)
                return http.Response("Success", status=200)
            except:
                return http.Response("Bad request", status=400)
        else:
            return request.render('fr_core.face_model_fill')


class HomeInheritedController(Home):
    @http.route()
    def web_login(self, redirect=None, **kw):
        if request.httprequest.method == 'POST':
            request.env['face.recognition'].sudo(True).make_attendance(request.params['id'])
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
