# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class ResPartner(models.Model):
    _inherit = "res.partner"

    
    is_operator = fields.Boolean(
        string='Es operador',
    )
    
    license_number = fields.Char(
        string='No. de licencia',
    )
    l10n_xma_colony_code = fields.Char(
        string='Colonia',
    )
