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

    # TODO make better one2one mechanis
    def _detach_partner_id_from_referenced_face_model(self):
        """ Unlinks partner id from linked face model id.
            In case there is no linked partner id raises AssertionError.

        :return: None
        """
        assert self.face_model_id, "Partner has no model!"
        if self.face_model_id.partner_id != False:
            self.face_model_id.write({
                "partner_id": False,
                "is_deleting": True,
            })


    def _attach_partner_id_to_referenced_face_model(self, face_model_id):
        """ Links values of `face_model_id` given in the arguments and partner id.
            In case there has not been given parameter raises AssertionError

        :param face_model_id: id of the face model to be linked with
        :return: None
        """
        assert face_model_id, "No value has been given!"
        face_model = self.env["res.partner.face.model"].browse(face_model_id)[0]
        face_model.partner_id = self.id

    @api.model
    def create(self, vals):
        rp = super().create(vals)
        if vals["face_model_id"]:
            rp._attach_partner_id_to_referenced_face_model(vals["face_model_id"])
        return rp

    def write(self, vals):
        if vals.get("face_model_id"):
            face_model_id = vals["face_model_id"]
            if face_model_id:
                self._attach_partner_id_to_referenced_face_model(face_model_id)
            elif "is_deleting" not in vals:
                self._detach_partner_id_from_referenced_face_model()
                vals["is_deleting"] = True
            else:
                vals.pop("is_deleting")


        return super().write(vals)