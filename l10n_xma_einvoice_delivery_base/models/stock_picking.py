# -*- coding: utf-8 -*-
import xmlrpc.client
import logging
from lxml.objectify import fromstring
import base64
from datetime import datetime, timedelta
import requests
import json
from odoo.tools import float_round
from odoo.tools.float_utils import float_repr
from odoo import fields, models, api, _, tools
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_TIME_FORMAT
from pytz import timezone
from lxml import etree, objectify
from xml.etree import ElementTree as ET
from io import BytesIO, StringIO
import qrcode
_logger = logging.getLogger(__name__)

url_xmarts = 'http://159.203.170.13:8069'  # rec.company_id.edi_url_bd
db_xmarts = 'ssser'  # rec.company_id.edi_name_bd
# url_xmarts = 'http://localhost:8014'  # rec.company_id.edi_url_bd
# db_xmarts = 'cfdi4_s2'  # rec.company_id.edi_name_bd
import time
import uuid
from MqttLibPy.client import MqttClient
from MqttLibPy.serializer import Serializer

class StockPicking(models.Model):
    _inherit = "stock.picking"

    

    
    options = [
        ('00', 'Sin Uso de carreteras Federales'),
        ('01', 'Autotransporte Federal'),
    ]

    l10n_xma_trasport_type = fields.Selection(
        options,
        string="Tipo de transporte"
    )
    l10n_xma_vehicle_id = fields.Many2one(
        'l10n.xma.vehicle',
        string="Vehículo",
    )
	
    l10n_xma_distance_km = fields.Integer(
        string='Distancia en kilometros',
    )
    
    l10n_xma_date_signed = fields.Datetime(
        string='Fecha de emisión',
        default=fields.Datetime.now,
    )
    
    
    l10n_xma_electronic_number = fields.Char(
        string='Número electónico',
    )

    l10n_xma_qty_total_products = fields.Float(
        string="Cantidad total",
        compute="calculate_qty_total"
    )

    l10n_xma_weight_total_products = fields.Float(
        string="peso total",
        compute="calculate_weight_total"
    )

    edi_cfdi = fields.Binary(
        string="Archivo CFDI",
        copy=False,
        readonly=True
    )
    edi_cfdi_name = fields.Char(
        string="Nombre del archivo CFDI",
        copy=False,
        tracking=True,
        readonly=True
    )

    
    l10n_sing = fields.Boolean(copy=False)
    
    edi_cadena_original = fields.Text(
        string="Cadena Original",
        copy=False,
        readonly=True
    )

    l10n_xma_edelivery_invoice = fields.Boolean(
        string='Es documento de traslado',
    )

    ##------------ Carta porte 3.0 -------------#

    
    options_transp = [
        ('00', 'No'),
        ('01', 'Sí'),
    ]

    l10n_xma_transp_internac = fields.Selection(
        options_transp,
        string="TranspInternac"
    )

    options_istmo = [
        ('si', 'Sí'),
        ('no', 'No'),
    ]

    l10n_xma_is_registro_itsmo = fields.Selection(
        options_istmo,        
        default='no',        
        string="Usa Zonas del ISTMO"
    )

    
    l10n_xma_polo_origen_id = fields.Many2one(
        string='Polo Origen',
        comodel_name='l10n.xma.registro.istmo',
    )
    l10n_xma_polo_destino_id = fields.Many2one(
        string='Polo Destino',
        comodel_name='l10n.xma.registro.istmo',
    )

    # l10n_xma_unidad_peso_id = fields.Many2one(
    #     string='UnidadPeso',
    #     comodel_name='l10n.xma.unidad.peso',
    # )
    
    options_trans = [
        ('si', 'Sí'),
        ('no', 'No'),
    ]

    l10n_xma_is_international_transport = fields.Selection(
        options_trans,        
        default='no',        
        string="Es transporte internacional ?"
    )
    
    options_entrasali = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    ]

    l10n_xma_entradasalida = fields.Selection(
        options_entrasali,
        string="Entrada/Salida Mercancía"
    )


    
    l10n_xma_regimen_aduanero_id_id = fields.Many2many(
        string='Regimen Aduanero',
        comodel_name='l10n.xma.regimen.aduanero',
    )

    
    l10n_xma_cve_transporte_id = fields.Many2one(
        string='Clave de transporte',
        comodel_name='l10n.xma.cve.transporte',
    )

    options_returned = [
        ('si', 'Sí'),
        ('no', 'No'),
    ]
    
    l10n_xma_is_returned_goods = fields.Selection(
        options_returned,
        string="Es devolución de mercancía?"
    )

    l10n_xma_idccp = fields.Char(
        string='ID Complemento Carta Porte',
        help="Este valor se genera de manerá automática al momento de timbrar la factura es similar al" 
             "funciomaniento del timbrado solo que al valor obtenido se le antepone el valor CCC.",
    )

    
    l10n_xma_goods_entry = fields.Datetime(
        string='Fecha y hora de entrada',
        default=fields.Datetime.now,
    )

    l10n_xma_merchandise_release = fields.Datetime(
        string='Fecha y hora de salida',
    )
    
    

    ##------------------------------------------#



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

    def l10n_xma_consulted_xml_view(self):
        self.l10n_xma_consulted_xml(self.l10n_xma_electronic_number, self.id, self.company_id.vat, self)

    def l10n_xma_consulted_xml(self, folio, picking_id, rfc, factura):
        xml_json = {
            'folio': folio,
            'id_factura': picking_id,
            'rfc': rfc
        }
        company = factura.get_company()
        uuid = company.company_name
        rfc = factura.company_id.partner_id.vat
        country = factura.company_id.partner_id.country_id.code.lower()
        _logger.info(f"uuid/{uuid}/rfc/{rfc}/country/{country}/consult")
        xml_json = {"from":uuid, "data":xml_json}
        mqtt_client = MqttClient("api.xmarts.com", 1883, prefix=f"uuid/{uuid}/rfc/{rfc}/country/{country}/", encryption_key=company.key)
        # xml_json = json.dumps(xml_json)
        print(xml_json)
        mqtt_client.send_message_serialized(
            [xml_json],
            f"uuid/{uuid}/rfc/{rfc}/country/{country}/consult", 
            valid_json=True, 
            secure=True
        )

    def get_company(self):
        company_id = self.env['res.company'].search([("company_name", "!=", "")], limit=1)
        if not company_id:
            company_id = self.env['res.company'].search([], limit=1)

        return company_id

    def send_delivery_guide(self):
        for rec in self:
            xml_json = rec.get_edi_json()
            edelivery_json = {
                "id":rec.id,
                "uuid_client":rec.company_id.uuid_client,
                "data":xml_json,
                "rfc":rec.company_id.vat,
                "prod": 'NO' if rec.company_id.l10n_xma_test else 'SI',
                "type": 'D',
                "pac_invoice": 'solu_fa' if rec.company_id.l10n_xma_test else rec.company_id.l10n_xma_type_pac,
            }
            xml_json = {"MX_edelivery": edelivery_json}
            company = rec.get_company()
            uuid = company.company_name
            rfc = rec.company_id.partner_id.vat
            country = company.partner_id.country_id.code.lower()
            xml_json = {"from":uuid, "data":xml_json}
            mqtt_client = MqttClient("api.xmarts.com", 1883, prefix=f"uuid/{uuid}/rfc/{rfc}/country/{country}/", encryption_key=company.key)
            # xml_json = json.dumps(xml_json)
            print(xml_json, type(xml_json))
            mqtt_client.send_message_serialized(
                [xml_json],
                f"uuid/{uuid}/rfc/{rfc}/country/{country}/stamp", 
                valid_json=True, 
                secure=True
            )

            time.sleep(2)
            rec.refresh_account_move_xma()
            break
        
    
    def refresh_account_move_xma(self):
        time.sleep(1)
        return {
            'name': _("Inventario"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'domain': [('id', '=', self.id)],
            'target': 'current',
            'res_id': self.id,
        }

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

    def edi_sign_transfer_invoice(self):
        for rec in self:
            #time_invoice = fields.Date.context_today(self) #self.env['einvoice.edi.certificate'].sudo().get_mx_current_datetime()
            # time_invoice = self.get_mx_current_datetime()
            current_dt = datetime.now()
            date_time = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), current_dt)
            # self.l10n_xma_date_post = current_dt
            time_invoice = date_time
            Mercancia = []
            items = 0
            pbruto = 0
            # items += 1
            # pbruto += round(((l.quantity * l.product_id.weight) * l.product_uom_id.factor_inv),4)
            CantidadTransporta = []
            CantidadTransporta.append({

                'Cantidad': self.l10n_xma_qty_total_products,# totaltodos los productos  | hacer campo calculadoi
                'IDDestino': "DE" + str(self.location_dest_id.id).zfill(6), # DE + id del registro
                'IDOrigen':"OR" + str(self.location_id.id).zfill(6),  # OR + id del registro
            })
            total_weight = 0
            materialp = 0
            for items in rec.move_ids_without_package:
                total_weight += items.product_id.weight
                goods = self.env['l10n.xma.goods'].search([('stock_move_line_id','=', items.id)], limit=1)
                materialpeligroso = ''
                cvematerialpeligroso = ''
                embalaje = ''
                descripembalaje = ''
                if items.product_id.l10n_xma_is_hazaudous_material == 'si':
                    materialp += 1
                    materialpeligroso = 'Sí'
                    cvematerialpeligroso = items.product_id.l10n_xma_hazaudous_material_id.code
                    embalaje = items.product_id.l10n_xma_tipo_embalaje_id.clave
                    descripembalaje = items.product_id.descripcion_embalaje
                elif  items.product_id.l10n_xma_is_hazaudous_material ==  'noo':
                    materialpeligroso = 'No'
                    cvematerialpeligroso = {}
                    embalaje = {}
                    descripembalaje = {}
                else:
                    materialpeligroso = {}
                    cvematerialpeligroso = {}
                    embalaje = {}
                    descripembalaje = {}
                if goods:
                    Mercancia.append({
                        'BienesTransp': items.product_id.l10n_xma_productcode_id.code, #codesat
                        'Cantidad': '%.2f' % float(items.product_uom_qty), #qty
                        'Descripcion':items.description_picking.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;'), # name
                        'ClaveUnidad': items.product_uom.l10n_xma_uomcode_id.code, #codesat unidad de medida 
                        'PesoEnKg': '%.2f' % float(items.product_id.weight), # peso
                        'MaterialPeligroso': materialpeligroso, # 'Sí' if items.product_id.l10n_xma_is_hazaudous_material == 'si' else 'No',
                        'CveMaterialPeligroso': cvematerialpeligroso, # items.product_id.l10n_xma_hazaudous_material_id.code if items.product_id.l10n_xma_is_hazaudous_material == 'si' else {},
                        'Embalaje': embalaje, # items.product_id.l10n_xma_tipo_embalaje_id.clave if items.product_id.l10n_xma_is_hazaudous_material == 'si' else {},
                        'DescripEmbalaje': descripembalaje, # items.product_id.descripcion_embalaje if items.product_id.l10n_xma_is_hazaudous_material == 'si' else {},                   
                        'SectorCOFEPRIS': items.product_id.l10n_xma_sector_cofepris_id.clave if items.product_id.l10n_xma_sector_cofepris_id and items.product_id.l10n_xma_is_control_cofepris == True else {},
                        'NombreIngredienteActivo': goods.nombre_ingrediente_activo if goods.nombre_ingrediente_activo else {},
                        'NomQuimico': goods.nomquimico if goods.nomquimico else {},
                        'DenominacionGenericaProd': goods.dengenprod if goods.dengenprod else {},
                        'DenominacionDistintivaProd': goods.dendistprod if goods.dendistprod else {},
                        'Fabricante': goods.fabricante if goods.fabricante else {},
                        'FechaCaducidad': goods.fecha_caducidad.strftime('%Y-%m-%d') if goods.fecha_caducidad else {},
                        'LoteMedicamento': goods.lote_medicamento if goods.lote_medicamento else {},
                        'FormaFarmaceutica': goods.forma_farmaceutica_id.clave if goods.forma_farmaceutica_id.clave else {},
                        'CondicionesEspTransp': goods.condiciones_especiales_id.clave if goods.condiciones_especiales_id.clave else {},
                        'RegistroSanitarioFolioAutorizacion': goods.regsanfolauto if goods.regsanfolauto else {},
                        'PermisoImportacion': goods.permiso_importacion if goods.permiso_importacion else {},
                        'FolioImpoVUCEM': goods.folimpvucem if goods.folimpvucem else {},
                        'NumCAS': goods.numcas if goods.numcas else {},
                        'RazonSocialEmpImp': goods.razsocempimp if goods.razsocempimp else {},
                        'NumRegSanPlagCOFEPRIS': goods.num_regsanplag_cofepris if goods.num_regsanplag_cofepris else {},
                        'DatosFabricante': goods.datos_fabricante if goods.datos_fabricante else {},
                        'DatosFormulador': goods.datos_formulador if goods.datos_formulador else {},
                        'DatosMaquilador': goods.datos_maquilador if goods.datos_maquilador else {},
                        'UsoAutorizado': goods.uso_autorizado if goods.uso_autorizado else {},

                        'cartaporte31:CantidadTransporta': CantidadTransporta,
                    })
                else:
                    Mercancia.append({
                        'BienesTransp': items.product_id.l10n_xma_productcode_id.code, #codesat
                        'Cantidad': '%.2f' % float(items.product_uom_qty), #qty
                        'Descripcion':items.description_picking.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;'), # name
                        'ClaveUnidad': items.product_uom.l10n_xma_uomcode_id.code, #codesat unidad de medida 
                        'PesoEnKg': '%.2f' % float(items.product_id.weight), # peso
                        'cartaporte31:CantidadTransporta': CantidadTransporta,
                        'SectorCOFEPRIS': items.product_id.l10n_xma_sector_cofepris_id.clave if items.product_id.l10n_xma_sector_cofepris_id and items.product_id.l10n_xma_is_control_cofepris == True  else {},
                        'MaterialPeligroso': materialpeligroso,
                        'CveMaterialPeligroso': cvematerialpeligroso, # items.product_id.l10n_xma_hazaudous_material_id.code if items.product_id.l10n_xma_is_hazaudous_material == 'si' else {},
                        'Embalaje': embalaje, # items.product_id.l10n_xma_tipo_embalaje_id.clave if items.product_id.l10n_xma_is_hazaudous_material == 'si' else {},
                        'DescripEmbalaje': descripembalaje, # items.product_id.descripcion_embalaje if items.product_id.l10n_xma_is_hazaudous_material == 'si' else {},                   
                        'TipoMateria': items.product_id.l10n_xma_tipo_materia.clave if rec.l10n_xma_is_international_transport != 'no' else {},
                        'DescripcionMateria': (items.product_id.l10n_xma_tipo_materia.name if items.product_id.l10n_xma_tipo_materia.clave == '05' else {}) if rec.l10n_xma_is_international_transport != 'no' else {}
                        
                    })

            figuras = []
            for figs in self.l10n_xma_vehicle_id.l10n_xma_figures_ids:
                figuras.append({
                        'NombreFigura': figs.operador_id.name, # Que dato va a qui nombre de la figura o el operador
                        'NumLicencia': figs.operador_id.license_number,
                        'TipoFigura': figs.type,
                        'RFCFigura': figs.operador_id.vat,

                        # 'cartaporte31:Domicilio': {
                        #     'Calle': figs.operador_id.street or '',
                        #     'CodigoPostal': figs.operador_id.zip,
                        #     # 'Colonia': '%04d' % int(figs.operador_id.edi_colony_code_id.clave) if figs.operador_id.edi_colony_code_id.clave else {},
                        #     'Estado': figs.operador_id.state_id.code,
                        #     'Municipio':'%03d' % int(figs.operador_id.municipality_id.code) if figs.operador_id.municipality_id.code else {},
                        #     'NumeroExterior':figs.operador_id.street2 or '',
                        #     'Pais':figs.operador_id.country_id.edi_code,
                        # }
                    })
                
            Remolque = []
            for rem in self.l10n_xma_vehicle_id.l10n_xma_trailers_ids:
                Remolque.append({
                        'Placa': rem.name,
                        'SubTipoRem': rem.trailer_type_id.code,
                    })

            ubicaciones = []

            
            ubicaciones.append({
                'cartaporte31:Ubicacion': {
                            'DistanciaRecorrida': self.l10n_xma_distance_km,
                            'TipoUbicacion':"Destino",
                            'IDUbicacion': "DE" + str(self.location_dest_id.id).zfill(6),
                            'RFCRemitenteDestinatario': self.partner_id.vat if self.partner_id.country_id.code == 'MX' else 'XEXX010101000', #"BEAJ800907F71", 
                            'NombreRemitenteDestinatario': self.partner_id.name, #"Betran Angulo Jose Enrique",
                            'NumRegIdTrib': self.partner_id.vat if self.partner_id.country_id.code != 'MX' else {},
                            'ResidenciaFiscal': self.partner_id.country_id.l10n_xma_country_code if self.partner_id.country_id.code != 'MX' else {},
                            # 'NumEstacion': ,
                            #'NombreEstacion': ,
                            #'NavegacionTrafico': ,
                            
                            'FechaHoraSalidaLlegada': self.get_mx_current_datetime_ubications(self.l10n_xma_merchandise_release).strftime('%Y-%m-%dT%H:%M:%S'),

                            #'TipoEstacion': ,                  
                            
                            
                            
                            
                            'cartaporte31:Domicilio': {
                                'Calle': self.partner_id.street, #"LAGO DE GUADALUPE",
                                'CodigoPostal': self.partner_id.zip, #"52920",
                                # 'Colonia': '%04d' % int(rec.company_id.edi_colony_code_id.clave), #"2135",
                                'Estado': self.partner_id.state_id.code, #"MEX",
                                #'Localidad': "01",
                                'Municipio': self.partner_id.municipality_id.code, #"013"
                                'NumeroExterior':rec.partner_id.external_number,
                                'NumeroInterior':rec.partner_id.internal_number,
                                'Pais': self.partner_id.country_id.l10n_xma_country_code,
                                'Referencia': self.partner_id.ref,
                                'Colonia':self.partner_id.l10n_xma_colony_code
                            }
                        }
            })

            ubicaciones.append({
                    'cartaporte31:Ubicacion':{
                            'TipoUbicacion':"Origen" ,
                            'IDUbicacion':"OR" + str(self.location_id.id).zfill(6),
                            'RFCRemitenteDestinatario': self.company_id.vat if self.company_id.country_id.code == 'MX' else 'XEXX010101000', #"ZUC100723VB8",
                            'NombreRemitenteDestinatario': self.company_id.name, #"Zucarmex SA de CV",
                            'NumRegIdTrib': self.company_id.vat if self.company_id.country_id.code != 'MX' else {},
                            'ResidenciaFiscal': self.company_id.country_id.l10n_xma_country_code if self.company_id.country_id.code != 'MX' else {},
                            # 'NumEstacion': ,
                            #'NombreEstacion': ,
                            #'NavegacionTrafico': ,

                            'FechaHoraSalidaLlegada': self.get_mx_current_datetime_ubications(self.l10n_xma_goods_entry).strftime('%Y-%m-%dT%H:%M:%S'),
                            
                            #'TipoEstacion': ,
                            
                            #'DistanciaRecorrida': ,
                             # OR + id del registro
                            'cartaporte31:Domicilio':{
                                'Calle': self.company_id.partner_id.street, # "Lopez",
                                'CodigoPostal': self.company_id.zip, #"64410",
                                # 'Colonia': '%04d' % int(rec.company_id.edi_colony_code_id.clave), # "0252",
                                'Estado': self.company_id.partner_id.state_id.code,  #"NLE",
                                #'Localidad': "07",
                                'Municipio': self.company_id.partner_id.municipality_id.code, #"039",
                                'NumeroExterior':rec.company_id.partner_id.external_number,
                                'NumeroInterior':rec.company_id.partner_id.internal_number,
                                'Pais': self.company_id.partner_id.country_id.l10n_xma_country_code,
                                'Referencia': self.company_id.partner_id.ref,
                                'Colonia':self.company_id.partner_id.l10n_xma_colony_code
                            }
                        }
            })
            print("l10n_xma_is_registro_itsmo",rec.l10n_xma_is_registro_itsmo)
            valor_si = 'Sí'
            raduaneros = []
            if rec.l10n_xma_is_international_transport != 'no':
                for x in rec.l10n_xma_regimen_aduanero_id_id:
                    raduaneros.append({"cartaporte31:RegimenAduaneroCCP": { 'RegimenAduanero':x.clave}})

            Carta_porte = {
                'Version':"3.1",
                'IdCCP': rec.l10n_xma_idccp,
                'TranspInternac': 'No' if self.l10n_xma_is_international_transport == 'no' else 'Sí',
                # 'RegimenAduanero': rec.l10n_xma_regimen_aduanero_id_id.clave if rec.l10n_xma_is_international_transport != 'no' else {},
                'EntradaSalidaMerc': rec.l10n_xma_entradasalida.capitalize() if rec.l10n_xma_is_international_transport != 'no' else {},
                'PaisOrigenDestino': rec.partner_id.country_id.l10n_xma_country_code if rec.l10n_xma_is_international_transport != 'no' else {},
                'ViaEntradaSalida': rec.l10n_xma_cve_transporte_id.clave if rec.l10n_xma_is_international_transport != 'no' else {},
                'TotalDistRec': rec.l10n_xma_distance_km, #
                'RegistroISTMO': 'Sí' if rec.l10n_xma_is_registro_itsmo == 'si' else {},
                'UbicacionPoloOrigen': rec.l10n_xma_polo_origen_id.clave if rec.l10n_xma_is_registro_itsmo == 'si' else {},
                'UbicacionPoloDestino': rec.l10n_xma_polo_destino_id.clave if rec.l10n_xma_is_registro_itsmo == 'si' else {},  

                "cartaporte31:RegimenesAduaneros": raduaneros,

                'cartaporte31:Ubicaciones': ubicaciones,
                'cartaporte31:Mercancias':{
                    
                    # 'CargoPorTasacion':"1222",
                    'LogisticaInversaRecoleccionDevolucion': 'Sí', # actualizacion solo se queda en si no tiene otra opcion

                    'PesoBrutoTotal': self.l10n_xma_weight_total_products,# campo computado
                    
                    'NumTotalMercancias': int(self.l10n_xma_qty_total_products), #total productos 
                    
                    'PesoNetoTotal': total_weight,
                     
                    'UnidadPeso': "XBX",

                    'cartaporte31:Mercancia':Mercancia,

                    'cartaporte31:Autotransporte':{

                        'NumPermisoSCT': rec.l10n_xma_vehicle_id.num_permiso_sct if rec.l10n_xma_vehicle_id.num_permiso_sct else {},
                        'PermSCT': rec.l10n_xma_vehicle_id.permission_type_id.code if rec.l10n_xma_vehicle_id.permission_type_id.code else {},

                        'cartaporte31:IdentificacionVehicular':{
                            'PlacaVM': rec.l10n_xma_vehicle_id.vehicle_licence if rec.l10n_xma_vehicle_id.vehicle_licence else {},
                            'AnioModeloVM': rec.l10n_xma_vehicle_id.vehicle_model if rec.l10n_xma_vehicle_id.vehicle_model else {},  
                            'ConfigVehicular': rec.l10n_xma_vehicle_id.vehicle_type_id.code if rec.l10n_xma_vehicle_id.vehicle_type_id.code else {},
                            'PesoBrutoVehicular': rec.l10n_xma_vehicle_id.total_vehice_weigth if rec.l10n_xma_vehicle_id.total_vehice_weigth else {},
                        },
                        'cartaporte31:Seguros':{
                            'PolizaRespCivil': rec.l10n_xma_vehicle_id.insure_policy if rec.l10n_xma_vehicle_id.insure_policy else {},
                            'AseguraRespCivil': rec.l10n_xma_vehicle_id.insure_company if rec.l10n_xma_vehicle_id.insure_company else {},
                            'AseguraCarga': rec.l10n_xma_vehicle_id.goods_insurer if rec.l10n_xma_vehicle_id.goods_insurer else {},
                            'PolizaCarga': rec.l10n_xma_vehicle_id.goods_insurer_policy if rec.l10n_xma_vehicle_id.goods_insurer_policy else {},
                            'AseguraMedAmbiente': rec.l10n_xma_vehicle_id.environment_insurer_company if rec.l10n_xma_vehicle_id.environment_insurer_company and materialp > 0 else {},
                            'PolizaMedAmbiente': rec.l10n_xma_vehicle_id.environment_insurer_policy if rec.l10n_xma_vehicle_id.environment_insurer_policy and materialp > 0 else {},
                        },
                        # 'cartaporte31:Remolques': {
                        #     'cartaporte31:Remolque':Remolque
                        # },   
                        
                    },
                },
                'cartaporte31:FiguraTransporte':{
                    'cartaporte31:TiposFigura':figuras,
                    
                }


            }
            print("Carta_porte 283++++++++++", Carta_porte, )              
            return Carta_porte
        
    def get_values_cofepris(self, id):
        
        print("get_values_cofepris", id)
        goods = self.env['l10n.xma.goods'].search([('stock_move_line_id','=', id)], limit=1)
        print("get_values_cofepris goods", goods)
        if goods:
            return goods
        else:
            return  False
        
    def _get_FechaOrig(self):
        for rec in self:

            date = rec.l10n_xma_goods_entry.strftime('%Y-%m-%dT%H:%M:%S')

            return date
           

    @api.model
    def _l10n_mx_edi_xmarts_info(self):
        url = 'http://ws.facturacionmexico.com.mx/pac/?wsdl'
        return {
            'url': url,
            'multi': False,  # TODO: implement multi
            'username': 'EKU9003173C9' if self.company_id.edi_test_pac == True else self.company_id.edi_user_pac,
            'password': 'EKU9003173C9' if self.company_id.edi_test_pac == True else self.company_id.edi_pass_pac,
            'production': 'NO' if self.company_id.edi_test_pac == True else 'SI',
        }

    def get_edi_json(self):
        for rec in self:

            #time_invoice = fields.Date.context_today(self) #self.env['einvoice.edi.certificate'].sudo().get_mx_current_datetime()
            
            # time_invoice = self.get_mx_current_datetime()
            current_dt = datetime.now()
            date_time = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), current_dt)
            # self.l10n_xma_date_post = current_dt
            time_invoice = date_time
            lista_productos = []
            for items in rec.move_ids_without_package:
                
                lista_productos.append({"cfdi:Concepto": {
                            'Cantidad': items.product_uom_qty,
                            'ClaveProdServ': items.product_id.l10n_xma_productcode_id.code,
                            'ClaveUnidad': items.product_uom.l10n_xma_uomcode_id.code,
                            'Descripcion': items.description_picking.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;'),
                            'Importe': "0.00",
                            'ValorUnitario': "0.00",                                                
                            'Unidad': items.product_uom.name,
                            'ObjetoImp':"01",
                            'NoIdentificacion': items.product_id.default_code or '01',
                            #'ObjetoImp': '02' if obj_imp > 0 else '01',
                            #'Descuento': ('%.*f' % (rec.currency_id.decimal_places, subtotal_wo_discount(line) - line.price_subtotal)),
                            # "cfdi:Impuestos": {"cfdi:Traslados": product_taxes_list, "cfdi:Retenciones": product_taxes_list2},
                            # "cfdi:InformacionAduanera": pedimentos
                        }})
            
            xml_json = {
                'Fecha': time_invoice.strftime('%Y-%m-%dT%H:%M:%S'),
                'Folio': self.name.split('/')[2],
                'Serie': self.name.split('/')[0],
                'TipoDeComprobante': 'T',
                'LugarExpedicion': self.company_id.zip or  self.company_id.partner_id.zip,
                'Moneda': 'XXX',
                'Version': '4.0',
                'Exportacion':"01",
                'SubTotal': 0,
                'Total': 0,
                'xmlns:cartaporte31': 'http://www.sat.gob.mx/CartaPorte31',
                'xmlns:cfdi': 'http://www.sat.gob.mx/cfd/4',
                'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                'xsi:schemaLocation': 'http://www.sat.gob.mx/cfd/4 http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd http://www.sat.gob.mx/CartaPorte31 http://www.sat.gob.mx/sitio_internet/cfd/CartaPorte/CartaPorte31.xsd',
                'Sello': '',
                #'FormaPago': '',
                'NoCertificado': '',
                'Certificado': '',          
                'cfdi:Emisor': {
                    'Rfc': self.company_id.vat,
                    'Nombre': self.company_id.name,
                    'RegimenFiscal': self.company_id.partner_id.l10n_xma_taxpayer_type_id.code
                },
                'cfdi:Receptor':{
                                'Rfc': self.company_id.vat if self.l10n_xma_trasport_type == '00' else self.company_id.vat,
                                'Nombre': self.company_id.name  if self.l10n_xma_trasport_type == '00' else self.company_id.name,
                                'UsoCFDI': 'S01',
                                'DomicilioFiscalReceptor': self.partner_id.zip,
                                'RegimenFiscalReceptor': self.company_id.partner_id.l10n_xma_taxpayer_type_id.code  if self.l10n_xma_trasport_type == '00' else self.company_id.partner_id.l10n_xma_taxpayer_type_id.code,
                },
                'cfdi:Conceptos': lista_productos,
            }
            if self.l10n_xma_trasport_type == '01':
                xml_json['xmlns:cartaporte31']="http://www.sat.gob.mx/CartaPorte31"
                xml_json['cfdi:Complemento']={
                            'cartaporte31:CartaPorte' : rec.edi_sign_transfer_invoice() 
                            }
                if self.l10n_xma_vehicle_id.l10n_xma_trailers_ids:
                    remolque = []
                    for line in self.l10n_xma_vehicle_id.l10n_xma_trailers_ids:
                        remolque.append({
                            'cartaporte31:Remolque':{
                                    'SubTipoRem': line.trailer_type_id.code,
                                    'Placa': line.name,
                                }
                        })
                    xml_json['cfdi:Complemento']['cartaporte31:CartaPorte']['cartaporte31:Mercancias']['cartaporte31:Autotransporte'].update({
                        'cartaporte31:Remolques':remolque
                    })
                print(xml_json['cfdi:Complemento']['cartaporte31:CartaPorte']['cartaporte31:Mercancias'])
            return xml_json

    def edi_sign_invoice(self):
        for rec in self:
            xml_json = rec.get_edi_json()
            try:
                user_data = rec._l10n_mx_edi_xmarts_info()
                _logger.info(user_data)
                url = 'http://159.203.170.13:8069' #rec.company_id.edi_url_bd
                db = 'server'
                # username = 'admin'
                # password = '123'
                #url = rec.company_id.edi_url_bd
                #db = rec.company_id.edi_name_bd
                username = rec.company_id.edi_user_bd
                password = rec.company_id.edi_passw_bd  # password_xmarts

                _logger.info(url, db, username, password)
                common = xmlrpc.client.ServerProxy(
                    '{}/xmlrpc/2/common'.format(url))
                uid = common.authenticate(db, username, password, {})
                models = xmlrpc.client.ServerProxy(
                    '{}/xmlrpc/2/object'.format(url))
                response = {}
                model_name = 'sign.account.move'
                print("DATOS ACCESO: ",url,username,password, user_data['username'],user_data['password'],user_data['production'])
                response = models.execute_kw(db, uid, password, model_name,'request_sign_invoice', [False,
                                                                                xml_json, user_data['username'],
                                                                                user_data['password'],
                                                                                user_data['production'],'F'])
                
                print("esponse['code']",response['code'])
                if str(response['code']) == '200':
                    rec.l10n_sing = True
                    rec.message_post(body=response['msg'], message_type='notification')
                    rec.l10n_xma_electronic_number = response['uuid']
                    rec.edi_cfdi_name = \
                        ('%s-carta-%s.xml' %
                            (rec.name,
                            "4.0".replace('.', '-'))).replace('/', '')
                    self.edi_cfdi = response['xml']
                    rec.edi_cadena_original = response['cadena']
                else:
                    rec.message_post(body=response['msg'], message_type='notification')

            except Exception as err:
                _logger.info("xma_log except err: %s", err)
                rec.message_post(
                    body=f'The sign service requested failed: {err}',
                    message_type='notification')
                

    def _l10n_mx_edi_get_signed_cfdi_data(self):
        self.ensure_one()
        if self.l10n_sing == True:
            return base64.decodebytes(self.edi_cfdi)
        return None
                
    def _l10n_mx_edi_decode_cfdi_carta(self, cfdi_data=None):
        ''' Helper to extract relevant data from the CFDI to be used, for example, when printing the picking.
        TODO replace this function in l10n_mx_edi.account_move with a reusable model method
        :param cfdi_data:   The optional cfdi data.
        :return:            A python dictionary.
        '''
        self.ensure_one()

        def get_node(cfdi_node, attribute, namespaces):
            if hasattr(cfdi_node, 'Complemento'):
                node = cfdi_node.Complemento.xpath(attribute, namespaces=namespaces)
                return node[0] if node else None
            else:
                return None

        # Get the signed cfdi data.
        if not cfdi_data:
            cfdi_data = self._l10n_mx_edi_get_signed_cfdi_data()

        # Nothing to decode.
        if not cfdi_data:
            return {}

        cfdi_node = objectify.fromstring(cfdi_data)
        tfd_node = get_node(
            cfdi_node,
            'tfd:TimbreFiscalDigital[1]',
            {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'},
        )
        print("xxxx1",cfdi_node.get('sello', cfdi_node.get('Sello', 'No identificado')))
        print("xxxx2",cfdi_node.Emisor.get('Rfc', cfdi_node.Emisor.get('rfc')))
        print("xxxx3",cfdi_node.Receptor.get('Rfc', cfdi_node.Receptor.get('rfc')))
        print("xxxx4",({} if tfd_node is None else tfd_node).get('UUID'))
        return {
            'uuid': ({} if tfd_node is None else tfd_node).get('UUID'),
            'supplier_rfc': cfdi_node.Emisor.get('Rfc', cfdi_node.Emisor.get('rfc')),
            'customer_rfc': cfdi_node.Receptor.get('Rfc', cfdi_node.Receptor.get('rfc')),
            'amount_total': cfdi_node.get('Total', cfdi_node.get('total')),
            'cfdi_node': cfdi_node,
            'usage': cfdi_node.Receptor.get('UsoCFDI'),
            'payment_method': cfdi_node.get('formaDePago', cfdi_node.get('MetodoPago')),
            'bank_account': cfdi_node.get('NumCtaPago'),
            'sello': cfdi_node.get('sello', cfdi_node.get('Sello', 'No identificado')),
            'sello_sat': tfd_node is not None and tfd_node.get('selloSAT', tfd_node.get('SelloSAT', 'No identificado')),
            'cadena': self.edi_cadena_original,
            'certificate_number': cfdi_node.get('noCertificado', cfdi_node.get('NoCertificado')),
            'certificate_sat_number': tfd_node is not None and tfd_node.get('NoCertificadoSAT'),
            'expedition': cfdi_node.get('LugarExpedicion'),
            'fiscal_regime': cfdi_node.Emisor.get('RegimenFiscal', ''),
            'emission_date_str': cfdi_node.get('fecha', cfdi_node.get('Fecha', '')).replace('T', ' '),
            'stamp_date': tfd_node is not None and tfd_node.get('FechaTimbrado', '').replace('T', ' '),
            'emission_date': cfdi_node.get('fecha', cfdi_node.get('Fecha', '')),
        }

    def xx(self,x):
        print("+++  488 +++",x)
    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        for rec in self:
            if not rec.l10n_xma_idccp:
                rec.l10n_xma_idccp = rec.generate_IdCCP()
        return res

    def action_confirm(self):
        res = super(StockPicking, self).action_confirm()
        for rec in self:
            if not rec.l10n_xma_idccp:
                rec.l10n_xma_idccp = rec.generate_IdCCP()
        return res

    def generate_IdCCP(self):
        self.ensure_one()
        # Generar un UUID
        generated_uuid = uuid.uuid4()

        # Convertir el UUID a su representación en cadena
        uuid_str = str(generated_uuid)

        # Reemplazar los primeros caracteres por "CCC" (asegúrate de que la longitud sea la misma)
        uuid_with_c = "CCC" + uuid_str[3:]

        print("UUID con 'CCC' al inicio:", uuid_with_c)
        uuid_with_c = uuid_with_c.upper()

        return uuid_with_c

    ##------------------------------------------##
