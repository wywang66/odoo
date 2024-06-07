# -*- coding: utf-8 -*-
{
    'name': "inheritance of quality",

    'summary': "inheritance of quality check",

    'description': """
Long description of module's purpose
    """,
    'application': False,
    'sequence': -160,
    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'ELW/ELW Inheritted',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['elw_quality'],
    

    # always loaded
    'data': [
        'views/quality_check_extend_view.xml',
    ],
  
    
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': True,
}

