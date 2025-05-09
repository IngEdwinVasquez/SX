# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import requests
import logging
from datetime import date, datetime

_logger = logging.getLogger(__name__)


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'
    _description = 'Clase para modificar el modulo de Gastos'

    
    expense_e_ncf = fields.Char(string='E-NCF')
    expense_security_code = fields.Char(string='Código Seguridad', readonly=True)
    expense_digital_signature_date = fields.Datetime(string='Fecha Firma Digital', readonly=True)
    expense_fiscal_qr = fields.Binary(string='QR FISCAL', readonly=True)
    expense_ecf_type = fields.Selection([
        ('43', 'Gastos Menores Electrónico'),
        ('47', 'Comprobante para Pagos al Exterior Electrónico'),
        ('0', 'Ya Tiene NCF')
    ], default='43', string='Tipo de ECF')

  #  def action_register_payment(self):
        #if self.expense_line_ids and len(self.expense_line_ids) > 0:
         #   if not self.expense_e_ncf:
          #      raise ValidationError("El campo E-NCF es requerido.")

    #    res = super().action_register_payment()
     #   return res

    def api_request(self):
         # Validación: si el RNC de la empresa está vacío, no ejecutar nada
        if not self.env.user.company_id.vat:
           _logger.warning("La empresa no tiene RNC (vat). Se omite el envío del documento fiscal.")
           return
        
        ecf_encabezado = {
            'IdDoc': self.get_id_doc(),
            'Emisor': self.get_emisor()
        }
        detalles_items = {
            'Item': self.get_items()
        }
       
        params = {
            'Ambiente': 'testecf'
        }
        headers = {
            'Content-Type': 'application/json'
        }
        body = {
            'ECFEncabezado': ecf_encabezado,
            'DetallesItems': detalles_items
        }
        response = requests.post('https://pymesecf.com/api/ECF/EnvioECF', headers=headers, params=params, json=body)
        response_data = response.json()

        if response.status_code == 200:
            if 'ncf' in response_data and 'fechaYHoraFirmaDigital' in response_data and 'codigoDeSeguridad' in response_data and 'qrCode' in response_data:
                date_format = '%d-%m-%Y %H:%M:%S'
                digital_signature_date = datetime.strptime(response_data['fechaYHoraFirmaDigital'], date_format)
                self.expense_e_ncf = response_data['ncf']
                self.expense_digital_signature_date = digital_signature_date
                self.expense_security_code = response_data['codigoDeSeguridad']
                self.expense_fiscal_qr = response_data['qrCode']
            else:
                _logger.info(f'Body:\n{body}')
                _logger.info(f'Status Code:\n{response.status_code}')
                _logger.info(f'Respuesta:\n{response_data}')
                raise ValidationError(f"Error al obtener los datos:\n{response_data['mensajes'][0]['valor']}")
        else:
            _logger.info(f'Body:\n{body}')
            _logger.info(f'Status Code:\n{response.status_code}')
            _logger.info(f'Respuesta:\n{response_data}')
            raise ValidationError(f"Error al consumir la API\n{response_data}")

    def get_id_doc(self):
        id_doc = {
            'TipoeCF': self.expense_ecf_type
        }
        return id_doc

    def get_emisor(self):
        emisor = {
            'RNCEmisor': self.env.user.company_id.vat
        }
        return emisor

    def get_items(self):
        item = []
        expenses = self.expense_line_ids
        line_number = 1
        for line in expenses:
            if self.expense_ecf_type == '43':
                item.append({
                    'NumeroLinea': str(line_number),
                    'IndicadorFacturacion': '4',
                    'NombreItem': line.product_id.name,
                    'IndicadorBienoServicio': '2' if line.product_id.type == 'service' else '1',
                    'CantidadItem': str(int(line.quantity)),
                    'UnidadMedida': line.product_id.unit_of_measure,
                    'PrecioUnitarioItem': str(line.price_unit),
                    'MontoItem': str(int(line.total_amount))
                })
            if self.expense_ecf_type == '47':
                item.append({
                    'NumeroLinea': str(line_number),
                    'IndicadorFacturacion': '4',
                    "retencion": {
                        "indicadorAgenteRetencionoPercepcion": "1",
                        "montoISRRetenido": str(round(int(line.total_amount) * 0.27, 2))
                    },
                    'NombreItem': line.product_id.name,
                    'IndicadorBienoServicio': '2' if line.product_id.type == 'service' else '1',
                    'CantidadItem': str(int(line.quantity)),
                    'UnidadMedida': line.product_id.unit_of_measure,
                    'PrecioUnitarioItem': str(line.price_unit),
                    'MontoItem': str(int(line.total_amount))
                })
            line_number += 1
        return item
