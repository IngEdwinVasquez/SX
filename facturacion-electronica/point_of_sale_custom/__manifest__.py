# -*- coding: utf-8 -*-
{
    'name': 'Point Of Sale ECF',
    'version': '17.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['point_of_sale'],
    'category': 'Accounting',
    'summary': 'Personalizaciones para el modelo de facturas',
    'installable': True,
    'application': False,

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
