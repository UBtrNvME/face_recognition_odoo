import base64
import json
from io import BytesIO

from odoo import _, http
from odoo.http import request
from odoo.tools import logging

import numpy as np
import pytesseract
from PIL import Image

from ..scripts import auto_crop_uid as uid_rec
from ..scripts.CustomErrors import UnrecognizableDocument

# import werkzeug
# from odoo.exceptions import UserError
# from odoo.addons.auth_signup.controllers.main import AuthSignupHome
# from odoo.addons.auth_signup.models.res_users import SignupError
# from odoo.addons.web.controllers.main import Home


_logger = logging.getLogger(__name__)


class FaceRecognitionController(http.Controller):
    @http.route(
        ["/api/v1/employee/<int:user_id>/processImage"],
        type="json",
        auth="public",
        methods=["GET", "POST"],
        website=False,
        csrf=False,
    )
    def process_image(self, user_id):
        jsondata = json.loads(request.httprequest.data)
        user = request.env["res.users"].search([["id", "=", user_id]])
        res = -1000
        headers = {"Content-Type": "application/json"}
        body = {"results": {"code": 200, "message": "OK"}, "face_rec_result": 0}
        if user:
            partner = user.partner_id
            # unknown_attachment = partner_id.add_new_face_image_attachment(jsondata["image_in_64encodeDataURL"])
            image_datas = jsondata["image_in_64encodeDataURL"]
            index_to_strip_from = image_datas.find("base64,") + len("base64,")
            striped_image_datas = image_datas[index_to_strip_from:]
            res = request.env["face.recognition"].compare(
                striped_image_datas, partner.id
            )

        if res >= 90.0:
            body["face_rec_result"] = 200
        elif res == -1:
            body["face_rec_result"] = 201
        elif res == -2:
            body["face_rec_result"] = 202
        elif res == -3:
            body["face_rec_result"] = 203
        elif res < 90:
            body["face_rec_result"] = 204
        else:
            body["face_rec_result"] = 412
            body["results"] = {"code": 412, "message": "Fail"}
        return body

    @http.route(
        ["/api/v1/faceModel/<int:face_model_id>/makeAttachment"],
        type="json",
        auth="public",
        methods=["GET", "POST"],
        website=False,
        csrf=False,
    )
    def make_attachment(self, face_model_id):
        jsondata = json.loads(request.httprequest.data)
        face_model = (
            request.env["res.partner.face.model"]
            .sudo(True)
            .search([["id", "=", face_model_id]])
        )
        if face_model:
            # unknown_attachment = partner_id.add_new_face_image_attachment(jsondata["image_in_64encodeDataURL"])
            image_datas = jsondata["image_in_64encodeDataURL"]
            index_to_strip_from = image_datas.find("base64,") + len("base64,")
            striped_image_datas = image_datas[index_to_strip_from:]
            try:
                attachment, response = face_model.add_new_face_image_attachment(
                    striped_image_datas, "face", True
                )
                return http.Response("Ok", status=200)
            except:
                return http.Response("No Terms Found", status=412)

    @http.route(
        ["/api/v1/processImage"],
        type="json",
        auth="public",
        methods=["GET", "POST"],
        website=False,
        csrf=False,
    )
    def process_image_of_unknown_user(self):
        image_datas = json.loads(request.httprequest.data)["unknown_user_image"]
        image_dimensions = json.loads(request.httprequest.data)["image_dimensions"]
        response = {}
        if not image_datas:
            response["status"] = {
                "success": True,
                "code": 400,
                "message": "Bad Request",
                "message_ru": "",
            }
            return response
        unknown_user_image = self.process_image_datas_to_base64(image_datas)
        face_locations = (
            request.env["face.recognition"]
            .sudo(True)
            .get_face_locations_within_ellipse(unknown_user_image, image_dimensions)
        )
        if len(face_locations) and len(face_locations) <= 1:
            try:
                user, model = (
                    request.env["face.recognition"]
                    .sudo(True)
                    .find_id_of_the_user_on_the_image(
                        unknown_user_image, face_locations
                    )
                )
            except TimeoutError:
                return {
                    "status": {
                        "success": False,
                        "code": 408,
                        "message": "Request Timeout",
                        "message_ru": "",
                    }
                }

            if not user or user in [-i for i in range(1, 4)]:
                if user == -3:
                    response["status"] = {
                        "success": True,
                        "code": 301,
                        "message": "No User With Such Encoding In Database",
                        "message_ru": "Пользователь с данной кодировкой, не найден!",
                    }
                    response["route"] = "/web/login"
                    response["payload"] = {
                        "isRecognised": False,
                        "model": model.id,
                    }
                else:
                    response["status"] = {
                        "success": False,
                        "code": 402,
                        "message": "No Face On The Image",
                        "message_ru": "",
                    }
            else:
                response["status"] = {
                    "success": True,
                    "code": 300,
                    "message": "Successfully Recognised User",
                    "message_ru": "Пользователь успешно распознан!",
                }
                response["payload"] = {
                    "isRecognised": True,
                    "login": user.login,
                    "name": user.name,
                    "hasPassword": user.has_password,
                    "id": user.id,
                }
                response["route"] = "/web/login"
        else:
            if len(face_locations):
                response["status"] = {
                    "success": False,
                    "code": 401,
                    "message": "Too Many Faces On The Image",
                    "message_ru": "",
                }
            else:
                response["status"] = {
                    "success": False,
                    "code": 405,
                    "message": "Face not within the ellipse",
                    "message_ru": "Ошибка, Поместите лицо в выделенную область!",
                }
        return response

    @http.route(
        ["/api/v1/processIinImage"],
        type="json",
        auth="public",
        methods=["GET", "POST"],
        website=False,
        csrf=False,
    )
    def process_image_iin_v1(self):
        image_data = request.params.get("unknown_iin")
        face_model_id = request.params.get("face_model_id")
        if not image_data:
            return http.Response("No Terms Found", status=412)
        image_data = self.process_image_datas_to_base64(image_data)
        img = Image.open(BytesIO(base64.b64decode(image_data)))
        text = pytesseract.image_to_string(img)
        iin = [int(s) for s in text.split() if s.isdigit() and len(s) == 12]

        if len(iin):
            partner = (
                request.env["res.partner"]
                .sudo(True)
                .search([["face_model_id", "=", int(face_model_id)]])
            )
            iin_id = (
                request.env["iin.recognition"]
                .sudo(True)
                .create({"name": str(iin[0]), "image": image_data})
            )

            partner.iin_recognition_id = iin_id.id
        return iin

    @http.route(
        ["/api/processFrontIinImage"],
        type="json",
        auth="public",
        methods=["GET", "POST"],
        website=False,
        csrf=False,
    )
    def process_image_iin_front(self):
        image_data = self.process_image_datas_to_base64(
            request.params.get("unknown_iin_image")
        )
        img = Image.open(BytesIO(base64.b64decode(image_data)))
        response = dict(error=False, results=None)
        try:
            data = uid_rec.prepare_uid("front", np.array(img))
            data["iin"] = data.pop("individual_identification_number")
            data["name"] = (
                f"{data.pop('last_name_kaz')} {data.pop('first_name_kaz')} "
                f"{data.pop('father_name_kaz')}".title()
            )
            data["dob"] = "-".join(
                list(map(lambda x: x.strip(), data.pop("date_of_birth").split(".")))[
                    ::-1
                ]
            )
            response["results"] = data
        except UnrecognizableDocument:
            response["error"] = True
        finally:
            return response

    @http.route(
        ["/api/processBackIinImage"],
        type="json",
        auth="public",
        methods=["GET", "POST"],
        website=False,
        csrf=False,
    )
    def process_image_iin_back(self):
        genders = {"F": "female", "M": "male"}
        image_data = self.process_image_datas_to_base64(
            request.params.get("unknown_iin_image")
        )
        img = Image.open(BytesIO(base64.b64decode(image_data)))
        response = dict(error=False, results=None)
        try:
            data = uid_rec.prepare_uid("back", np.array(img))
            data.pop("place_of_birth")
            data[
                "login"
            ] = f"{data.pop('first_name')}.{data.pop('last_name')}@gmail.com".lower()
            data["gender"] = genders[data.pop("gender")]
            for key in [
                "issuing_authority",
                "date_of_expiring",
                "document_number",
                "date_of_issuing",
            ]:
                data.pop(key)
            response["results"] = data
        except UnrecognizableDocument:
            response["error"] = True
        finally:
            return response

    @staticmethod
    def process_image_datas_to_base64(image_datas):
        index_to_strip_from = image_datas.find("base64,") + len("base64,")
        return image_datas[index_to_strip_from:]

    @http.route("/test1", type="http", auth="public", methods=["GET", "POST"])
    def test1(self):
        return http.Response("OK", status=200)

    @http.route("/web/signup/<int:model_id>", type="http", auth="public", website=True)
    def web_auth_signup(self, model_id, *args, **kw):
        qcontext = request.params.copy()
        is_error = False
        if request.httprequest.method == "GET":
            return request.render("fr_core.signup")
        else:
            data = request.params
            res = (
                request.env["res.users"]
                .sudo(True)
                .search([["login", "=", data["login"]]])
            )
            if len(res):
                is_error = True
                qcontext["error_email"] = _(
                    "Another user is already registered using this email address."
                )
            if data["password"] != data["confirm_password"]:
                is_error = True
                qcontext["error_password"] = _("Passwords do not match.")
            if len(data["iin"]) != 12:
                qcontext["error_iin"] = _("Please enter correct IIN")
                is_error = True
            if not is_error:
                partner = (
                    request.env["res.partner"]
                    .sudo(True)
                    .create({"name": data["name"], "face_model_id": model_id})
                )
                user = (
                    request.env["res.users"]
                    .sudo(True)
                    .create(
                        {
                            "login": data["login"],
                            "groups_id": [(6, 0, [8])],
                            "partner_id": partner.id,
                        }
                    )
                )
                user.password = data["password"]
                partner.iin = data["iin"]
            return (
                http.redirect_with_hash("/api/v1/face_model/%d/fill" % (model_id))
                if not is_error
                else request.render("fr_core.signup", qcontext)
            )

    @http.route(
        ["/api/v1/face_model/checkImageType"], type="json", auth="public", website=True
    )
    def face_model_check_image_type(self):
        data = request.params
        image_type = data["image_type"]
        image_data = self.process_image_datas_to_base64(data["image_data"])
        face_location = request.env[
            "face.recognition"
        ].get_face_locations_within_ellipse(image_data)
        if len(face_location) >= 1 and len(face_location):
            if image_type == "face_with_smile":
                is_face_smiling = request.env["face.recognition"].is_face_smiling(
                    image_data, face_location
                )
                if (
                    is_face_smiling
                    and len(is_face_smiling)
                    and len(is_face_smiling) <= 1
                ):
                    for value in is_face_smiling.values():
                        return {
                            "status": {
                                "success": True,
                                "code": 200,
                                "message": "Successful request",
                            },
                            "payload": {
                                "requested_image_type": image_type,
                                "is_correct_type": value,
                                "actual_image_type": "face_with_smile"
                                if value
                                else "other",
                            },
                        }
                else:
                    return {
                        "status": {
                            "success": False,
                            "code": 400,
                            "message": "Bad request",
                        },
                    }
            else:
                image_raccourcir = request.env[
                    "face.recognition"
                ].determine_face_raccourcir(
                    request.env["face.recognition"].get_face_landmarks(image_data)
                )
                if not image_raccourcir:
                    return {
                        "status": {
                            "success": False,
                            "code": 400,
                            "message": "Bad request",
                        },
                    }
                is_correct_raccoursir = image_raccourcir == image_type
                return {
                    "status": {
                        "success": True,
                        "code": 200,
                        "message": "Successful request",
                    },
                    "payload": {
                        "requested_image_type": image_type,
                        "is_correct_type": is_correct_raccoursir,
                        "actual_image_type": image_raccourcir,
                    },
                }
        else:
            return {
                "status": {"success": False, "code": 400, "message": "Bad request",},
            }

    @http.route(
        ["/api/v1/face_model/<int:model_id>/fill"],
        type="http",
        auth="public",
        website=True,
    )
    def face_model_fill(self, model_id):
        if request.httprequest.method == "POST":
            data = json.loads(request.httprequest.data)
            images_to_attach = data["images_to_attach"]
            face_model = (
                request.env["res.partner.face.model"]
                .sudo(True)
                .search([["id", "=", model_id]])
            )
            try:
                for key in images_to_attach:
                    face_model.sudo(True).add_new_face_image_attachment(
                        image_datas=self.process_image_datas_to_base64(
                            images_to_attach[key]
                        ),
                        image_name="new",
                        with_encoding=True,
                    )
                return http.Response("Success", status=200)
            except:
                return http.Response("Bad request", status=400)
        else:
            return request.render("fr_core.face_model_fill")


# class AuthSignupHome(Home):
#     def do_signup(self, qcontext):
#         """ Shared helper that creates a res.partner out of a token """
#         values = {key: qcontext.get(key) for key in
#                   ('login', 'name', 'password', 'iin', 'face_model_id', 'city', 'dob')}
#         # values.update({'country_id': int(qcontext.get('country_id'))})
#         for key in values:
#             if values[key] == '':
#                 values.pop(key)
#             elif '_id' in key:
#                 values[key] = int(values[key])
#         if not values:
#             raise UserError(_("The form was not properly filled in."))
#         if values.get('password') != qcontext.get('confirm_password'):
#             raise UserError(_("Passwords do not match; please retype them."))
#         supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
#         lang = request.context.get('lang', '').split('_')[0]
#         if lang in supported_lang_codes:
#             values['lang'] = lang
#         self._signup_with_values(qcontext.get('token'), values)
#         request.env.cr.commit()
#
#     @http.route()
#     def web_login(self, redirect=None, **kw):
#         if request.httprequest.method == 'POST':
#             return super(AuthSignupHome, self).web_login(redirect=redirect, **kw)
#
#         if 'login' in request.params or 'isRecognised' in request.params:
#             return super(AuthSignupHome, self).web_login(redirect=redirect, **kw)
#         return http.redirect_with_hash("/web/login/face_recognition")
#
#     @http.route("/web/login/<string:login>", type="http", auth="none")
#     def web_login_user(self, login, redirect=None, **kw):
#         if login == 'unrecognized_user':
#             s = f'?login=false&hasPassword=true&isRecognised=true'
#             return http.redirect_with_hash('/web/login%s' % s)
#         user = request.env['res.users'].sudo(True).search([['login', '=', login]])
#         if user and user.has_password:
#             s = f'?login={login}&hasPassword=true&name={user.name}&isRecognised=true&id={user.id}'
#             return http.redirect_with_hash('/web/login%s' % s)
#         return http.redirect_with_hash('/web/login/face_recognition')
#
#     @http.route('/web/login/face_recognition', type='http', auth="public", website=True)
#     def web_login_face_recognition(self, **kw):
#         # from here you can call
#         print("HELLO")
#         page = request.render('fr_core.face_recognition_page')
#         print(page)
#         return page
#
#     @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
#     def web_auth_signup(self, *args, **kw):
#         qcontext = self.get_auth_signup_qcontext()
#         qcontext['states'] = request.env['res.country.state'].sudo().search([])
#         qcontext['countries'] = request.env['res.country'].sudo().search([])
#
#         if not qcontext.get('token') and not qcontext.get('signup_enabled'):
#             raise werkzeug.exceptions.NotFound()
#
#         is_error = 'error_iin' in qcontext or 'error_password' in qcontext or 'error_email' in qcontext
#         if not is_error and request.httprequest.method == 'POST':
#             try:
#                 self.do_signup(qcontext)
#                 # Send an account creation confirmation email
#                 if qcontext.get('token'):
#                     user_sudo = request.env['res.users'].sudo().search([('login', '=', qcontext.get('login'))])
#                     template = request.env.ref('auth_signup.mail_template_user_signup_account_created',
#                                                raise_if_not_found=False)
#                     if user_sudo and template:
#                         template.sudo().with_context(
#                             lang=user_sudo.lang,
#                             auth_login=werkzeug.url_encode({'auth_login': user_sudo.email}),
#                         ).send_mail(user_sudo.id, force_send=True)
#
#                 if qcontext and 'face_model_id' in qcontext:
#                     return http.redirect_with_hash('/api/v1/face_model/%s/fill' % (qcontext['face_model_id']))
#                 return self.web_login(*args, **kw)
#             except UserError as e:
#                 qcontext['error'] = e.name or e.value
#             except (SignupError, AssertionError) as e:
#                 if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
#                     qcontext["error_email"] = _("Another user is already registered using this email address.")
#                 else:
#                     _logger.error("%s", e)
#                     qcontext['error'] = _("Could not create a new account.")
#
#         response = request.render('auth_signup.signup', qcontext)
#         response.headers['X-Frame-Options'] = 'DENY'
#         return response
