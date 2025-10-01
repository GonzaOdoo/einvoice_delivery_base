# -*- coding: utf-8 -*-
from odoo import fields, models


class L10nXmaTrailer(models.Model):
    _name = "l10n.xma.trailer"
    _description = "Remolques."
    _order = 'id'
    _rec_names_search = ['name']

    trailer_type_id = fields.Many2one(
        'l10n.xma.trailer.type',
        string='Tipo',
    )
    vehicle_id = fields.Many2one(
        'l10n.xma.vehicle',
        string='Vehículo',
    )
    name = fields.Char(
        string='Nombre',
    )