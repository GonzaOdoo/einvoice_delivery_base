from odoo import fields, models


class L10nXmaCveTransporte(models.Model):
    _name = "l10n.xma.cve.transporte"
    _description = "Claves transporte"
    _order = 'id'
    _rec_names_search = ['clave','name']

    clave = fields.Char(
        string='Clave',
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
        return [(tipo.id, "%s %s" % (tipo.clave, tipo.name or '')) for tipo in self]