# -*- coding: utf-8 -*-
{
    'name': "ELW Product Rework",

    'summary': "Product Repair and Rework",

    'description': """
Digital bigbite sales module
    """,
    'sequence': -80,
    'application': True,
    'author': "Digital BigBite",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'ELW/ELW Product Rework',

    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'sale_management'],

    # always loaded
    'data': [
        # 'views/sale_order_view.xml',
    ],
    'license': 'LGPL-3',
}
