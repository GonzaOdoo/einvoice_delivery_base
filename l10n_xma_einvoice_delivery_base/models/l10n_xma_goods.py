# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class L10nXmaGoods(models.Model):
    _name = "l10n.xma.goods"
    _description = "Mercancias."
    _order = 'id'
    _rec_names_search = ['name']

    move_id = fields.Many2one(
        'account.move',
        string="Carta porte",
    )

    stock_move_line_id = fields.Many2one(
        'stock.move',
        string="Movimiento de almacen",
    )

    product_code_id = fields.Many2one(
        'l10n_xma.productcode',
        string="Producto Transportado",
    )    
    description = fields.Char(
        string='Descripción',
        readonly=False,
        store=True
        
    )    
    quantity = fields.Float(
        string='Cantidad',
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string="Unidad de medida",
    )
    weight = fields.Float(
        string='Peso',
        digits=(12, 3)
    )
    goods_value = fields.Float(
        string='Valor de la mercancia',
        digits=(12, 3)
    )
    currency_id = fields.Many2one(
        'res.currency',
        string="Moneda",
    )
    l10n_sing = fields.Boolean(copy=False)

    l10n_xma_is_hazaudous_material = fields.Selection(
        [('si', "Si"),("noo", "No (Opcional)"), ('no', 'No')],   
        default='no',        
        string="Es Material Peligroso",
    )
    l10n_xma_hazaudous_material_id = fields.Many2one(
        'l10n_xma.hazardous.material',
        string="Tipo de embalaje"
    )
    l10n_xma_tipo_embalaje_id = fields.Many2one(
        'l10n.xma.tipo.embalaje',
        string="Tipo de embalaje"
    )    
    descripcion_embalaje = fields.Char(
        string='Descripción embalaje',        
        related='l10n_xma_tipo_embalaje_id.name',
        
        readonly=False 
    )
    
    is_control_cofepris = fields.Boolean(
        string='Controlado por la cofrepis',
    )    
    l10n_xma_sector_cofepris_id_id = fields.Many2one(
        string='Sector Cofrepis',
        comodel_name='l10n.xma.sector.cofepris',
    )    
    nombre_ingrediente_activo = fields.Char(
        string='Ingrediente activo',
        help="Nombre común del ingrediente activo de los precursores, químicos de uso dual, plaguicidas o fertilizantes "
             "que se trasladan a través de los distintos medios de transporte"
    )
    nomquimico = fields.Char(
        string='Sustancia activa',
        help="Nombre de la sustancia activa de los precursores, químicos de uso dual o sustancias tóxicas que se traslada "
              "a través de los distintos medios de transporte."
    )
    dengenprod = fields.Char(
        string='Farmaco o sutancia activa',
        help="Fármaco o la sustancia activa del medicamento, psicotrópico o estupefaciente que se traslada a "
             "través de los distintos medios de transporte."
    )    
    dendistprod = fields.Char(
        string='Nombre comercial o marca',
        help="Marca con la que se comercializa el producto o nombre que le asigna el laboratorio o "
             "fabricante a sus especialidades farmacéuticas con el fin de distinguirlas de otras similares del medicamento, "
             "psicotrópico o estupefaciente que se traslada a través de los distintos medios de transporte."
    )
    
    fabricante = fields.Char(
        string='Nombre del fabricante',
        help="Nombre o razón social del establecimiento que realiza la fabricación o manufactura del medicamento, "
             "precursor, químico de uso dual, psicotrópico o estupefaciente que se traslada a través de los distintos medios de transporte."
    )    
    fecha_caducidad = fields.Date(
        string='Fecha de caducidad',
        help="Fecha de caducidad del medicamento, psicotrópico o estupefaciente; o para expresar la fecha "
             "de reanálisis del precursor o químico de uso dual que se traslada a través de los distintos medios de transporte."
    )
    lote_medicamento = fields.Char(
        string='Lote del medicamento',
        help="Denominación que identifica y confiere trazabilidad del medicamento, precursor, químico de uso dual, "
             "psicotrópico o estupefaciente elaborado en un ciclo de producción, bajo condiciones equivalentes de operación y durante un periodo."
    )    
    forma_farmaceutica_id = fields.Many2one(
        string='Forma farmaceutica',
        comodel_name='l10n.xma.forma.farmaceutica',
        help="Forma farmacéutica o mezcla del medicamento, precursor, químico de uso dual, psicotrópico o estupefaciente "
             "que presenta ciertas características físicas para su adecuada dosificación, conservación y administración"
    )
    condiciones_especiales_id = fields.Many2one(
        string='Condiciones especiales',
        comodel_name='l10n.xma.condiciones.especiales',
        help="Condición en la cual es necesario mantener el medicamento, precursor, químico de uso dual, psicotrópicos o estupefacientes durante el traslado y almacenamiento."
    )    
    regsanfolauto = fields.Char(
        string='No. de autorización',
        help="Registro sanitario o folio de autorización con el que cuenta la empresa para el traslado del medicamento, psicotrópico o estupefaciente"
    )
    permiso_importacion = fields.Char(
        string='Permiso de importación',
        help="Folio del permiso de importación con el que cuenta el medicamento, precursor, químico de uso dual, psicotrópico o estupefaciente"
    )    
    folimpvucem = fields.Char(
        string='No. VUCEM',
        help="Número de folio de importación VUCEM para la identificación del documento, para el traslado de medicamentos, "
             "precursores o químicos de uso dual, sustancias tóxicas, plaguicidas o fertizantes."

    )    
    numcas = fields.Char(
        string='Número Chemical Abstracs Service',
        help="Número Chemical Abstracts Service (CAS) con el que se identifica el compuesto químico de la sustancia tóxica."
    )
    razsocempimp = fields.Char(
        string='Razón Social Empresa Importadora',
        help="Nombre o razón social de la empresa importadora de las sustancias tóxicas."
    )
    num_regsanplag_cofepris = fields.Char(
        string='No. Registro Sanitario',
        help="Número de registro sanitario para plaguicidas o fertilizantes cuya importación, comercialización y uso están "
             "permitidos en México, mismo que emite la Comisión Intersecretarial para el Control del Proceso y Uso de Plaguicidas, "
             "Fertilizantes y Sustancias Tóxicas (CICLOPLAFEST)."
    )
    datos_fabricante = fields.Char(
        string='Datos del fabricante',
        help="País y nombre o razón social de quien produce o fabrica el ingrediente activo del plaguicida o fertilizante."
    )
    datos_formulador = fields.Char(
        string='Datos del formulador',
        help="País y nombre o razón social de quien formula el ingrediente activo del plaguicida o fertilizante."
    )    
    datos_maquilador = fields.Char(
        string='Datos del maquilador',
        help="País y nombre o razón social de quien maquila el ingrediente activo del plaguicida o fertilizante."
    )    
    uso_autorizado = fields.Char(
        string='Uso autorizado',
        help="Uso autorizado del plaguicida o fertilizante de acuerdo a la regulación del país."
    )
    documento_aduanero_id = fields.Many2one(
        string='Tipo de documento',
        comodel_name='l10n.xma.documento.aduanero',
    )
    numpedimento = fields.Char(
        string='No. de Pedimento',
    )
    rfcimpo = fields.Char(
        string='RFC Importador',
    )

    l10n_xma_tipo_materia = fields.Many2one("l10n.xma.tipo.materia", string="Tipo Materia")
    