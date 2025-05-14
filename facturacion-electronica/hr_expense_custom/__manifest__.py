# -*- coding: utf-8 -*-
{
    'name': 'Expense Account ECF',
    'version': '17.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['hr_expense'],
    'category': 'Accounting',
    'summary': 'Personalizaciones para el modelo de facturas',
    'installable': True,
    'application': False,
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/hr_expense_sheet.xml',
    ],
}
