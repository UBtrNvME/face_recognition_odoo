# -*- coding: utf-8 -*-
{
    'name': "gpodem",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'orange_theme_odoo12', 'odoo_web_login', 'disable_odoo_online', 'project',
                'project_task_default_stage'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        # 'views/templates.xml',
        'views/project_project_views.xml',
    ],
    'sequence': -1,
    'application': True,
    'installable': True
}
