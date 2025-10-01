# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductProduct(models.Model):
    _inherit="product.product"

    l10n_xma_is_control_cofepris = fields.Boolean(
        string='Control cofepris',
        related="product_tmpl_id.l10n_xma_is_control_cofepris",        
        readonly=False 
        
    )
    
    l10n_xma_sector_cofepris_id = fields.Many2one(
        'l10n.xma.sector.cofepris',
        string="Sector Cofrepis",
        related="product_tmpl_id.l10n_xma_sector_cofepris_id",
        readonly=False
    )

    l10n_xma_tipo_embalaje_id = fields.Many2one(
        'l10n.xma.tipo.embalaje',
        string="Tipo de embalaje",
        related="product_tmpl_id.l10n_xma_tipo_embalaje_id",
        readonly=False
    )    
    descripcion_embalaje = fields.Char(
        string='Descripción embalaje',        
        related='l10n_xma_tipo_embalaje_id.name',
        readonly=False
        
    )

    l10n_xma_tipo_materia = fields.Many2one("l10n.xma.tipo.materia", string="Tipo Materia", related="product_tmpl_id.l10n_xma_tipo_materia")