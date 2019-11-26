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
    'depends': ['base', 'disable_odoo_online', 'project',
                'project_task_default_stage', 'contacts', 'web_widget_url_advanced'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/project_project_views.xml',
        'views/project_region_views.xml',
        'views/res_partner_views.xml',
        'views/frontend/project.xml',
        'views/frontend/user.xml',
        'data/mail_servers.xml',
        'data/project_type_data.xml',
        'views/resources.xml',
    ],
    'sequence': -1,
    'application': True,
    'installable': True
}