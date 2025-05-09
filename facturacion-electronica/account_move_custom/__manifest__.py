# -*- coding: utf-8 -*-
{
    'name': "account_move_custom",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['accountant', 'product'],

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
