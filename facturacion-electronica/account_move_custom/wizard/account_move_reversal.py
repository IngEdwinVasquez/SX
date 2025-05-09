# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccountMoveReversalCustom(models.TransientModel):
    _inherit = 'account.move.reversal'

    @api.constrains('reason')
    def _check_reason_length(self):
        for record in self:
            if len(record.reason) > 90:
                raise ValidationError('La razón debe ser menor o igual a 90 caracteres')
