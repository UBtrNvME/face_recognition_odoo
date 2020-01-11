# -*- coding: utf-8 -*-
{
    'name': "Face Recognition",

    'summary': """
        Face Recognition for Users""",

    'description': """
        Odoo12 module for testing Face Recognition using Python module face-recognition
    """,

    'author': "QZHub",
    'website': "http://qzhub.kz:8080",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts', 'hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/face_recognition_views.xml',
        'views/face_recognition_message_wizard.xml',
    ],
    'sequence': -1,
    'application': True,
    'installable': True
}