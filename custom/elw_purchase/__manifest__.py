# -*- coding: utf-8 -*-
{
    'name': "ELW Purchase",

    'summary': "Purchase orders, Tenders and Agreements",

    'description': """
Digital bigbite purchase module
    """,
    'sequence': -140,
    'application': True,
    'author': "Digital BigBite",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'ELW/ELW Purchase',

    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase', 'mail', 'account'],

    # always loaded
    'data': [
        'views/purchase_order_view.xml',
    ],
    'license': 'LGPL-3',
}
