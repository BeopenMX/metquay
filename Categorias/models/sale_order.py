from odoo import api, fields, models, _

class Product_category(models.Model):
    _inherit = 'product.template'
    category = fields.Many2one('categorias',string='Cat. Metquay',readonly=0)

class Sale_Order_Category(models.Model):
    _inherit = 'sale.order.line'
    category = fields.Many2one('categorias',string='Cat Metquay',readonly=0, related='product_id.product_tmpl_id.category')