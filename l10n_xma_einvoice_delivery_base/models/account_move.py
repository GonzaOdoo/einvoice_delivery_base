# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import json
from lxml.objectify import fromstring
import base64
from datetime import datetime, timedelta
from odoo.tools import float_round
import time
from random import choice, randint
from lxml import etree, objectify
import uuid
from MqttLibPy.client import MqttClient
from MqttLibPy.serializer import Serializer



class AccountMove(models.Model):
    _inherit = "account.move"

    
    l10n_xma_edelivery_invoice = fields.Boolean(
        string='Es documento de traslado',
    )
    l10n_xma_transport_type = fields.Selection(
        selection=[
            ('NA', "Nacional"),
            ('IN', "Internacional"),
        ], default="NA",
        string="Tipo de transporte", )
    
    l10n_xma_distance_traveled = fields.Float(
        string='Distancia recorrida',
    )
    
    l10n_xma_vehicle_id = fields.Many2one(
        string='Vehículo',
        comodel_name='l10n.xma.vehicle',
        ondelete='restrict',
    )

    l10n_xma_goods_movements_ids = fields.One2many('l10n.xma.goods.movements', 'move_id', copy=True, string="Movimiento de mercancías")

    l10n_xma_goods_ids = fields.One2many('l10n.xma.goods', 'move_id', copy=True, string="Mercancias")


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
        copy=False,
    )
    
    l10n_xma_goods_entry = fields.Datetime(
        string='Fecha y hora de entrada',
        default=fields.Datetime.now,
    )

    l10n_xma_merchandise_release = fields.Datetime(
        string='Fecha y hora de salida',
    )

    ##------------------------------------------#

    ##---------- functions   -------------##

    def generate_IdCCP(self):
        # Generar un UUID
        generated_uuid = uuid.uuid4()

        # Convertir el UUID a su representación en cadena
        uuid_str = str(generated_uuid)

        # Reemplazar los primeros caracteres por "CCC" (asegúrate de que la longitud sea la misma)
        uuid_with_c = "CCC" + uuid_str[3:]

        print("UUID con 'CCC' al inicio:", uuid_with_c)

        return uuid_with_c

    def action_post(self):
        for record in self:
            if not record.l10n_xma_idccp:
                record.l10n_xma_idccp = record.generate_IdCCP()
        return super(AccountMove, self).action_post()

    def calculate_qty_total(self):
        for rec in self:
            qty = 0
            for items in rec.l10n_xma_goods_ids:
                qty += items.quantity
            return qty
        
    def calculate_qty_total_general(self):
        for rec in self:
            qty = 0
            for items in rec.l10n_xma_goods_ids:
                qty += 1
            return qty
        
    def calculate_weight_total(self):
        for rec in self:
            weight = 0
            for items in rec.l10n_xma_goods_ids:
                weight += items.weight

            return weight

    def get_mx_current_datetime(self):
        return fields.Datetime.context_timestamp(
            self.with_context(tz='America/Mexico_City'), self.l10n_xma_date_post)
    
    def get_mx_current_datetime_ubications(self, date):
        return fields.Datetime.context_timestamp(
            self.with_context(tz='America/Mexico_City'), date)
    
    def edi_sign_transfer_invoice(self):
        for rec in self:
            #time_invoice = fields.Date.context_today(self) #self.env['einvoice.edi.certificate'].sudo().get_mx_current_datetime()
            # time_invoice = rec.get_mx_current_datetime()
            current_dt = datetime.now()
            date_time = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), current_dt)
            self.l10n_xma_date_post = current_dt
            time_invoice = date_time
            
            # Mercancia = []
            # items = 0
            # pbruto = 0
            # # items += 1
            # # pbruto += round(((l.quantity * l.product_id.weight) * l.product_uom_id.factor_inv),4)
            # CantidadTransporta = []
            # CantidadTransporta.append({

            #     'Cantidad': self.l10n_xma_qty_total_products,# totaltodos los productos  | hacer campo calculadoi
            #     'IDDestino': "DE" + str(self.location_dest_id.id).zfill(6), # DE + id del registro
            #     'IDOrigen':"OR" + str(self.location_id.id).zfill(6),  # OR + id del registro
            # })
            # for items in rec.move_ids_without_package:
            #     Mercancia.append({
            #         'BienesTransp': items.product_id.l10n_xma_productcode_id.code, #codesat
            #         'Cantidad': items.product_uom_qty, #qty
            #         'Descripcion':items.description_picking.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;'), # name
            #         'ClaveUnidad': items.product_uom.l10n_xma_uomcode.code, #codesat unidad de medida 
            #         'PesoEnKg': items.product_id.weight, # peso
            #         'cartaporte31:CantidadTransporta': CantidadTransporta,
            #     })
            # figuras = []
            # for figs in self.l10n_xma_vehicle_id.l10n_xma_figures_ids:
            #     figuras.append({
            #             'TipoFigura': figs.type_of_operdor,
            #             'RFCFigura': figs.operador_id.vat,
            #             'NumLicencia': figs.operador_id.license_number,

            #             # 'cartaporte31:Domicilio': {
            #             #     'Calle': rec.vehicle_id.driver_id.street or '',
            #             #     'CodigoPostal': rec.vehicle_id.driver_id.zip,
            #             #     'Colonia': '%04d' % int(rec.vehicle_id.driver_id.edi_colony_code_id.clave),
            #             #     'Estado': rec.vehicle_id.driver_id.state_id.code,
            #             #     'Municipio':'%03d' % int(rec.vehicle_id.driver_id.edi_edi_municipality_id.code),
            #             #     'NumeroExterior':rec.vehicle_id.driver_id.street2 or '',
            #             #     'Pais':rec.vehicle_id.driver_id.country_id.edi_code,
            #             # }
            #         })
            Ubicaciones = []
            idorigen = 0
            iddestino = 0
            for line in self.l10n_xma_goods_movements_ids:
                if line.transfer_type == 'Origen':
                    idorigen = line.id
                    Ubicaciones.append({
                        'cartaporte31:Ubicacion': {
                            'TipoUbicacion':"Origen" ,
                            'RFCRemitenteDestinatario': line.vat if line.country_id.code == 'MX' else 'XEXX010101000',
                            'NumRegIdTrib': '01010101' if line.country_id.code != 'MX' else {},
                            'ResidenciaFiscal': line.country_id.l10n_xma_country_code if line.country_id.code != 'MX' else {},
                            'FechaHoraSalidaLlegada': self.get_mx_current_datetime_ubications(line.date_transfer).strftime('%Y-%m-%dT%H:%M:%S'),
                            'IDUbicacion':"OR" + str(line.id).zfill(6), # OR + id del registro
                            'cartaporte31:Domicilio':{
                                'Calle': line.street, 
                                'CodigoPostal':line.cp,
                                #'Colonia':'%04d' % int(rec.company_id.edi_colony_code_id.clave),
                                'Estado': line.state_id.code, 
                                'Municipio': line.municipality_id.code,
                                'NumeroExterior':line.external_number,
                                'NumeroInterior':line.internal_number,
                                'Pais': line.country_id.l10n_xma_country_code,
                                'Referencia': line.reference,
                                'Colonia': line.colony_code
                            },                  
                            },
                    })
                else:
                    iddestino = line.id
                    Ubicaciones.append({
                        'cartaporte31:Ubicacion': {
                            'TipoUbicacion':"Destino" ,
                            'DistanciaRecorrida': self.l10n_xma_distance_traveled,
                            'RFCRemitenteDestinatario': line.vat if line.country_id.code == 'MX' else 'XEXX010101000',
                            'NumRegIdTrib': '01010101' if line.country_id.code != 'MX' else {},
                            'ResidenciaFiscal': line.country_id.l10n_xma_country_code if line.country_id.code != 'MX' else {},
                            'FechaHoraSalidaLlegada': self.get_mx_current_datetime_ubications(line.date_transfer).strftime('%Y-%m-%dT%H:%M:%S'),
                            'IDUbicacion':"DE" + str(line.id).zfill(6), # OR + id del registro
                            'cartaporte31:Domicilio':{
                                'Calle': line.street, 
                                'CodigoPostal':line.cp,
                                #'Colonia':'%04d' % int(rec.company_id.edi_colony_code_id.clave),
                                'Estado': line.state_id.code, 
                                'Municipio': line.municipality_id.code,
                                'NumeroExterior':line.external_number,
                                'NumeroInterior':line.internal_number,
                                'Pais': line.country_id.l10n_xma_country_code,
                                'Referencia': line.reference,
                                'Colonia': line.colony_code
                            },                  
                            },
                    })

            Mercancia = []
            items = 0
            pbruto = 0
            # items += 1
            # pbruto += round(((l.quantity * l.product_id.weight) * l.product_uom_id.factor_inv),4)
            CantidadTransporta = []
            CantidadTransporta.append({

                'Cantidad': rec.calculate_qty_total(),# totaltodos los productos  | hacer campo calculadoi
                'IDDestino': "DE" + str(iddestino).zfill(6), # DE + id del registro
                'IDOrigen':"OR" + str(idorigen).zfill(6),  # OR + id del registro
            })
            materialp = 0
            for items in rec.l10n_xma_goods_ids:

                materialpeligroso = ''
                cvematerialpeligroso = ''
                embalaje = ''
                descripembalaje = ''
                if items.l10n_xma_is_hazaudous_material == 'si':
                    materialp += 1
                    materialpeligroso = 'Sí'
                    cvematerialpeligroso = items.l10n_xma_hazaudous_material_id.code
                    embalaje = items.l10n_xma_tipo_embalaje_id.clave
                    descripembalaje = items.descripcion_embalaje
                elif  items.l10n_xma_is_hazaudous_material ==  'noo':
                    materialpeligroso = 'No'
                    cvematerialpeligroso = {}
                    embalaje = {}
                    descripembalaje = {}
                else:
                    materialpeligroso = {}
                    cvematerialpeligroso = {}
                    embalaje = {}
                    descripembalaje = {}
                Mercancia.append({
                    'BienesTransp': items.product_code_id.code, #codesat
                    'Cantidad': '%.3f' % float(items.quantity), #qty
                    'Descripcion':items.description.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;'), # name
                    'ClaveUnidad': items.uom_id.l10n_xma_uomcode_id.code, #codesat unidad de medida 
                    'PesoEnKg': '%.3f' % float(items.weight), # peso
                    'MaterialPeligroso': materialpeligroso, #  'Sí' if items.l10n_xma_is_hazaudous_material == 'si' else 'No',
                    'CveMaterialPeligroso': cvematerialpeligroso, # items.l10n_xma_hazaudous_material_id.code if items.l10n_xma_is_hazaudous_material == 'si' else {},
                    'Embalaje': embalaje, #items.l10n_xma_tipo_embalaje_id.clave if items.l10n_xma_is_hazaudous_material == 'si' else {},
                    'DescripEmbalaje': descripembalaje, #items.descripcion_embalaje if items.l10n_xma_is_hazaudous_material == 'si' else {},
                    'TipoMateria': items.l10n_xma_tipo_materia.clave if rec.l10n_xma_is_international_transport != 'no' else {},
                    'DescripcionMateria': (items.l10n_xma_tipo_materia.name if items.l10n_xma_tipo_materia.clave == '05' else {}) if rec.l10n_xma_is_international_transport != 'no' else {},
                    'SectorCOFEPRIS': items.l10n_xma_sector_cofepris_id_id.clave if items.l10n_xma_sector_cofepris_id_id.clave else {},
                    'NombreIngredienteActivo': items.nombre_ingrediente_activo if items.nombre_ingrediente_activo else {},
                    'NomQuimico': items.nomquimico if items.nomquimico else {},
                    'DenominacionGenericaProd': items.dengenprod if items.dengenprod else {},
                    'DenominacionDistintivaProd': items.dendistprod if items.dendistprod else {},
                    'Fabricante': items.fabricante if items.fabricante else {},
                    'FechaCaducidad':  items.fecha_caducidad.strftime('%Y-%m-%d')  if items.fecha_caducidad else {},
                    'LoteMedicamento': items.lote_medicamento if items.lote_medicamento else {},
                    'FormaFarmaceutica': items.forma_farmaceutica_id.clave if items.forma_farmaceutica_id.clave else {},
                    'CondicionesEspTransp': items.condiciones_especiales_id.clave if items.condiciones_especiales_id.clave else {},
                    'RegistroSanitarioFolioAutorizacion': items.regsanfolauto if items.regsanfolauto else {},
                    'PermisoImportacion': items.permiso_importacion if items.permiso_importacion else {},
                    'FolioImpoVUCEM': items.folimpvucem if items.folimpvucem else {},
                    'NumCAS': items.numcas if items.numcas else {},
                    'RazonSocialEmpImp': items.razsocempimp if items.razsocempimp else {},
                    'NumRegSanPlagCOFEPRIS': items.num_regsanplag_cofepris if items.num_regsanplag_cofepris else {},
                    'DatosFabricante': items.datos_fabricante if items.datos_fabricante else {},
                    'DatosFormulador': items.datos_formulador if items.datos_formulador else {},
                    'DatosMaquilador': items.datos_maquilador if items.datos_maquilador else {},
                    'UsoAutorizado': items.uso_autorizado if items.uso_autorizado else {},

                    'cartaporte31:CantidadTransporta': CantidadTransporta,
                })
            figuras = []
            for figs in self.l10n_xma_vehicle_id.l10n_xma_figures_ids:
                figuras.append({
                        'NombreFigura': figs.operador_id.name,
                        'TipoFigura': figs.type,
                        'RFCFigura': figs.operador_id.vat,
                        'NumLicencia': figs.operador_id.license_number,

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
            
            raduaneros = []
            if rec.l10n_xma_is_international_transport != 'no':
                for x in rec.l10n_xma_regimen_aduanero_id_id:
                    raduaneros.append({'cartaporte31:RegimenAduaneroCCP': { 'RegimenAduanero':x.clave}})
            Carta_porte = {
                'Version':"3.1",
                'IdCCP': rec.l10n_xma_idccp,
                'TranspInternac': 'No' if self.l10n_xma_is_international_transport == 'no' else 'Sí',
                # 'RegimenAduanero': rec.l10n_xma_regimen_aduanero_id_id.clave if rec.l10n_xma_is_international_transport != 'no' else {},
                'EntradaSalidaMerc': rec.l10n_xma_entradasalida.capitalize() if rec.l10n_xma_is_international_transport != 'no' else {},
                'PaisOrigenDestino': rec.partner_id.country_id.l10n_xma_country_code if rec.l10n_xma_is_international_transport != 'no' else {},
                'ViaEntradaSalida': rec.l10n_xma_cve_transporte_id.clave if rec.l10n_xma_is_international_transport != 'no' else {},
                'TotalDistRec': rec.l10n_xma_distance_traveled, #
                'RegistroISTMO': 'Sí' if rec.l10n_xma_is_registro_itsmo == 'si' else {},
                'UbicacionPoloOrigen': rec.l10n_xma_polo_origen_id.clave if rec.l10n_xma_is_registro_itsmo == 'si' else {},
                'UbicacionPoloDestino': rec.l10n_xma_polo_destino_id.clave if rec.l10n_xma_is_registro_itsmo == 'si' else {},
                'cartaporte31:RegimenesAduaneros': raduaneros,
                'cartaporte31:Ubicaciones': Ubicaciones,
                'cartaporte31:Mercancias':{

                    'PesoBrutoTotal': self.calculate_weight_total(),# campo computado
                    'UnidadPeso':"KGM",
                    'NumTotalMercancias': self.calculate_qty_total_general(), #total productos 

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
                        #     # 'cartaporte31:Remolque':Remolque
                        # },   
                        
                    },
                },
                'cartaporte31:FiguraTransporte':{
                    'cartaporte31:TiposFigura':figuras,
                    
                }


            }                
            return Carta_porte
        
        

    def generate_json_l10n_mx_delivery_mx(self):
        def subtotal_wo_discount(l): return float_round(
            l.price_subtotal / (1 - l.discount/100) if l.discount != 100 else
            l.price_unit * l.quantity, int(2))
        def tax_name(t): return {
            'ISR': '001', 'IVA': '002', 'IEPS': '003'}.get(t, False)
        
        current_dt = datetime.now()
        date_time = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), current_dt)
        self.l10n_xma_date_post = current_dt
        time_invoice = date_time
        conceptos = []
        for items in self.invoice_line_ids:
            if items.product_id:
                traslados1 = []
                retenciones1 = []
                obje_imp = 0
                if items.tax_ids:
                    for taxes in items.tax_ids:
                        if taxes.amount >= 0:
                            obje_imp+=1
                            print("items.tax_base_amount * (taxes.amount / 100)", items.tax_base_amount * (taxes.amount / 100))
                            print('items.tax_base_amount', items.tax_base_amount, 'taxes.amount', taxes.amount)
                            traslados1.append({
                                'cfdi:Traslado': {
                                    'Base': items.price_subtotal,
                                    'Impuesto': taxes.l10n_xma_tax_type_id.code, 
                                    'TipoFactor': taxes.l10n_xma_tax_factor_type_id.name, 
                                    'TasaOCuota': '%.6f' % abs(taxes.amount if taxes.amount_type == 'fixed' else (taxes.amount / 100.0)), 
                                    'Importe': round(items.price_subtotal * (taxes.amount / 100), 2)
                                }
                            })
                        else:
                            obje_imp+=1
                            print("items.tax_base_amount * (taxes.amount / 100)", items.tax_base_amount * (taxes.amount / 100))
                            print('items.tax_base_amount', items.tax_base_amount, 'taxes.amount', taxes.amount)
                            retenciones1.append({
                                'cfdi:Retencion': {
                                    'Base': items.price_subtotal,
                                    'Impuesto': taxes.l10n_xma_tax_type_id.code, 
                                    'TipoFactor': taxes.l10n_xma_tax_factor_type_id.name, 
                                    'TasaOCuota': '%.6f' % abs(taxes.amount if taxes.amount_type == 'fixed' else (taxes.amount / 100.0)), 
                                    'Importe': round(items.price_subtotal * (taxes.amount / 100), 2) * -1
                                }
                            })
                print(':::::::::::::::::::::::traslados:::::::::::::::::::::::::', traslados1)
                if items.product_id.default_code:
                    conceptos.append({
                        'cfdi:Concepto':{
                            'ClaveProdServ':items.product_id.l10n_xma_productcode_id.code,
                            'NoIdentificacion': items.product_id.default_code or '',
                            'Cantidad': '%.6f' % items.quantity,
                            'ClaveUnidad': items.product_uom_id.l10n_xma_uomcode_id.code,
                            'Unidad': items.product_uom_id.name,
                            'Descripcion': items.name.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;'),
                            'ValorUnitario': '%.*f' % (self.currency_id.decimal_places, subtotal_wo_discount(items)/items.quantity) if items.quantity else 0.0,
                            'Importe': '%.*f' % (self.currency_id.decimal_places, subtotal_wo_discount(items)),
                            'ObjetoImp': '02' if obje_imp > 0 else '01',
                            'Descuento': ('%.*f' % (self.currency_id.decimal_places, subtotal_wo_discount(items) - items.price_subtotal)),
                            'cfdi:Impuestos': {
                                'cfdi:Traslados': traslados1 if traslados1 else [],
                                'cfdi:Retenciones': retenciones1 if retenciones1 else []
                            }
                        },
                    })
                else:
                    conceptos.append({
                        'cfdi:Concepto':{
                            'ClaveProdServ':items.product_id.l10n_xma_productcode_id.code,
                            'Cantidad': '%.6f' % items.quantity,
                            'ClaveUnidad': items.product_uom_id.l10n_xma_uomcode_id.code,
                            'Unidad': items.product_uom_id.name,
                            'Descripcion': items.name.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;'),
                            'ValorUnitario': '%.*f' % (self.currency_id.decimal_places, subtotal_wo_discount(items)/items.quantity) if items.quantity else 0.0,
                            'Importe': '%.*f' % (self.currency_id.decimal_places, subtotal_wo_discount(items)),
                            'ObjetoImp': '02' if obje_imp > 0 else '01',
                            'Descuento': ('%.*f' % (self.currency_id.decimal_places, subtotal_wo_discount(items) - items.price_subtotal)),
                            'cfdi:Impuestos': {
                                'cfdi:Traslados': traslados1 if traslados1 else [],
                                'cfdi:Retenciones': retenciones1 if retenciones1 else []
                            }
                        },
                    })
        # traslados = []

        # for line in self.invoice_line_ids:
        #     for taxes in line.tax_ids:
        #         traslados.append({
        #             'cfdi:Traslado': {
        #                 'Importe': self.amount_total, 
        #                 'Impuesto': taxes.l10n_xma_tax_type_id.code,
        #                 'TipoFactor': taxes.l10n_xma_tax_factor_type_id.name,
        #                 'TasaOCuota': self.amount_total * (taxes.amount / 100)
        #             }
        #         })
        total_withhold = 0
        withhold_count = 0
        total_transferred = 0
        transferred_count = 0
        name_transferred = ""
        name_withhold = ""
        type_transferred = ""
        taxes_lines = []

        transferred_taxes = []

        withhold_taxes = []

        for line in self.invoice_line_ids.filtered('price_subtotal'):
            price = line.price_unit * \
                (1.0 - (line.discount or 0.0) / 100.0)
            tax_line = {tax['id']: tax for tax in line.tax_ids.compute_all(
                price, line.currency_id, line.quantity, line.product_id, line.partner_id, self.move_type in ('in_refund', 'out_refund'))['taxes']}
            for tax in line.tax_ids.filtered(lambda r: r.l10n_xma_tax_factor_type_id.name != 'Exento'):
                tax_dict = tax_line.get(tax.id, {})
                tasa = '%.6f' % abs(
                            tax.amount if tax.amount_type == 'fixed' else (tax.amount / 100.0))
                amount = round(abs(tax_dict.get(
                    'amount', tax.amount / 100 * float("%.2f" % line.price_subtotal))), 2)
                basee = round(float(amount) / float(tasa) if tax.amount_type == 'fixed' else tax_dict.get('base', line.price_subtotal), line.currency_id.decimal_places)
                if tax.amount >= 0:
                    total_transferred = round((total_transferred + amount), 2)
                    name_transferred = tax.l10n_xma_tax_type_id.code
                    print("------------------------------", name_transferred)
                    type_transferred = tax.l10n_xma_tax_factor_type_id.name

                    exist = False
                    print("LISTAAAAAA: ", transferred_taxes)
                    for tt in transferred_taxes:
                        if tax.id == tt['cfdi:Traslado']['id']:
                            exist = True
                            tt['cfdi:Traslado']['Importe'] += round(amount, 2)
                            tt['cfdi:Traslado']['Base'] += basee
                    if exist == False:
                        transferred_taxes.append({'cfdi:Traslado': {
                            'id': tax.id,
                            "Base": basee,
                            # "Base": '%.*f' % (line.currency_id.decimal_places, float(amount) / float(tasa) if tax.amount_type == 'fixed' else tax_dict.get('base', line.price_subtotal)),
                            'Importe': round(amount, 2),
                            'Impuesto': name_transferred,
                            'TipoFactor': type_transferred,
                            'TasaOCuota': '%.6f' % abs(tax.amount if tax.amount_type == 'fixed' else (tax.amount / 100.0))
                        }})
                        print("______________________________", transferred_taxes)
                else:
                    total_withhold += amount
                    name_withhold = tax_name(tax.mapped('invoice_repartition_line_ids.tag_ids')[0].name if tax.mapped(
                        'invoice_repartition_line_ids.tag_ids') else '')

                    exist = False
                    for wt in withhold_taxes:
                        if tax.id == wt['cfdi:Retencion']['id']:
                            exist = True
                            wt['cfdi:Retencion']['Importe'] += amount
                    if exist == False:
                        withhold_taxes.append({'cfdi:Retencion': {
                            'id': tax.id,
                            'Importe': round(amount, 2),
                            'Impuesto': tax.l10n_xma_tax_type_id.code
                        }})
        for tt in transferred_taxes:
            del tt['cfdi:Traslado']['id']
            tt['cfdi:Traslado']['Importe'] = round(tt['cfdi:Traslado']['Importe'], self.currency_id.decimal_places)
            tt['cfdi:Traslado']['Base'] = round(tt['cfdi:Traslado']['Base'], self.currency_id.decimal_places)
        for wt in withhold_taxes:
            del wt['cfdi:Retencion']['id']
            wt['cfdi:Retencion']['Importe'] = round(wt['cfdi:Retencion']['Importe'], self.currency_id.decimal_places)
        def get_discount(l, d): return (
                '%.*f' % (int(d), subtotal_wo_discount(l) - l.price_subtotal)) if l.discount else False
        total_discount = sum([float(get_discount(p, 2))
                                for p in self.invoice_line_ids])
        amount_untaxed = '%.*f' % (2, sum([subtotal_wo_discount(p)
                                               for p in self.invoice_line_ids]))
        
        cfdi_impuestos = {}
        # if total_transferred != 0 or total_withhold != 0:
        #     continue
        cfdi_impuestos = {
            'TotalImpuestosTrasladados': total_transferred if total_transferred > 0 else 0,
            'cfdi:Retenciones': withhold_taxes,
            'cfdi:Traslados': transferred_taxes
        }
        if total_withhold:
            cfdi_impuestos['TotalImpuestosRetenidos'] = total_withhold
        condiciones = str(self.invoice_payment_term_id.name).replace('|', ' ')
        document_type = 'ingreso' if self.move_type == 'out_invoice' else 'egreso'
        date = self.invoice_date or fields.Date.today()
        company_id = self.company_id
        ctx = dict(company_id=company_id.id, date=date)
        mxn = self.env.ref('base.MXN').with_context(ctx)
        invoice_currency = self.currency_id.with_context(ctx)
        print("amount_untaxed", amount_untaxed)
        print("total_discount", total_discount)
        print("total_transferred", total_transferred)
        print("total_withhold", total_withhold)
        descuento = float('%.*f' % (2, total_discount) if total_discount else 0)
        json_m = {
            'xmlns:cartaporte31': 'http://www.sat.gob.mx/CartaPorte31',
            'xmlns:cfdi': 'http://www.sat.gob.mx/cfd/4',
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:schemaLocation': 'http://www.sat.gob.mx/cfd/4 http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd http://www.sat.gob.mx/CartaPorte31 http://www.sat.gob.mx/sitio_internet/cfd/CartaPorte/CartaPorte31.xsd',
            'Version': '4.0',
            'Fecha': time_invoice.strftime('%Y-%m-%dT%H:%M:%S'),
            'Folio': self.sequence_number,
            'Serie': self.sequence_prefix,
            'Sello': '',
            'FormaPago': self.l10n_xma_payment_form.code,
            'NoCertificado': '',
            'Certificado': '',
            'CondicionesDePago':condiciones.strip()[:1000] if self.invoice_payment_term_id else False,
            'SubTotal': float(self.amount_untaxed + descuento),
            'Descuento': '%.*f' % (2, total_discount) if total_discount else 0,
            'Moneda': self.currency_id.name,
            'TipoCambio':('%.6f' % (invoice_currency._convert(1, mxn, self.company_id, self.invoice_date or fields.Date.today(), round=False))) if self.currency_id.name != 'MXN' else {},
            'Total': '%0.*f' % (2, float(amount_untaxed) - float(float('%.*f' % (2, total_discount)) or 0) + (
                    float(total_transferred) or 0) - (float(total_withhold) or 0)),
            'TipoDeComprobante': document_type[0].upper(),
            'Exportacion': '01',
            'MetodoPago':  self._einvoice_edi_get_payment_policy(),
            'LugarExpedicion': self.company_id.zip or  self.company_id.partner_id.zip,
            'cfdi:CfdiRelacionados': [], 
            'cfdi:Emisor': {
                'Rfc': self.company_id.vat,
                'Nombre': self.company_id.name,
                'RegimenFiscal':self.company_id.partner_id.l10n_xma_taxpayer_type_id.code
            },
            'cfdi:Receptor': {
                'Rfc': self.partner_id.vat,
                'Nombre': self.partner_id.name,
                'UsoCFDI': self.l10n_xma_use_document_id.code,
                'DomicilioFiscalReceptor':self.partner_id.zip,
                'RegimenFiscalReceptor': self.partner_id.l10n_xma_taxpayer_type_id.code
            },
            'cfdi:Conceptos': conceptos,
            'cfdi:Impuestos': cfdi_impuestos
        }

        json_m['xmlns:cartaporte31']="http://www.sat.gob.mx/CartaPorte31"
        json_m['cfdi:Complemento']={
                    'cartaporte31:CartaPorte' : self.edi_sign_transfer_invoice() 
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
            json_m['cfdi:Complemento']['cartaporte31:CartaPorte']['cartaporte31:Mercancias']['cartaporte31:Autotransporte'].update({
                'cartaporte31:Remolques':remolque
            })
        return json_m

    def _get_FechaOrig(self):
        for rec in self:

            date = rec.l10n_xma_goods_entry.strftime('%Y-%m-%dT%H:%M:%S')

            return date


    def _get_FechaTimb(self):
        for rec in self:
            date = '2023-02-10T10:30:21'

            return date
    
    def get_company(self):
        company_id = self.env['res.company'].sudo().search([("company_name", "!=", "")], limit=1)
        if not company_id:
            company_id = self.env['res.company'].sudo().search([], limit=1)

        return company_id

    def l10n_xma_generate_edelivery(self):
        for rec in self:
            print("+++")
            xml_json_mx = rec.generate_json_l10n_mx_delivery_mx()
            json_complete = {
                "id":rec.id,
                "uuid_client":rec.company_id.uuid_client,
                "data":xml_json_mx,
                "rfc":rec.company_id.vat,
                "prod": 'NO' if rec.company_id.l10n_xma_test else 'SI',
                "type": 'F',
                "pac_invoice": rec.company_id.l10n_xma_type_pac,
            }
            xml_json = {"MX": json_complete}
            company = rec.get_company()
            uuid = company.company_name
            rfc = rec.company_id.partner_id.vat
            country = company.partner_id.country_id.code.lower()
            xml_json = {"from":uuid, "data":xml_json}
            mqtt_client = MqttClient("api.xmarts.com", 1883, prefix=f"uuid/{uuid}/rfc/{rfc}/country/{country}/", encryption_key=company.key)
            # xml_json = json.dumps(xml_json)
            print(xml_json)
            mqtt_client.send_message_serialized(
                [xml_json],
                f"uuid/{uuid}/rfc/{rfc}/country/{country}/stamp", 
                valid_json=True, 
                secure=True
            )
            print(xml_json)
            # asyncio.run(self.async_send_message(xml_json.encode('utf-8').decode('unicode_escape')))

            self.env.cr.commit()
            time.sleep(1) 
            return True


    def _l10n_mx_edi_get_signed_cfdi_data(self):
        self.ensure_one()
        if self.l10n_xma_timbre == True:
            return base64.decodebytes(self.l10n_xma_invoice_cfdi)
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
            'cadena': self.l10n_xma_cadena_original,
            'certificate_number': cfdi_node.get('noCertificado', cfdi_node.get('NoCertificado')),
            'certificate_sat_number': tfd_node is not None and tfd_node.get('NoCertificadoSAT'),
            'expedition': cfdi_node.get('LugarExpedicion'),
            'fiscal_regime': cfdi_node.Emisor.get('RegimenFiscal', ''),
            'emission_date_str': cfdi_node.get('fecha', cfdi_node.get('Fecha', '')).replace('T', ' '),
            'stamp_date': tfd_node is not None and tfd_node.get('FechaTimbrado', '').replace('T', ' '),
        }

    ##------------------------------------##