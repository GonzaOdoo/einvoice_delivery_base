from odoo import fields, models


class L10nXmaRegimenAduanero(models.Model):
    _name = "l10n.xma.regimen.aduanero"
    _description = "Regimen Aduanero"
    _order = 'id'
    _rec_names_search = ['clave','name','impoexpo']

    clave = fields.Char(
        string='Clave',
    )
    name = fields.Char(
        string='Descripción',
    )
    
    impoexpo = fields.Char(
        string='ImpoExpo',
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
        return [(regimen.id, "%s %s" % (regimen.clave, regimen.name or '')) for regimen in self]
    