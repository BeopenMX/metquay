{
    'name': 'sale_multi_Lot',
    'version': '13.1',
    'category': 'Sales Management',
    'summary': 'Modulo para seleccionar lotes desde la venta. reservandolos al momento de seleccionarlos.',
    'author': 'Xmarts',
    'depends': ['sale_stock','stock','account'],
    'data': [
        'views/sale_view.xml',
        'views/account_invoice.xml',
        'report/sale_order_report.xml',
        'report/invoice_order_report.xml',

    ],
    'qweb': [],
    'css': [],
    'js': [],
    'images': [
        'static/description/so_03.png',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
