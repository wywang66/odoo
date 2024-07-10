# -*- coding: utf-8 -*-
{
    'name': "ELW Manufacturing",

    'summary': "ELW Manufacturing",

    'description': """
Long description of module's purpose
    """,
    'application': True,
    'sequence': -125,
    'author': "Digital BigBite",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'ELW/ELW Manufacturing',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['mrp', 'elw_quality'],

    # always loaded
    'data': [
        # 'security/elw_module_security_data.xml',
        # 'security/ir.model.access.csv',
        'views/mrp_view.xml',
        'views/mrp_workcenter_view_inherit.xml',
        'views/maintenance_view_inherit.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': True,
}
