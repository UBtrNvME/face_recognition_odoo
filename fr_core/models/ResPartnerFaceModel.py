import base64
import json
from io import BytesIO

import face_recognition
import numpy as np
from PIL import Image

from odoo import api, fields, models
import logging
from odoo.tools.translate import _


_logger = logging.getLogger(__name__)


class ResPartnerFaceModel(models.Model):
    _name = 'res.partner.face.model'

    name = fields.Char(string='Name', readonly=True)
    face_encodings = fields.Text(string='Face Encoding')
    is_encodings_hidden = fields.Boolean(string='Show/Hide Encodings')
    type = fields.Selection(selection=[('temp', 'Temporary'), ('perm', 'Permanent')],
                            string='Permanent/Temporary Encoding',
                            default='temp')
    number_of_encodings = fields.Integer(string='Number of Encodings', default=0)
    attachment_ids = fields.Many2many(comodel_name='ir.attachment',
                                      relation='res_partner_face_model_ir_attachment_rel',
                                      column1='face_model_id',
                                      column2='attachment_id')
    partner_id = fields.Many2one(comodel_name='res.partner',
                                 string='Partner',
                                 compute='compute_partner',
                                 inverse='partner_inverse',
                                 store=True)
    # Buffer for One2one field
    partner_ids = fields.One2many(comodel_name='res.partner',
                                  inverse_name='face_model_id')

    def _compute_face_encoding(self, base64encoded_image):
        """ Computes face encodings from the base64 encoded image object.
            Returns set of numpy array of 128 elements that characterizes face,
            corresponding to each face on the image.

            If no face has been found on the image returns an empty array.

            :param base64encoded_image: image array object from which to encode
            :type base64encoded_image: :class: 'ndarray'

            :returns: A list of numpy arrays containing elements which
                      characterize face image.
            :rtype: list(array())
        """

        face_image = self.load_image_base64(base64encoded_image)
        return face_recognition.face_encodings(face_image, None, 20, 'large')[0]

    @staticmethod
    def load_image_base64(base64string: str) -> np.ndarray:
        """ Converts binary string encoded with base64 into numpy array,
            which then can be used by face recognition libraries,
            to create face encodings.

            Do not handles wrong inputs, which will only cause b64decode error.
            Returns numpy array of the image,
            which was beforehand convert to RGB by the function

        :param base64string: binary string in 64base encoding
        :type base64string: str
        :return: array representing imputed image binary string
        :rtype: np.ndarray
        """
        image = Image.open(BytesIO(base64.b64decode(base64string)))
        return np.array(image.convert('RGB'))

    def get_attachment_ids(self):
        attachment_local_urls = []
        for attachment in self.env['ir.attachment'].search([['id', 'in', self.attachment_ids.ids]]):
            attachment_local_urls.append(attachment.local_url)
        return attachment_local_urls

    def add_new_face_image_attachment(self, image_datas: str, image_name: str = '', with_encoding: bool = False) -> (
            int, str):
        """ Method which creates new attachment in ir.attachment table with image_datas and image_name parsed,
            and after that append this new attachment Face Model.

            By default doesn't generate Face Encoding, and doesn't append it to Face Model,
            however with_encoding parameter can be specified to do so.
            Returns `attachment_id` and `message` which says what has been done, or problem which has been encountered.

        :param image_datas: image binary string base64 encoded from which to create attachment
        :type image_datas: str
        :param image_name: name of the image to be attached, doesnt result in name of attachment, just a flag
        :type image_name: str
        :param with_encoding: a flag which tells to switch on/off image face encoding
        :type with_encoding: bool
        :return: tuple of attachment_id and message describing process
        :rtype: (int, bool)
        """
        for fm in self:
            new_encoding = False
            response = 'Created Attachment'

            if with_encoding:
                try:
                    new_encoding = self._compute_face_encoding(image_datas)
                except:
                    return -1, 'Problem Encoding'

            number_of_attachments = len(fm.attachment_ids.ids)
            attachment_name_prefix = 'unknown_' if image_name == '' else 'face_'
            attachment_name_postfix = '_number_%d.jpeg' % (number_of_attachments + 1) if image_name != '' else '.jpeg'
            attachment_name = attachment_name_prefix + f'image_fm_{fm.id}' + attachment_name_postfix

            attachment = self.env['ir.attachment'].create({
                'name'     : attachment_name,
                'type'     : 'binary',
                'datas'    : image_datas,
                'res_model': 'res.partner.face.model',
                'mimetype' : 'image/jpeg'
            })
            fm.attachment_ids = [(4, attachment.id, 0)]
            if with_encoding:
                # TODO move this block of code into separate function
                fm.face_encodings = fm.face_encodings or '{}'
                jsondata = json.loads(fm.face_encodings)
                jsondata[str(attachment.id)] = list(new_encoding)
                fm.face_encodings = json.dumps(jsondata)
                response = 'Created Encoding'
            fm.number_of_encodings += 1
            return attachment, response

    def show_face_encodings(self):
        """ Method which changes value of the field `is_encoding_hidden` to False,
            which then results in unhiding of the `field face_encoding` from the form view
        """
        for fm in self:
            fm.is_encodings_hidden = False

    def hide_face_encodings(self):
        """ Method which changes value of the field `is_encoding_hidden` to True,
            which then results in hiding of the `field face_encoding` from the form view
        """
        for fm in self:
            fm.is_encodings_hidden = True

    @api.model
    def create(self, vals):
        if vals.get('partner_id'):
            if vals['type'] == 'temp':
                vals['type'] = 'perm'
                # raise Warning(_('Error!'), _('We are going to make this as a permanent Face Model'))

        if vals.get('type'):
            if vals['type'] == 'temp':
                vals['name'] = self.env['ir.sequence'].next_by_code('seq.face.model.temporary')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('seq.face.model.permanent') + '-' + \
                               self.env['res.partner'].browse(vals['partner_id'])[0].name

        if vals.get('attachment_ids') != [[6, 0, []]]:
            pass

        res = super(ResPartnerFaceModel, self).create(vals)

        return res

    # TODO Add mechanics of removing unnecessary temp face models
    @api.model
    def create_temporary_face_model(self, vals):
        if vals.get('image_in_base64') and vals.get('face_encoding'):
            image_in_base64, face_encoding = vals['image_in_base64'], vals['face_encoding']
            face_model = self.env['res.partner.face.model'].sudo(True).create({
                'type': 'temp'
            })

            attachment, _ = face_model.add_new_face_image_attachment(image_in_base64, 'temp')
            # TODO move this block of code into separate function
            face_model.face_encodings = face_model.face_encodings or '{}'
            jsondata = json.loads(face_model.face_encodings)
            jsondata[str(attachment.id)] = list(face_encoding[0])
            face_model.face_encodings = json.dumps(jsondata)
            return face_model
        return None

    def write(self, vals):
        attachment_tuple = vals.get('attachment_ids')
        if attachment_tuple and attachment_tuple[0][0] == 6 and attachment_tuple[0][2] == []:
            self.face_encodings = ''
        if vals.get('partner_id'):
            if self.type == 'temp':
                vals['type'] = 'perm'
                vals['name'] = self.env['ir.sequence'].next_by_code('seq.face.model.permanent') + '-' + \
                               self.env['res.partner'].browse(vals['partner_id'])[0].name

        elif attachment_tuple and attachment_tuple[0][0] == 6:
            attachment_ids = attachment_tuple[0][2]
            json_data = json.loads(self.face_encodings) if self.face_encodings else {}
            keys = list(json_data.keys())
            for key in keys:
                if key not in attachment_ids:
                    json_data.pop(key)
            number_of_encodings = 0
            for attachment_id in attachment_ids:
                number_of_encodings += 1
                if attachment_id not in json_data:
                    json_data[str(attachment_id)] = list(
                        self._compute_face_encoding(self.env['ir.attachment'].browse(attachment_id)[0].datas))
            vals['face_encodings'] = json.dumps(json_data)
            vals['number_of_encodings'] = number_of_encodings

        return super(ResPartnerFaceModel, self).write(vals)

    @api.model
    def compare_with_unknown(self, unknown_encoding):
        similar_partners, face_models = self._organize_model_objects_in_dictionary()
        batch_number = 0

        if len(similar_partners) == 1:
            encoding_batch = []
            for face_model in face_models:
                encoding_batch.append(face_model[list(face_model.keys())[0]])

            results = face_recognition.compare_faces(encoding_batch, unknown_encoding[0], 0.4)
            for i in range(len(results)):
                if not results[i]:
                    similar_partners.pop(i)
                    face_models.pop(i)
        else:
            while len(similar_partners) > 1:
                encoding_batch = []
                for face_model in face_models:
                    encoding_batch.append(face_model[list(face_model.keys())[0]])
                results = face_recognition.compare_faces(encoding_batch, unknown_encoding[0], 0.4)
                deleted = 0
                for i in range(len(results)):
                    if not results[i]:
                        similar_partners.pop(i - deleted)
                        face_models.pop(i - deleted)
                        deleted += 1
                batch_number += 1
        if len(similar_partners) and len(similar_partners) <= 1:
            user = self.env['res.users'].search([['partner_id', '=', similar_partners[0]]])
        else:
            user = False
        return user

    def _organize_model_objects_in_dictionary(self):
        face_models = []
        partners = []

        gotten_face_models_records = self.search_read([
            ['type', '=', 'perm'],
            ['face_encodings', '!=', '']
        ], fields=['partner_id', 'face_encodings'])

        for record in gotten_face_models_records:
            face_models.append(json.loads(record['face_encodings']))
            if record['partner_id']:
                partners.append(record['partner_id'][0])
        return partners, face_models

    @api.depends('partner_ids')
    def compute_partner(self):
        for fm in self:
            if len(fm.partner_ids) > 0:
                fm.write({
                    'partner_id': fm.partner_ids[0].id
                })

    def partner_inverse(self):
        for fm in self:
            if len(fm.partner_ids) > 0:
                # delete previous reference
                partner = self.env['res.partner'].browse(fm.partner_ids[0].id)
                partner.face_model_id = False
            # set new reference
            fm.partner_id.face_model_id = fm

