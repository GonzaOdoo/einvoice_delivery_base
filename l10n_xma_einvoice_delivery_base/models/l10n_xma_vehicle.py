# -*- coding: utf-8 -*-
from odoo import fields, models,api


class L10nXmaVehicle(models.Model):
    _name = "l10n.xma.vehicle"
    _description = "Tipo de vehículo."
    _order = 'id'

    vehicle_licence = fields.Char(
        string="No. de placa"
    )

    vehicle_model = fields.Char(
        string="Modelo"
    )

    name = fields.Char(
        string="Nombre"
    )

    insure_company = fields.Char(
        string="Compañía aseguradora",
    )

    insure_policy = fields.Char(
        string="No. de póliza"

    )

    environment_insurer_company = fields.Char(
        string="Compañia aseguradora medio ambiente",
    )

    environment_insurer_policy = fields.Char(
        string="No. póliza aseguradora medio ambiente",
    )
    
    permission_type_id = fields.Many2one(
        'l10n.xma.permission.type',
        string='Tipo de permiso.',
    )

    vehicle_type_id = fields.Many2one(
        'l10n.xma.vehicle.type',
        string='Tipo de vehículo',
        domain=lambda self: self._get_domain_vehicle(),
    )
    country_id = fields.Many2one('res.country',
        string='País',
        compute='get_country_id_from_company',
    )

    @api.model
    def get_country_id_from_company(self):
        for rec in self:
            rec.country_id = self.env.company.country_id.id
    def _get_domain_vehicle(self):
        country_id = self.env.company.country_id.id
        domain = ['|', ('country_id', '=', country_id), ('country_id', '=', False)]
        print(domain)
        return domain


    l10n_xma_figures_ids = fields.One2many('l10n.xma.figure', 'vehicle_id')

    l10n_xma_trailers_ids = fields.One2many('l10n.xma.trailer', 'vehicle_id')

    
    total_vehice_weigth = fields.Char(
        string='Peso bruto vehicular',
    )

    num_permiso_sct = fields.Char(
        string='Número de permiso SCT',
    )
    
    goods_insurer = fields.Char(
        string='Compañía aseguradora de carga',
    )
    goods_insurer_policy = fields.Char(
        string='Poliza compañía aseguradora de carga',
    )
    options_type = [
                    ('1', 'Número de identificación del vehículo'),
                    ('2', 'Número de matrícula del vehículo')
                ]
    l10n_xma_type_vehicle = fields.Selection(
        options_type, string="Tipo de Identificacion del vehiculo",
        default='1',
    )

