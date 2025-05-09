# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import requests
import logging
from datetime import date, datetime, timedelta

_logger = logging.getLogger(__name__)


class AccountMoveCustom(models.Model):
    _inherit = 'account.move'
    _description = 'Clase para modificar el modulo de cuentas'
    
    out_invoice_e_ncf = fields.Char(string='E-NCF', readonly=True)
    out_invoice_security_code = fields.Char(string='Código Seguridad', readonly=True)
    out_invoice_digital_signature_date = fields.Datetime(string='Fecha Firma Digital', readonly=True)
    out_invoice_fiscal_qr = fields.Binary(string='QR FISCAL', readonly=True)
    out_refund_e_ncf = fields.Char(string='E-NCF', readonly=True)
    out_refund_security_code = fields.Char(string='Código Seguridad', readonly=True)
    out_refund_digital_signature_date = fields.Datetime(string='Fecha Firma Digital', readonly=True)
    out_refund_qr = fields.Binary(string='QR Nota de Crédito', readonly=True)
    expense_e_ncf = fields.Char(string='E-NCF')
    expense_security_code = fields.Char(string='Código Seguridad', readonly=True)
    expense_digital_signature_date = fields.Datetime(string='Fecha Firma Digital', readonly=True)
    expense_fiscal_qr = fields.Binary(string='QR FISCAL', readonly=True)
    purchase_order_e_ncf = fields.Char(string='E-NCF')
    purchase_order_security_code = fields.Char(string='Código Seguridad', readonly=True)
    purchase_order_digital_signature_date = fields.Datetime(string='Fecha Firma Digital', readonly=True)
    purchase_order_fiscal_qr = fields.Binary(string='QR FISCAL', readonly=True)
    purchase_order_ecf_type = fields.Selection([
        ('41', 'Compras Electrónico'),
        ('0', 'Ya Tiene NCF')
    ], string='Tipo de ECF')
    purchase_order_retention_perception_indicator = fields.Selection([
        ('1', 'Retención'),
        ('2', 'Percepción')
    ], string='Indicador Agente Retención Percepción')
    purchase_order_payment_type = fields.Selection([
        ('1', 'Contado'),
        ('2', 'Crédito'),
        ('3', 'Gratuito')
    ], string='Tipo de pago')
    expense_ecf_type = fields.Selection([
        ('43', 'Gastos Menores Electrónico'),
        ('47', 'Comprobante para Pagos al Exterior Electrónico'),
        ('0', 'Ya Tiene NCF')
    ], string='Tipo de ECF')
    expense_retention_perception_indicator = fields.Selection([
        ('1', 'Retención'),
        ('2', 'Percepción')
    ], string='Indicador Agente Retención Percepción')
    out_invoice_ecf_type = fields.Selection([
        ('31', 'Factura de Crédito Fiscal Electrónico'),
        ('32', 'Factura de Consumo Electrónica'),
        ('33', 'Nota de Débito Electrónica'),
        ('34', 'Nota de Crédito Electrónica'),
        ('44', 'Regímenes Especiales Electrónico'),
        ('45', 'Gubernamental Electrónico'),
        ('46', 'Comprobante de Exportaciones Electrónico')
    ], default='32', string='Tipo de ECF')
    out_invoice_income_type = fields.Selection([
        ('01', 'Ingresos por operaciones (No financieros)'),
        ('02', 'Ingresos Financieros'),
        ('03', 'Ingresos Extraordinarios'),
        ('04', 'Ingresos por Arrendamientos'),
        ('05', 'Ingresos por Venta de Activo Depreciable'),
        ('06', 'Otros Ingresos')
    ], default='01', string='Tipo de ingreso')
    out_invoice_payment_type = fields.Selection([
        ('1', 'Contado'),
        ('2', 'Crédito'),
        ('3', 'Gratuito')
    ], default='1', string='Tipo de pago')
    out_refund_modification_code = fields.Selection([
        ('1', 'Anula el NCF modificado'),
        ('2', 'Corrige Texto del Comprobante Fiscal modificado'),
        ('3', 'Corrige montos del NCF modificado'),
        ('4', 'Reemplazo NCF emitido en contingencia'),
        ('5', 'Referencia Factura Consumo Electrónica')
    ], default='1', string='Código de Modificación')

    def action_post(self):
        res = super().action_post()
        if self.move_type:
            purchase_order = self.env['purchase.order'].search([('invoice_ids', 'in', [self.id])])
            if self.move_type == 'in_invoice' and not purchase_order:
                return res
            if self.company_id.vat:
                self.api_request()
            else:
                _logger.warning("La empresa no tiene RNC (vat). Se omite el envío del documento fiscal.")
        return res


    def action_create_payments(self):
        if self.move_type:
            if self.move_type == 'in_invoice' and self.expense_sheet_id:
                if not self.expense_e_ncf:
                    if self.company_id.vat:
                        self.api_request()
                    else:
                        _logger.warning("La empresa no tiene RNC (vat). Se omite el envío del documento fiscal.")
        return super().action_create_payments()


    def api_request(self):
         # Validación: si el RNC de la empresa está vacío, no ejecutar nada
        if not self.company_id.vat:
           _logger.warning("La empresa no tiene RNC (vat). Se omite el envío del documento fiscal.")
           return
         #url = 'https://pymesecf.com/api/ECF/EnvioECF'

        # Nota de creditos de proveedores
        if self.move_type == 'in_refund':
            return
        # Nota de debito de proveedores
        if self.move_type == 'in_debit':
            return
        # Nota de debito de clientes
        if self.move_type == 'out_debit':
            return
        # Asientos Contables de Gastos
        if self.move_type == 'entry':
            return

        headers = {
            'Content-Type': 'application/json'
        }

        ecf_encabezado = {}
        detalles_items = {}
        params = {}
        body = {}
        _logger.info("Valor de variable: %s", self.move_type)
        
        # Facturas de clientes
        if self.move_type == 'out_invoice':
            if not self.out_invoice_ecf_type:
                raise ValidationError("El campo 'Tipo de ECF' es requerido")
            if not self.out_invoice_income_type:
                raise ValidationError("El campo 'Tipo de ingreso' es requerido")
            if not self.out_invoice_payment_type:
                raise ValidationError("El campo 'Tipo de Pago' es requerido")
            ecf_encabezado = {
                'IdDoc': self.get_id_doc(),
                'Emisor': self.get_emisor(),
                'Comprador': self.get_comprador()
            }

            detalles_items = {
                'Item': self.get_items()
            }

            if self.out_invoice_ecf_type == '32' and int(self.amount_residual) < 250000:
                url = 'https://pymesecf.com/api/ECF/EnvioResumen'

                params = {
                    'Ambiente': 'testecf',
                    'ticket': 'false'
                }
            else:
                url = 'https://pymesecf.com/api/ECF/EnvioECF'

                params = {
                    'Ambiente': 'testecf'
                }

            body = {
                'ECFEncabezado':  ecf_encabezado,
                'DetallesItems': detalles_items
            }

        # Nota de credito de clientes
        if self.move_type == 'out_refund':
            if not self.reversed_entry_id:
                raise ValidationError(f"La nota de crédito {self.name} no tiene factura asociada")
            if not self.out_refund_modification_code:
                raise ValidationError("El campo 'Código de Modificación' es requerido")

            ecf_encabezado = {
                'IdDoc': self.get_id_doc(),
                'Emisor': self.get_emisor(),
                'Comprador': self.get_comprador()
            }

            detalles_items = {
                'Item': self.get_items()
            }

            informacion_referencia = {
                'ncfModificado': self.out_invoice_e_ncf,
                'fechaNCFModificado': self.invoice_date.strftime('%d-%m-%Y'),
                'codigoModificacion': self.out_refund_modification_code,
                'razonModificacion': self.ref.split(', ')[1]
            }

            url = 'https://pymesecf.com/api/ECF/EnvioECF'

            params = {
                'Ambiente': 'testecf'
            }

            body = {
                'ECFEncabezado': ecf_encabezado,
                'DetallesItems': detalles_items,
                'informacionReferencia': informacion_referencia
            }

        # Facturas de proveedores
        if self.move_type == 'in_invoice':
            # Tiene gasto
            if self.expense_sheet_id:
                if not self.expense_ecf_type:
                    raise ValidationError("El campo 'Tipo de ECF' es requerido")
                if self.expense_ecf_type == '47' and not self.expense_retention_perception_indicator:
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
                    'Ambiente': 'testecf'
                }
    
                body = {
                    'ECFEncabezado': ecf_encabezado,
                    'DetallesItems': detalles_items
                }

            purchase_order = self.env['purchase.order'].search([('invoice_ids', 'in', [self.id])])
            # Tiene Orden de Compra
            if purchase_order:
                if not self.purchase_order_ecf_type:
                    raise ValidationError("El campo 'Tipo de ECF' es requerido")
                if self.purchase_order_ecf_type == '41' and not self.purchase_order_retention_perception_indicator:
                    raise ValidationError("El campo 'Indicador Agente Retención Percepción' es requerido")
                if self.purchase_order_ecf_type == '41' and not self.purchase_order_payment_type:
                    raise ValidationError("El campo 'Tipo de Pago' es requerido")
                if self.purchase_order_e_ncf:
                    return
                ecf_encabezado = {
                    'IdDoc': self.get_id_doc(),
                    'Emisor': self.get_emisor(),
                    'Comprador': self.get_comprador()
                }
    
                detalles_items = {
                    'Item': self.get_items()
                }
    
                url = 'https://pymesecf.com/api/ECF/EnvioECF'
    
                params = {
                    'Ambiente': 'testecf'
                }
    
                body = {
                    'ECFEncabezado': ecf_encabezado,
                    'DetallesItems': detalles_items
                }
        
        
        response = requests.post(url, headers=headers, params=params, json=body)
        try:
            response_data = response.json()
        except ValueError:
            _logger.error(f"No se pudo decodificar JSON. Respuesta recibida: {response.text}")
            raise ValidationError("La respuesta de la DGII no es un JSON válido. Verifica la estructura del envío o intenta más tarde.")

        if response.status_code == 200:
            if 'ncf' in response_data and 'fechaYHoraFirmaDigital' in response_data and 'codigoDeSeguridad' in response_data and 'qrCode' in response_data:
                if self.move_type == 'out_invoice':
                    date_format = '%d-%m-%Y %H:%M:%S'
                    digital_signature_date = datetime.strptime(response_data['fechaYHoraFirmaDigital'], date_format)
                    self.out_invoice_e_ncf = response_data['ncf']
                    self.out_invoice_digital_signature_date = digital_signature_date
                    self.out_invoice_security_code = response_data['codigoDeSeguridad']
                    self.out_invoice_fiscal_qr = response_data['qrCode']
                if self.move_type == 'out_refund':
                    if not self.reversed_entry_id:
                        raise ValidationError(f"La nota de crédito {self.name} no tiene factura asociada")
                    date_format = '%d-%m-%Y %H:%M:%S'
                    digital_signature_date = datetime.strptime(response_data['fechaYHoraFirmaDigital'], date_format)
                    self.out_refund_e_ncf = response_data['ncf']
                    self.out_refund_digital_signature_date = digital_signature_date
                    self.out_refund_security_code = response_data['codigoDeSeguridad']
                    self.out_refund_qr = response_data['qrCode']
                if self.move_type == 'in_invoice':
                    if self.expense_sheet_id:
                        date_format = '%d-%m-%Y %H:%M:%S'
                        digital_signature_date = datetime.strptime(response_data['fechaYHoraFirmaDigital'], date_format)
                        self.expense_e_ncf = response_data['ncf']
                        self.expense_digital_signature_date = digital_signature_date
                        self.expense_security_code = response_data['codigoDeSeguridad']
                        self.expense_fiscal_qr = response_data['qrCode']
                    if purchase_order:
                        date_format = '%d-%m-%Y %H:%M:%S'
                        digital_signature_date = datetime.strptime(response_data['fechaYHoraFirmaDigital'], date_format)
                        self.purchase_order_e_ncf = response_data['ncf']
                        self.purchase_order_digital_signature_date = digital_signature_date
                        self.purchase_order_security_code = response_data['codigoDeSeguridad']
                        self.purchase_order_fiscal_qr = response_data['qrCode']
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
        id_doc = {}
        if self.move_type == 'out_invoice':
            id_doc = {
                'TipoeCF': self.out_invoice_ecf_type,
                'IndicadorMontoGravado': '0',
                'TipoIngresos': self.out_invoice_income_type,
                'TipoPago': self.out_invoice_payment_type
            }

        if self.move_type == 'out_refund':
            if not self.reversed_entry_id:
                raise ValidationError(f"La nota de crédito {self.name} no tiene factura asociada")

            days_difference = (date.today() - self.reversed_entry_id.invoice_date).days
            indicador_nota_credito = '0' if days_difference <= 30 else '1'
            id_doc = {
                'TipoeCF': '34',
                'indicadorNotaCredito': indicador_nota_credito,
                'IndicadorMontoGravado': '0',
                'TipoIngresos': self.out_invoice_income_type,
                'TipoPago': self.out_invoice_payment_type
            }

        if self.move_type == 'in_invoice':
            if self.expense_sheet_id:
                id_doc = {
                    'TipoeCF': self.expense_ecf_type
                }

            purchase_order = self.env['purchase.order'].search([('invoice_ids', 'in', [self.id])])
            if purchase_order:
                fecha_limite_pago = (fields.Date.context_today(self) + timedelta(days=15)).strftime('%d-%m-%Y')
                id_doc = {
                    'TipoeCF': self.purchase_order_ecf_type,
                    'IndicadorMontoGravado': '0',
                    'TipoPago': self.purchase_order_payment_type,
                    'FechaLimitePago': fecha_limite_pago
                }

        return id_doc

    def get_emisor(self):
        company = self.company_id
        vat = company.vat
        company_name = company.name
        
        if vat:
            _logger.info(f"[EMISOR] Empresa: {company_name} | RNC: {vat}")
        else:
            _logger.warning(f"[EMISOR] La empresa '{company_name}' no tiene RNC (vat) configurado.")
        
        emisor = {
            'RNCEmisor': str(vat) if vat else ''
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
        products = self.invoice_line_ids
        purchase_order = self.env['purchase.order'].search([('invoice_ids', 'in', [self.id])])
        line_number = 1
        for line in products:
            if self.move_type == 'out_invoice' or self.move_type == 'out_refund':
                if len(line.tax_ids) > 0:
                    tax_name = line.tax_ids.name
                    if tax_name == '18% ITBIS':
                        invoice_indicator = '1'
                    elif tax_name == '16% ITBIS':
                        invoice_indicator = '2'
                    elif tax_name == '0% ITBIS':
                        invoice_indicator = '3'
                    elif tax_name == 'ITBIS Exempt':
                        invoice_indicator = '4'
                    else:
                        raise ValidationError(f"El impuesto '{tax_name}' no está permitido.")
                else:
                    raise ValidationError(f"No tiene impuesto.")
                item.append({
                    'NumeroLinea': str(line_number),
                    'IndicadorFacturacion': invoice_indicator,
                    'NombreItem': line.product_id.name,
                    'IndicadorBienoServicio': '2' if line.product_id.type == 'service' else '1',
                    'CantidadItem': str(int(line.quantity)),
                    'UnidadMedida': line.product_id.unit_of_measure,
                    'PrecioUnitarioItem': str(line.price_unit),
                    'MontoItem': str(round(line.price_unit * line.quantity, 2))
                })

            if self.move_type == 'in_invoice':
                if self.expense_sheet_id:
                    if self.expense_ecf_type == '43':
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

                    if self.expense_ecf_type == '47':
                        item.append({
                            'NumeroLinea': str(line_number),
                            'IndicadorFacturacion': '4',
                            "retencion": {
                                "indicadorAgenteRetencionoPercepcion": self.expense_retention_perception_indicator,
                                "montoISRRetenido": str(round(int(line.amount_residual) * 0.27, 2))
                            },
                            'NombreItem': line.product_id.name,
                            'IndicadorBienoServicio': '2' if line.product_id.type == 'service' else '1',
                            'CantidadItem': str(int(line.quantity)),
                            'UnidadMedida': line.product_id.unit_of_measure,
                            'PrecioUnitarioItem': str(line.price_unit),
                            'MontoItem': str(round(line.price_unit * line.quantity, 2))
                        })

                if purchase_order:
                    if len(line.tax_ids) > 0:
                        tax_name = line.tax_ids.name
                        if tax_name == '18% ITBIS':
                            invoice_indicator = '1'
                            monto_itbis_retenido = str(round(line.price_subtotal * 0.18, 2))
                        elif tax_name == '16% ITBIS':
                            invoice_indicator = '2'
                            monto_itbis_retenido = str(round(line.price_subtotal * 0.16, 2))
                        elif tax_name == '0% ITBIS':
                            invoice_indicator = '3'
                            monto_itbis_retenido = '0'
                        elif tax_name == 'ITBIS Exempt':
                            invoice_indicator = '4'
                            monto_itbis_retenido = '0'
                        else:
                            raise ValidationError(f"El impuesto '{tax_name}' no está permitido.")
                    else:
                        raise ValidationError(f"No tiene impuesto.")
                    item.append({
                        'NumeroLinea': str(line_number),
                        'IndicadorFacturacion': invoice_indicator,
                        "retencion": {
                            "indicadorAgenteRetencionoPercepcion": self.purchase_order_retention_perception_indicator,
                            "montoISRRetenido": str(round(line.price_subtotal * 0.27, 2)),
                            "MontoITBISRetenido": monto_itbis_retenido
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
