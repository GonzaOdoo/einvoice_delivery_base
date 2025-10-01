# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit="product.template"

    
    l10n_xma_is_control_cofepris = fields.Boolean(
        string='Control cofepris',
    )
    
    l10n_xma_sector_cofepris_id = fields.Many2one(
        'l10n.xma.sector.cofepris',
        string="Sector Cofrepis"
    )

    l10n_xma_tipo_embalaje_id = fields.Many2one(
        'l10n.xma.tipo.embalaje',
        string="Tipo de embalaje"
    )    
    descripcion_embalaje = fields.Char(
        string='Descripción embalaje',        
        related='l10n_xma_tipo_embalaje_id.name'
        
    )

    l10n_xma_tipo_materia = fields.Many2one("l10n.xma.tipo.materia", string="Tipo Materia")