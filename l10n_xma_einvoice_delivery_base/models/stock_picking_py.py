# -*- coding: utf-8 -*-
import logging
import base64
from odoo import fields, models, _, api
from odoo.exceptions import UserError
from xml.etree import ElementTree as ET
from io import BytesIO
from datetime import datetime, timedelta
import qrcode
_logger = logging.getLogger(__name__)
import time
from MqttLibPy.client import MqttClient
from MqttLibPy.serializer import Serializer
from xml.dom import minidom
import qrcode

class StockPickingPY(models.Model):
    _inherit = "stock.picking"

    l10n_xma_document_type_id = fields.Many2one(
        'l10n_latam.document.type', string="Tipo de Documento"
    )

    l10n_xma_date_signed = fields.Datetime(
        string='Fecha de emisión',
    )

    l10n_xma_documento = fields.Integer(
        string='Número de documento',
        copy=False,
        readonly=True
    )

    l10n_xma_edelivery_invoice = fields.Boolean(
        string='Es documento de traslado',
    )

    l10n_xma_issuance_type_id = fields.Many2one(
        'l10n_xma.issuance_type',
        string='Use Document'
    )

    l10n_xma_motive_id = fields.Many2one(
        'l10n_xma.use.document',
        string="Motivo de Emision",
        domain="['|', ['l10n_xma_transaction_type', '=', 'remision_note'], ['l10n_xma_transaction_type', '=', ''] ]"
    )
    
    sequence_number_assigned = fields.Boolean(
        string='Número de documento asignado',
        copy=False,
        readonly=True,
        default=False,
    )

    l10n_xma_cost_responsible_id = fields.Many2one(
        "l10n_xma.cost.responsible", 
        string="Responsable"
    )

    l10n_xma_modality_transaction_id = fields.Many2one(
        'l10n_xma.modality.transport', string="Modalidad de transporte"
    )

    l10n_xma_uuid_invoice = fields.Char(string="Folio", copy=False)
    
    l10n_xma_sifen_response = fields.Selection(
        [('1', ' '),
            ('2', 'Firmado'),
            ('3', 'Rechazado'),
            ('5', 'Autorizado'),
            ('6', 'Rechazado por Sifen'),
            ('7', 'Aprobado con Observaciones'),
            ('8', 'Cancelado'),
            ('9', 'Inutilizado'),
        ],default="1", string="Estado de Factura", readonly=True,
    )

    l10n_xma_xml_ar = fields.Binary(
        string = 'Invoice Xml', copy = False, readonly = False,
        help = 'The xml content encoded in base64.')
    
    l10n_xma_xml_name = fields.Char(
        string = 'Xml name',
        copy = False,
        readonly = True)
    
    l10n_xma_transport_type = fields.Selection(
        [('1', 'Propio'), ('2', 'Tercero')],
        string="Tipo de transporte",
        default='1',
    )
    l10n_xma_transport_type_id = fields.Many2one(
        'l10n_xma.transport.type',
        string="Tipo de transporte",
        help="Tipo de transporte utilizado para el traslado de mercaderia",
        domain=lambda self: self._get_domain_transport(),)
    
    def _get_domain_transport(self):
        country_id = self.env.company.country_id.id
        domain = ['|', ('country_id', '=', country_id), ('country_id', '=', False)]
        print(domain)
        return domain

    
    country_id = fields.Many2one('res.country',
        string='País',
        compute='get_country_id_from_company',
    )

    l10n_xma_flight_number = fields.Char(string="Número de vuelo")

    l10n_xma_use_document = fields.Boolean(string="Requiere Documento")

    l10n_xma_description_emision = fields.Char(string="Descripción de la Emisión",)

    l10n_xma_motive_id_code = fields.Char(related="l10n_xma_motive_id.code", string="Código de Motivo de Emisión", readonly=True)

    @api.model
    def get_country_id_from_company(self):
        for rec in self:
            rec.country_id = self.env.company.country_id.id
    
    ##------------------------------------------#
    def button_validate(self):
        country = self.company_id.partner_id.country_id.code.lower()
        if self.l10n_xma_use_document:
            if country == 'py':
                if not self.sequence_number_assigned and self.picking_type_id.code == 'outgoing':
                    if not self.l10n_xma_document_type_id or self.l10n_xma_document_type_id.code != '7':
                        raise UserError(_('Debe seleccionar un tipo de documento'))
                    else:
                        self.l10n_xma_documento = self.l10n_xma_document_type_id.l10n_xma_sequence_start
                        self.l10n_xma_document_type_id.l10n_xma_sequence_start += 1
        return super().button_validate()
    
    def consult_invoice_status(self):
        company = self.get_company()
        uuid = company.company_name
        rfc = self.company_id.partner_id.vat
        country = self.company_id.partner_id.country_id.code.lower()
        xml_json = {
            "from":  uuid,
            "id": self.id,
            "rfc": self.company_id.vat.split("-")[0],
            "data": {
                "NumRUC": rfc,
                "NumDocumentoInicial": int(self.l10n_xma_documento),
                "NumDocumentoFinal": int(self.l10n_xma_documento),
                "CodTipoDocumento": self.l10n_xma_document_type_id.code,
                "NumTimbrado": self.l10n_xma_document_type_id.l10n_xma_authorization_code,
                "CodPuntoExpedicion": self.l10n_xma_document_type_id.l10n_xma_dispatch_point,
                "AccImpresion": "N",
                "type": 'NRP',
                "id":self.id,
                "uuid_client":self.company_id.uuid_client,
                "rfc": self.company_id.vat.split("-")[0],
                "prod": 'NO',
                'integration_code': self.company_id.l10n_xma_integration_code,
                'access_key': self.company_id.l10n_xma_access_key
            } 
        }
        print(xml_json)
        _logger.info(f"uuid/{uuid}/rfc/{rfc}/country/{country}/consult")
        mqtt_client = MqttClient("api.xmarts.com", 1883, 
                                prefix=f"uuid/{uuid}/rfc/{rfc}/country/{country}/", 
                                encryption_key=company.key
        )
        mqtt_client.send_message_serialized(
            [xml_json],
            f"uuid/{uuid}/rfc/{rfc}/country/{country}/consult", 
            valid_json=True, 
            secure=True
        )
        self.refresh_account_move_xma()
    ##----------    Functions ------------------##
    def generate_qr_mx(self, company_vat, partner_rfc, total, uuid, fe):
        url = 'https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?re='+company_vat+'&rr='+partner_rfc+'&tt='+str(float(total))+'&id='+uuid+'&fe='+fe+''
        _logger.info("Generando QR")
        _logger.info(url)
        return self.generate_qr(url)

    def generate_qr(self, url):
        qr = qrcode.QRCode(version=1,error_correction=qrcode.constants.ERROR_CORRECT_L,box_size=20,border=4,)
        qr.add_data(url) #you can put here any attribute SKU in my case
        qr.make(fit=True)
        img = qr.make_image()
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()


    def get_company(self):
        company_id = self.env['res.company'].search([("company_name", "!=", "")], limit=1)
        if not company_id:
            company_id = self.env['res.company'].search([], limit=1)

        return company_id

    def l10n_xma_generate_delivery_guide(self):
        xml_json_py = self.generate_note_remission_py()
        # _logger.info(f"JSON: {xml_json_py}")
        xml_json = {"PY":xml_json_py}
        company = self.get_company()
        uuid = company.company_name
        rfc = self.company_id.partner_id.vat
        country = self.company_id.partner_id.country_id.code.lower()
        xml_json = {"from":uuid, "data":xml_json}
        mqtt_client = MqttClient("api.xmarts.com", 1883, prefix=f"uuid/{uuid}/rfc/{rfc}/country/{country}/", encryption_key=company.key)
        # print(xml_json)
        # xml_json = json.dumps(xml_json)
        mqtt_client.send_message_serialized(
            [xml_json],
            f"uuid/{uuid}/rfc/{rfc}/country/{country}/stamp", 
            valid_json=True, 
            secure=True
        )

        # self.l10n_xma_sif_status = 'sign'
        time.sleep(10)
        self.refresh_account_move_xma()
        
    
    def refresh_account_move_xma(self):
        return {
            'name': _("Inventario"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'domain': [('id', '=', self.id)],
            'target': 'current',
            'res_id': self.id,
        }

    def  generate_note_remission_py(self):
        ActividadesEconomicas = []
        for activities in self.company_id.l10n_xma_economic_activity_campany_id:
            # actividadesEco.append({
            #     "codigo": activities.code,
            #     "descripcion": activities.name,
            # })
            ActividadesEconomicas.append(
                {
                    "CodActividadEconomica": activities.code,
                    "DescActividadEconomica":activities.name,
                }
            )

        country_lines = self.partner_id.country_id
        DatosItem = []
        for lines in self.move_ids_without_package:
            DatosItem.append({
                "CodPaisOrigen": country_lines.l10n_xma_country_code, #"PRY",
                "DescInformacionesAdicionales":lines.product_id.name, #"LICENCIAS ODOO",
                "CodUnidadMedidaItem": int(lines.product_uom.l10n_xma_uomcode_id.code), # 77
                "DescUnidadMeditaItem": lines.product_uom.l10n_xma_uomcode_id.name,
                "DescDescripcionItem": lines.name, #"LICENCIAS ODOO",
                "DatosIvaItem": {},
                "DatosValorItem": {},
                "NumCantidadItem":  '%.4f' % (float(lines.product_uom_qty)), #1,
                "DescCodigoInternoItem": "1"
            })
        
        tipoRegimen = int(self.company_id.partner_id.l10n_xma_taxpayer_type_id.code)
        # time_invoice = self.get_mx_current_datetime()
        current_dt = datetime.now()
        date_time = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), current_dt)
        # self.l10n_xma_date_post = current_dt - timedelta(minutes=10)
        time_invoice = date_time
        str_time = time_invoice.strftime('%Y-%m-%dT%H:%M:%S')
        print(str_time)
        iddoc = {
            "NumTimbrado": int(self.l10n_xma_document_type_id.l10n_xma_authorization_code), #12559765,
            "CodTipoEmision": int(self.l10n_xma_issuance_type_id.code), #1
            "NumVersion": int(self.l10n_xma_document_type_id.journal_id.version_document), #150,
            "NumDocumento": int(str(self.l10n_xma_documento)), #26,
            "CodTipoDocumento":  int(self.l10n_xma_document_type_id.code), #1,
            "FechEmision": str_time, #"2023-07-31T02:08:00",
            "DescInformacionesDocumento": self.l10n_xma_document_type_id.name,
            # "CodMonedaOperacion": self.currency_id.name, #"PYG",
            "CodPuntoExpedicion": self.l10n_xma_document_type_id.l10n_xma_dispatch_point, # "001",
            "FechInicioTimbrado": self.company_id.start_date_post.strftime('%Y-%m-%d'), # "2023-07-31"
        }
        receptor = {}
        totales = {}
        receptor = {
            "CodNaturalezaReceptor": 1 if self.partner_id.l10n_xma_is_taxpayer else 2,  #1,
            "NumRUCReceptor": int(self.partner_id.vat), # 80055749,
            "CodTipoOperacionReceptor": int(self.partner_id.l10n_xma_customer_operation_type), #1,
            "CodTipoContribuyenteReceptor": 1, #1,
            "CodPaisReceptor": self.partner_id.country_id.l10n_xma_country_code, # "PRY",
            "CodDepartamentoReceptor": int(self.partner_id.state_id.code), ##11,
            "CodDistritoReceptor": int(self.partner_id.l10n_xma_municipality_id.code), #145,
            "CodCiudadReceptor": int(self.partner_id.l10n_xma_city_id.zipcode), #3432,
            "DescNombreReceptor": self.partner_id.name, #"FERMAQ S.R.L.",
            "DescDireccionReceptor": self.partner_id.street, # "KM. 15",
            "NumDigitoVerificadorRUCReceptor": int(self.partner_id.l10n_xma_control_digit), # 2,
            "NumNumeroCasaReceptor": self.partner_id.l10n_xma_external_number, # "1515"
        }
        destino= self.partner_id
        origen = self.company_id.partner_id
        datos_salida = {
            "DescDireccionSalida": origen.street,
            "NumCasaSalida": int(origen.l10n_xma_external_number),
            "DescComplementoDireccionSalida": origen.street2,
            "DescComplementoDireccion2Salida": origen.street2,
            "CodCiudadSalida": int(origen.l10n_xma_city_id.zipcode),
            "DescCiudadSalida": origen.l10n_xma_city_id.name,
            "CodDistritoSalida": int(origen.l10n_xma_municipality_id.code),
            "DescDistritoSalida": origen.l10n_xma_municipality_id.name,
            "CodDepartamentoSalida": int(origen.l10n_xma_city_id.state_id.code),
            "DescDepartamentoSalida": origen.l10n_xma_city_id.state_id.name,
            "NumTelefonoSalida": int(origen.phone.replace('+', '').replace(' ', '')),
        }
        datos_entrega = {
            "DescDireccionEntrega":destino.street,
            "NumCasaEntrega": int(destino.l10n_xma_external_number),
            "DescComplementoDireccionEntrega": destino.street2,
            "DescComplementoDireccion2Entrega": destino.street2,
            "CodCiudadEntrega": int(destino.l10n_xma_city_id.zipcode),
            'DescCiudadEntrega': destino.l10n_xma_city_id.name,
            "CodDistritoEntrega": int(destino.l10n_xma_municipality_id.code),
            'DescDistritoEntrega': destino.l10n_xma_municipality_id.name,
            "CodDepartamentoEntrega": int(destino.l10n_xma_city_id.state_id.code),
            "DescDepartamentoEntrega": destino.l10n_xma_city_id.state_id.name,
            "NumTelefonoEntrega":  int(destino.phone.replace('+', '').replace(' ', '')),
        }

        datos_transporte_transportista = {}
        count_pro = 0
        count_ope = 0
        for figure in self.l10n_xma_vehicle_id.l10n_xma_figures_ids:
            partner = figure.operador_id
            if figure.type == '01':
                
                datos_transporte_transportista.update({
                    "DescNombreChofer": partner.name,
                    "NumDocumentoIdentidadChofer": partner.license_number,#nuevo campo int(partner.vat),
                    "DescDireccionChofer": partner.street,
                })
                count_ope += 1
            elif figure.type == '02':
                datos_transporte_transportista.update({
                    "NumDigitoVerificadorRUCTransportista": partner.l10n_xma_control_digit,
                    "NumRUCTransportista": int(partner.vat),
                    "DescNombreTransportista": partner.name,
                    "CodNaturalezaTransportista": 1 if partner.l10n_xma_is_taxpayer else 2,
                    "CodNacionalidadTransportista": 'PRY',
                    "DescDomicilioTransportista": partner.street,
                })
                count_pro += 1

        if count_pro == 0:
            raise UserError(_("Debe seleccionar un transportista"))
        if count_ope == 0:
            raise UserError(_("Debe seleccionar un operador de transporte"))        
        
        print(datos_transporte_transportista)

        new_json = []
        json_data =  {
            # "DatosAdicionales": {
            #     "DescInformacionesAdicionales": "CORRESPONDIENTE A Julio 2023"
            # },
            "IdDocumento": iddoc,
            "Totales": totales,
            # Partner
            "Receptor": receptor,
            "DatosItem": DatosItem,
            # Company
            "Emisor": {
                "NumRUCEmisor": self.company_id.partner_id.vat , # "5448675",
                "NumRucDigitoVerificadorEmisor": int(self.company_id.partner_id.l10n_xma_control_digit),#0,
                "CodTipoContribuyenteEmisor": 1 if self.company_id.partner_id.company_type == 'person' else 2, #2,
                "CodTipoRegimenEmisor": tipoRegimen, #,8,
                "DescNombreEmisor": self.company_id.name, # "LIZBEL MARTINEZ SILVA",
                "DescNombreFantasiaEmisor": self.company_id.partner_id.name, # "LIZBEL MARTINEZ SILVA",
                "DescDirecionEmisor": self.company_id.partner_id.street, # "AMARRAS, COSTA DEL LAGO",
                "NumNumeroCasaEmisor": self.company_id.partner_id.l10n_xma_external_number,  #"0",
                "DescComplementoEmisor": self.company_id.partner_id.street, #"AMARRAS, COSTA DEL LAGO",
                "DescComplemento2Emisor": self.company_id.partner_id.street2, #"SUPERCARRETERA",
                "CodCiudadEmisor": int(self.company_id.partner_id.l10n_xma_city_id.zipcode),#3432,
                "CodDistritoEmisor": int(self.company_id.partner_id.l10n_xma_municipality_id.code), #145,
                "CodDepartamentoEmisor": int(self.company_id.partner_id.state_id.code), #11,
                "NumTelefonoEmisor": self.company_id.partner_id.phone or "", #"0973527155",
                "DescCorreoEmisor": self.company_id.partner_id.email or "", #"lizbelms@gmail.com",
                "DescNombreInternoEmisor": self.company_id.partner_id.name, #"LIZBEL MARTINEZ SILVA",
                "ActividadesEconomicas": ActividadesEconomicas,
            },
            "DatosEspecificosDocumento": {
                'DatosNotaRemision':{
                    'CodMotivoRemision': int(self.l10n_xma_motive_id.code),
                    'DescMotivoRemision': self.l10n_xma_motive_id.name,
                    'CodResponsable': 1,
                    'DescResponsable':'Emisor de la Factura Electrónica',
                    'NumKilometrosRecorridos': int(self.l10n_xma_distance_km),
                    'FechFuturaEmision': self.l10n_xma_date_signed.strftime('%Y-%m-%d'),
                },
            },
            'DatosTransporte':{
                'CodTipoTransporte': int(self.l10n_xma_transport_type_id.code),
                'CodModalidadTransporte': int(self.l10n_xma_modality_transaction_id.code),
                'CodResponsableFlete': int(self.l10n_xma_cost_responsible_id),
                'CodIncoterms': 'DAP',
                # 'DescManifiesto': '',
                'NumDespachoImportacion': '',
                'FechInicioTraslado': self.l10n_xma_goods_entry.date().strftime('%Y-%m-%d'), #'2024-08-20',
                'FechFinTraslado': self.l10n_xma_merchandise_release.date().strftime('%Y-%m-%d'), #'2024-08-22',
                'CodPaisDestino': 'PRY',
                'DatosTransporteSalida': datos_salida,
                'DatosTransporteEntrega':[datos_entrega],
                'DatosTransporteVehiculo':[{
                    "DescTipoVehiculo": self.l10n_xma_vehicle_id.vehicle_type_id.name,
                    "DescMarca": self.l10n_xma_vehicle_id.vehicle_model,
                    "CodTipoIdentificacionVehiculo": int(self.l10n_xma_vehicle_id.l10n_xma_type_vehicle), #int(self.l10n_xma_identification_type_vehicle),
                    "DescNumeroIdentificacionVehiculo": self.l10n_xma_vehicle_id.vehicle_licence,
                    "DescDatosAdicionalesVehiculo": self.l10n_xma_vehicle_id.name,
                    "DescNumeroMatriculaVehiculo": self.l10n_xma_vehicle_id.vehicle_licence,
                    "DescVuelo": self.l10n_xma_flight_number if int(self.l10n_xma_modality_transaction_id.code) == 3 else {},
                }],
                'DatosTransporteTransportista': datos_transporte_transportista,
                    # "CodNaturalezaTransportista": 1,
                    # "DescNombreTransportista": '3G Sociedad Anonima',
                    # "NumRUCTransportista": 80080311,
                    # "NumDigitoVerificadorRUCTransportista": 6,
                    # # "CodTipoDocumentoIdentidadTransportista": 1,
                    # # "NumDocumentoIdentidadTransportista": 1,
                    # "CodNacionalidadTransportista": 'PRY',
                    # "NumDocumentoIdentidadChofer": 4357744,
                    # "DescNombreChofer": 'Diego Benitez',
                    # "DescDomicilioTransportista": 'Ciudad del este',
                    # "DescDireccionChofer": 'Ciudad del Este',
                    # # "DescNombreAgente": '',
                    # # "NumRUCAgente": 1,
                    # # "NumDigitoVerificadorRUCAgente": 1,
                    # # "DescDireccionAgente": '',
            },
        }
        print(json_data)
        json_data = self.clean_empty_keys(json_data)
        new_json.append(json_data)

        json_complete = {
            "id":self.id,
            "uuid_client":self.company_id.uuid_client,
            "data": new_json,
            "rfc": self.company_id.vat,
            "prod": 'NO',
            "type": 'NRP',
            'integration_code': self.company_id.l10n_xma_integration_code,
            'access_key': self.company_id.l10n_xma_access_key
        }
        return json_complete

    def clean_empty_keys(self, data):
        if isinstance(data, dict):
            return {k: self.clean_empty_keys(v) for k, v in data.items() if v not in ({}, '')}
        elif isinstance(data, list):
            return [self.clean_empty_keys(item) for item in data if item not in ({}, '')]
        return data

    def calculate_qty_total(self):
        for rec in self:
            rec.l10n_xma_qty_total_products = 0
            for items in rec.move_ids_without_package:
                rec.l10n_xma_qty_total_products += 1
    def calculate_weight_total(self):
        for rec in self:
            rec.l10n_xma_weight_total_products = 0
            for items in rec.move_ids_without_package:
                rec.l10n_xma_weight_total_products += items.product_id.weight

    def get_mx_current_datetime(self):
        return fields.Datetime.context_timestamp(
            self.with_context(tz='America/Mexico_City'), self.l10n_xma_date_signed)
    
    def get_mx_current_datetime_ubications(self, date):
        return fields.Datetime.context_timestamp(
            self.with_context(tz='America/Mexico_City'), date)
    
    def get_data_origin_dest(self):
        destino= self.partner_id
        origen = self.company_id.partner_id
        datos = {
            'origen': {
                'direccion': origen.street,
                'numero_casa': origen.l10n_xma_external_number,
                'complemento_direccion': origen.street2,
                'complemento_direccion2': origen.street2,
                'ciudad_codigo': origen.l10n_xma_city_id.zipcode,
                'ciudad_descripcion': origen.l10n_xma_city_id.name,
                'distrito_codigo': origen.l10n_xma_municipality_id.code,
                'distrito_descripcion': origen.l10n_xma_municipality_id.name,
                'departamento_codigo': origen.l10n_xma_city_id.state_id.code,
                'departamento_descripcion': origen.l10n_xma_city_id.state_id.name,
                'telefono': origen.phone.replace('+', '').replace(' ', ''),
            },
            'destino': {
                'direccion': destino.street,
                'numero_casa': destino.l10n_xma_external_number,
                'complemento_direccion': destino.street2,
                'complemento_direccion2': destino.street2,
                'ciudad_codigo': destino.l10n_xma_city_id.zipcode,
                'ciudad_descripcion': destino.l10n_xma_city_id.name,
                'distrito_codigo': destino.l10n_xma_municipality_id.code,
                'distrito_descripcion': destino.l10n_xma_municipality_id.name,
                'departamento_codigo': destino.l10n_xma_city_id.state_id.code,
                'departamento_descripcion': destino.l10n_xma_city_id.state_id.name,
                'telefono': destino.phone.replace('+', '').replace(' ', ''),
            }
        }
        return datos

    def get_data_trasportist(self):
        datos_transporte_transportista = {}
        count_pro = 0
        count_ope = 0
        for figure in self.l10n_xma_vehicle_id.l10n_xma_figures_ids:
            partner = figure.operador_id
            type_con = 1 if partner.l10n_xma_is_taxpayer else 2
            if figure.type == '01':
                
                datos_transporte_transportista.update({
                    "nombre_cho": partner.name,
                    "num_cho": partner.l10n_xma_identification_number,#nuevo campo int(partner.vat),
                    "dir_cho": partner.street,
                })
            elif figure.type == '02':
                datos_transporte_transportista.update({
                    "ruc_tr": int(partner.vat),
                    "nombre_tr": partner.name,
                    "nat_tr": 'Contribuyente' if type_con == 1 else 'No Contribuyente',
                })
        print(datos_transporte_transportista)
        return datos_transporte_transportista

    @api.model
    def edi_get_xml_etree_py(self, py_xml=None):
        for rec in self:
            if rec.l10n_xma_xml_ar:
                stream = BytesIO(base64.b64decode(rec.l10n_xma_xml_ar))
                doc = minidom.parse(stream)
                Test = doc.getElementsByTagName("dCarQR")[0]
                print(Test.firstChild.data)
                return Test.firstChild.data

    def generate_cdc(self):
        newNumCDC = ''
        for i in range(0, len(self.l10n_xma_uuid_invoice), 4):
            newNumCDC += self.l10n_xma_uuid_invoice[i:i + 4] + " "

        return newNumCDC

    def generate_qr(self, url):
        qr = qrcode.QRCode(version=1,error_correction=qrcode.constants.ERROR_CORRECT_L,box_size=20,border=4,)
        qr.add_data(url) #you can put here any attribute SKU in my case
        qr.make(fit=True)
        img = qr.make_image()
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()
    ##------------------------------------------##