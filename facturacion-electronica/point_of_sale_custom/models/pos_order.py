# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'
    _description = 'Clase para modificar el modelo de pos.order'

    pos_ecf_type = fields.Char(string='Tipo ECF')
    pos_e_ncf = fields.Char(string='E-NCF', readonly=True)
    pos_security_code = fields.Char(string='Código Seguridad', readonly=True)
    pos_digital_signature_date = fields.Datetime(string='Fecha Firma Digital', readonly=True)
    pos_fiscal_qr = fields.Binary(string='QR FISCAL', readonly=True)

    def action_pos_order_paid(self):
         # Validación: si el RNC de la empresa está vacío, no ejecutar nada
        if not self.env.user.company_id.vat:
           _logger.warning("La empresa no tiene RNC (vat). Se omite el envío del documento fiscal.")
           return
        res = super(PosOrder, self).action_pos_order_paid()
        self.api_request()
        return res

    def action_pos_order_invoice(self):
         # Validación: si el RNC de la empresa está vacío, no ejecutar nada
        if not self.env.user.company_id.vat:
           _logger.warning("La empresa no tiene RNC (vat). Se omite el envío del documento fiscal.")
           return
        res = super(PosOrder, self).action_pos_order_invoice()
        return res

    def api_request(self):
         # Validación: si el RNC de la empresa está vacío, no ejecutar nada
        if not self.env.user.company_id.vat:
           _logger.warning("La empresa no tiene RNC (vat). Se omite el envío del documento fiscal.")
           return
        
        ecf_encabezado = {
            'IdDoc': self.get_id_doc(),
            'Emisor': self.get_emisor(),
            'Comprador': self.get_comprador()
        }
        detalles_items = {
            'Item': self.get_items()
        }
        if self.pos_ecf_type == '32' and int(self.amount_total) < 250000:
            url = 'https://pymesecf.com/api/ECF/EnvioResumen'
            params = {
                'Ambiente': 'testecf',
                'ticket': 'false'
            }
        else:
            url = 'https://pymesecf.com/api/ECF/EnvioECF?Ambiente=testecf'
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

        response = requests.post(url, headers=headers, params=params, json=body)
        response_data = response.json()

        if response.status_code == 200:
            if 'ncf' in response_data and 'fechaYHoraFirmaDigital' in response_data and 'codigoDeSeguridad' in response_data and 'qrCode' in response_data:
                date_format = '%d-%m-%Y %H:%M:%S'
                digital_signature_date = datetime.strptime(response_data['fechaYHoraFirmaDigital'], date_format)
                if self.to_invoice:
                    self.action_pos_order_invoice()
                    if self.account_move:
                        self.account_move.out_invoice_e_ncf = response_data['ncf']
                        self.account_move.out_invoice_digital_signature_date = digital_signature_date
                        self.account_move.out_invoice_security_code = response_data['codigoDeSeguridad']
                        self.account_move.out_invoice_fiscal_qr = response_data['qrCode']
                        _logger.info(self.account_move.out_invoice_e_ncf)
                self.pos_e_ncf = response_data['ncf']
                self.pos_digital_signature_date = digital_signature_date
                self.pos_security_code = response_data['codigoDeSeguridad']
                self.pos_fiscal_qr = response_data['qrCode']
            else:
                _logger.info(f'Body:\n{body}')
                _logger.info(f'Status Code:\n{response.status_code}')
                _logger.info(f'Respuesta:\n{response_data}')
                raise UserError(f"Error al obtener los datos:\n{response_data['mensajes'][0]['valor']}")
        else:
            _logger.info(f'Body:\n{body}')
            _logger.info(f'Status Code:\n{response.status_code}')
            _logger.info(f'Respuesta:\n{response_data}')
            raise UserError(f"Error al consumir la API\n{response_data}")

    def get_id_doc(self):
        if self.payment_ids.payment_method_id[0].name == 'Tarjeta' or self.payment_ids.payment_method_id[0].name == 'Efectivo':
            id_doc = {
                'TipoeCF': self.pos_ecf_type,
                'IndicadorMontoGravado': '0',
                'TipoIngresos': '01',
                'TipoPago': '1'
            }
        else:
            a_month_later = datetime.now() + relativedelta(months=1)
            id_doc = {
                'TipoeCF': self.pos_ecf_type,
                'IndicadorMontoGravado': '0',
                'TipoIngresos': '01',
                'TipoPago': '2',
                'FechaLimitePago': a_month_later.strftime('%d-%m-%Y')
            }
        return id_doc

    def get_emisor(self):
        emisor = {
            'RNCEmisor': self.env.user.company_id.vat
        }
        return emisor

   
    def get_comprador(self):
        if not self.partner_id.vat:
           raise ValidationError(f"El cliente '{self.partner_id.name}' no tiene RNC (vat) configurado.")
    
        comprador = {
          'RNCComprador': str(self.partner_id.vat),
          'RazonSocialComprador': self.partner_id.name
        }
        return comprador

    def get_items(self):
        item = []
        products = self.lines
        line_number = 1
        for line in products:
            if len(line.product_id.taxes_id) > 0:
                tax_name = line.product_id.taxes_id[0].name
                if tax_name == '18% ITBIS':
                    invoice_indicator = '1'
                elif tax_name == '16% ITBIS':
                    invoice_indicator = '2'
                elif tax_name == '0% ITBIS':
                    invoice_indicator = '3'
                elif tax_name == 'ITBIS Exempt':
                    invoice_indicator = '4'
                else:
                    raise UserError(f"Error: El impuesto '{tax_name}' no está permitido.")
            else:
                raise UserError(f"Error: No tiene impuesto.")

            item.append({
                'NumeroLinea': str(line_number),
                'IndicadorFacturacion': invoice_indicator,
                'NombreItem': line.product_id.name,
                'IndicadorBienoServicio': '2' if line.product_id.type == 'service' else '1',
                'CantidadItem': str(int(line.qty)),
                'UnidadMedida': line.product_id.uom_id.name,
                'PrecioUnitarioItem': str(line.price_unit),
                'MontoItem': str(round(line.price_unit * line.qty, 2))
            })
            line_number += 1
        return item
