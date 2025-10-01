# -*- coding: utf-8 -*-
from odoo import fields, models


class L10nXmaFigure(models.Model):
    _name = "l10n.xma.figure"
    _description = "Figuras."
    _order = 'id'
    _rec_names_search = ['name']

    operador_id = fields.Many2one(
        'res.partner',
        string="Operador"
    )

    name = fields.Char(
        string="Nombre",
        related="operador_id.name",
        store=True,
    )

    vehicle_id = fields.Many2one(
        'l10n.xma.vehicle',
        string="Vehículo",
    )

    options = [
        ('01', 'Operador'),
        ('02', 'Propietario'),
        ('03', 'Arrendador'),
        ('04', 'Notificado')
    ]

    type = fields.Selection(
        options,
        string="Tipo"
    )
