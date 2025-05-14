{
    "name": "Portal ECF",
    "version": "17.0.1",
    "summary": "Portal ECF integrado mediante iframe",
    "description": "Agrega un menú 'Portal ECF' que muestra el portal ECF dentro de Odoo en un iframe.",
    "author": "Gleny Lugo",
    "website": "https://tusitio.com",
    "category": "Tools",
    "license": "LGPL-3",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/ecf_portal_view.xml",
        "views/ecf_portal_menu.xml"
    ],
    "installable": True,
    "application": True
}
