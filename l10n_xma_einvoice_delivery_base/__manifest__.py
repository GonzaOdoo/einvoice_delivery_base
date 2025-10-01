# -*- coding: utf-8 -*-
{
    'name': "Delivery Electronic Invoice Base.",

    'summary': """
        Este módulo le  crea todos los modelos y campos adicionales que se necesitan para la generación de
         un comprobante electrónico para entregas de mercancias .""",

    'description': """
    """,

    'author': "Xmarts Méxicoy",
    'website': "https://www.xmarts.com",
    'category': 'Accounting/Accounting',
    'version': '18.0.0.0',
    'depends': ['account','stock','l10n_xma_einvoice','xma_core','base_address_extended'],
    'data': [
        'security/ir.model.access.csv',
        'data/l10n.xma.permission.type.csv',
        'data/l10n.xma.trailer.type.csv',
        'data/l10n.xma.vehicle.type.csv',
        'data/l10n_xma.use.document.csv',

        'data/l10n_xma_condiciones_especiales.xml',
        'data/l10n_xma_documento_aduanero.xml',
        'data/l10n_xma_forma_farmaceutica.xml',
        'data/l10n_xma_regimen_aduanero.xml',
        'data/l10n_xma_registro_istmo.xml',
        'data/l10n_xma_sector_cofepris.xml',
        'data/l10n_xma_tipo_materia.xml',
        'data/l10n_xma_cve_transporte.xml',
    ],
}
