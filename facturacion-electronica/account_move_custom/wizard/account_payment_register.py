# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, datetime
import requests
import logging

_logger = logging.getLogger(__name__)


class AccountPaymentRegisterCustom(models.TransientModel):
    _inherit = 'account.payment.register'

    payment_expense_e_ncf = fields.Char(string='E-NCF')
    payment_expense_ecf_type = fields.Selection([
        ('43', 'Gastos Menores Electrónico'),
        ('47', 'Comprobante para Pagos al Exterior Electrónico'),
        ('0', 'Ya Tiene NCF')
    ], default='43', string='Tipo de ECF')
    payment_expense_retention_perception_indicator = fields.Selection([
        ('1', 'Retención'),
        ('2', 'Percepción')
    ], default='1', string='Indicador Agente Retención Percepción')

    def action_create_payments(self):
        if self.line_ids.move_id.move_type == 'in_invoice' and self.line_ids.move_id.expense_sheet_id:
            if not self.payment_expense_e_ncf:
                self.api_request()
            else:
                self.line_ids.move_id.expense_ecf_type = self.payment_expense_ecf_type
                self.line_ids.move_id.expense_e_ncf = self.payment_expense_e_ncf

        res = super().action_create_payments()
        return res

    def api_request(self):
        if not self.payment_expense_ecf_type:
            raise ValidationError("El campo 'Tipo de ECF' es requerido")
        if self.payment_expense_ecf_type == '47' and not self.payment_expense_retention_perception_indicator:
            raise ValidationError("El campo 'Indicador Agente Retención Percepción' es requerido")
        ecf_encabezado = {
            'IdDoc': self.get_id_doc(),
            'Emisor': self.get_emisor()
        }
        detalles_items = {
            'Item': self.get_items()
        }
        url = 'https://pymesecf.com/api/ECF/EnvioECF'
        params = {
            'Ambiente': 'certecf'
        }
        headers = {
            'Content-Type': 'application/json'
        }
        body = {
            'ECFEncabezado': ecf_encabezado,
            'DetallesItems': detalles_items
        }

        response = requests.post(url, headers=headers, params=params, json=body)
        response_data = response.json()

        if response.status_code == 200:
            if 'ncf' in response_data and 'fechaYHoraFirmaDigital' in response_data and 'codigoDeSeguridad' in response_data and 'qrCode' in response_data:
                date_format = '%d-%m-%Y %H:%M:%S'
                digital_signature_date = datetime.strptime(response_data['fechaYHoraFirmaDigital'], date_format)
                self.line_ids.move_id.expense_ecf_type = self.payment_expense_ecf_type
                self.line_ids.move_id.expense_retention_perception_indicator = self.payment_expense_retention_perception_indicator
                self.line_ids.move_id.expense_e_ncf = response_data['ncf']
                self.line_ids.move_id.expense_digital_signature_date = digital_signature_date
                self.line_ids.move_id.expense_security_code = response_data['codigoDeSeguridad']
                self.line_ids.move_id.expense_fiscal_qr = response_data['qrCode']
                return
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
            'TipoeCF': self.payment_expense_ecf_type
        }
        return id_doc

    def get_emisor(self):
        emisor = {
            'RNCEmisor': self.env.user.company_id.vat
        }
        return emisor

    def get_items(self):
        item = []
        expenses = self.line_ids.move_id.invoice_line_ids
        line_number = 1
        for line in expenses:
            if self.payment_expense_ecf_type == '43':
                item.append({
                    'NumeroLinea': str(line_number),
                    'IndicadorFacturacion': '4',
                    'NombreItem': line.product_id.name,
                    'IndicadorBienoServicio': '2' if line.product_id.type == 'service' else '1',
                    'CantidadItem': str(int(line.quantity)),
                    'UnidadMedida': line.product_id.unit_of_measure,
                    'PrecioUnitarioItem': str(line.price_unit),
                    'MontoItem': str(round(line.price_unit * line.quantity, 2))
                })
            if self.payment_expense_ecf_type == '47':
                item.append({
                    'NumeroLinea': str(line_number),
                    'IndicadorFacturacion': '4',
                    "retencion": {
                        "indicadorAgenteRetencionoPercepcion": self.payment_expense_retention_perception_indicator,
                        "montoISRRetenido": str(round(int(line.price_unit) * 0.27, 2))
                    },
                    'NombreItem': line.product_id.name,
                    'IndicadorBienoServicio': '2' if line.product_id.type == 'service' else '1',
                    'CantidadItem': str(int(line.quantity)),
                    'UnidadMedida': line.product_id.unit_of_measure,
                    'PrecioUnitarioItem': str(line.price_unit),
                    'MontoItem': str(round(line.price_unit * line.quantity, 2))
                })
            line_number += 1
        return item
