# -*- coding: utf-8 -*-
{
    'name'       : "Face Recognition",

    'summary'    : """
        Face Recognition for Users""",

    'description': """
        Odoo12 module for testing Face Recognition using Python module face-recognition
    """,

    'author'     : "QZHub",
    'website'    : "https://www.qzhub.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category'   : 'Uncategorized',
    'version'    : '0.1',

    # any module necessary for this one to work correctly
    'depends'    : ['base', 'contacts', 'hr', 'hr_attendance', 'web'],

    # always loaded
    'data'       : [
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/employee_photobooth.xml',
        'views/res_partner_view.xml',
        'views/face_recognition_response_view.xml',
        'views/face_recognition_view.xml',
        'views/res_partner_face_encoding_view.xml',
        'data/data.xml'
        # 'views/face_recognition_page.xml',
    ],
    'qweb'       : [
        'static/src/xml/face_recognition_templates.xml',
    ],
    'sequence'   : -1,
    'application': True,
    'installable': True
}
