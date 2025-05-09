# -*- coding: utf-8 -*-
{
    'name': "Point Of Sale Custom",

    'summary': "",

    'description': """
Herencia de point_of_sale
    """,

    'author': "Gritvap",
    "contribuitors": [
        "Moisés Sia <msira2709.dev@gmail.com>",
        "Eduardo Bolivar <eduardobolivar2407@gmail.com>"
    ],
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
    ],
    "assets":{
        'point_of_sale._assets_pos': [
            'point_of_sale_custom/static/src/**/*',
        ]
    },
}
