# -*- coding: utf-8 -*-
from odoo import fields, models, _

class XmaCostResponsible(models.Model):
    _name = "l10n_xma.cost.responsible"
    
    name = fields.Char()
    code = fields.Char()
    country_id = fields.Many2one("res.country")