from odoo import models, fields

class PortalECF(models.Model):
    _name = 'ecf.portal'
    _description = 'Portal ECF'

    name = fields.Char(string="Nombre", default="Portal ECF", readonly=True)
