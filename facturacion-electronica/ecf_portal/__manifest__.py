{
    'name': 'Portal ECF',
    'version': '17.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['base'],
    'category': 'Accounting',
    'summary': 'Portal ECF integrado mediante iframe',
    'description': "Agrega un menú 'Portal ECF' que muestra el portal ECF dentro de Odoo en un iframe.",
    'installable': True,
    'application': False,
    
    
    "data": [
        "security/ir.model.access.csv",
        "views/ecf_portal_view.xml",
        "views/ecf_portal_menu.xml"
    ],
    "installable": True,
    "application": True
}
