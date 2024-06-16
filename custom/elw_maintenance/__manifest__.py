# -*- coding: utf-8 -*-
{
    'name': "ELW Maintenance",

    'summary': "Equipment Calibration",

    'description': """
Digital Bigbite equipment calibration
    """,
    'sequence': -120,
    'application': True,
    'author': "Digital BigBite",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'ELW/ELW Maintenance',

    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['maintenance'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/dbb_email_template_data.xml',
        # 'data/dbb_email_cron_data.xml',
        'data/sequence_data.xml',
        'data/calibration_data.xml',
        'views/calibration_stage_view.xml',
        'views/maintenance_calibration_view.xml',

        # 'views/dbb_calibration_overdue_view.xml',
    ],
    'license': 'LGPL-3',
}
