# -*- coding: utf-8 -*-
{
    'name': 'Account Move ECF',
    'version': '17.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['accountant', 'product'],
    'category': 'Accounting',
    'summary': 'Modulo de facturas electronicas',
    'installable': True,
    'application': False,

    # always loaded
    'data': [
        'security/ir.model.access.csv',

        'views/account_move_custom_views.xml',
        'views/product_template_custom_views.xml',
        'views/templates.xml',

        'reports/account_move_custom_report.xml',

        'wizard/account_payment_register_view.xml',
    ],
}
