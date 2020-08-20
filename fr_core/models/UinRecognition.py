from odoo import fields, models, api


class UinRecognition(models.Model):
    _name = 'uin.recognition'

    name = fields.Char(string='Name')
    image = fields.Binary(string='UIN image')
