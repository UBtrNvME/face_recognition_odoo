from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'Res Partner'

    # attachment_ids = fields.Many2many(comodel_name="ir.attachment",
    #                                   relation="face_images_res_partner_ir_attachment_rel",
    #                                   column1="partner_id",
    #                                   column2="attachment_id")
    face_model_id = fields.Many2one(comodel_name="res.partner.face.model",
                                    string="Face Encodings")
    iin = fields.Integer(string="Individual Identification Number")
