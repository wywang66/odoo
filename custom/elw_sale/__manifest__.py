# -*- coding: utf-8 -*-
{
    'name': "ELW Sales",

    'summary': "Sales, Quotation, Invoice",

    'description': """
Digital bigbite sales module
    """,
    'sequence': -130,
    'application': True,
    'author': "Digital BigBite",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'ELW/ELW Sales',

    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'sales_team',
        'account_payment',  # -> account, payment, portal
        'utm',],

    # always loaded
    'data': [
        'views/sale_order_view.xml',
    ],
    'license': 'LGPL-3',
}
