# -*- coding: utf-8 -*-
{
    'name': "ELW ERP Management",

    'summary': "ELW ERP Management",

    'description': """
Long description of module's purpose
    """,
    'application': True,
    'sequence': -150,
    'author': "Digital BigBite",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'ELW/ELW Module',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product', 'stock', 'account', 'elw_quality', 'purchase', 'sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/product_view.xml',
        'views/stock_picking_view.xml',
        'views/sale_order_view.xml',
        'views/ir_module_view.xml',
        'views/purchase_order_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': True,
}
