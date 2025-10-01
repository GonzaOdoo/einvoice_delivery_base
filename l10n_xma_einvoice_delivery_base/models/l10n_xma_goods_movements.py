from odoo import fields, models


class L10nXmaGoodsMovements(models.Model):
    _name = "l10n.xma.goods.movements"
    _description = "Movimiento de mercancías."
    _order = 'id'
    _rec_names_search = ['name']



    move_id = fields.Many2one(
        'account.move',
        string="Carta porte",
    )
    options = [
        ('Origen', 'Origen'),
        ('Destino', 'Destino'),
    ]

    transfer_type = fields.Selection(
        options,
        string="Tipo de movimiento"
    )    
    date_transfer = fields.Datetime(
        string='Fecha y hora Salida/Entrada',
    )    
    vat = fields.Char(
        string='RFC Remimente / Receptor',
    )    
    name = fields.Char(
        string='Nombre Remitente / Receptor',
    )
    country_id = fields.Many2one(
        'res.country',
        string='Pais',
    )
    state_id = fields.Many2one(
        'res.country.state',
        string='Estado',
    )
    municipality_id = fields.Many2one(
        'l10n_xma.municipality',
        string='Municipio',
    )
    locality_id = fields.Many2one(
        'res.city',
        string='Localidad',
    )
    
    colony = fields.Char(
        string='Colonia',
    )
    colony_code = fields.Char(
        string='Código de la colonia',
    )
    street = fields.Char(
        string='Calle',
    )
    cp = fields.Char(
        string='Código postal',
    )
    external_number = fields.Char(
        string='Número exterior',
    )
    internal_number = fields.Char(
        string='Número interno',
    )
    reference = fields.Char(
        string='Referencia',
    )