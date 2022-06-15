# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    # App information

    'name': 'Create Customer Using API',
    'version': '12.0',
    'category': 'Website',
    'summary': 'Connect, Integrate & Manage your Customer data from Odoo',
    'license': 'OPL-1',

    # Dependencies

    'depends': ['base','sale_stock','sale'],

    # Views

    'data': ['views/ir_cron.xml',
             'views/api_configuration.xml',
             'security/ir.model.access.csv',
             'views/res_user.xml',
             'views/sale_order.xml',
             'views/product_product.xml',
             'views/stock_picking.xml',

             ],

    # Odoo Store Specific

    'images': ['static/description/icon.png'],

    # Author

    'author': 'Xmarts',
    'website': '',
    'maintainer': '',

    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    

}
