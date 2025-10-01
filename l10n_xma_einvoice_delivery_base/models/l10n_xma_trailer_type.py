# -*- coding: utf-8 -*-
from odoo import fields, models


class L10nXmaTrailerType(models.Model):
    _name = "l10n.xma.trailer.type"
    _description = "Tipo de caja."
    _order = 'id'
    _rec_names_search = ['code','name']

    code = fields.Char(
        string='Código',
    )
    name = fields.Char(
        string='Nombre',
    )    
    valid_from = fields.Date(
        string='Valido desde',
    )
    valid_to = fields.Date(
        string='Valido hasta',
    )
    country_id = fields.Many2one(
        'res.country',
        string='Pais',
    )

    def name_get(self):
        # OVERRIDE
        return [(tipo.id, "%s %s" % (tipo.code, tipo.name or '')) for tipo in self]