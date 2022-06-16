from odoo import api, fields, models, _


class stock_production_lot(models.Model):
    _inherit = 'stock.production.lot'
    _rec_name = 'name'


    is_used= fields.Boolean(string="is_used")
    def name_get(self):
        res = []
        for record in self:
            lot_name = record.name or ''
            lot_with_qty = lot_name + "(" + str(record.product_qty) + " "+record.product_uom_id.name + ")"  
            res.append((record.id,lot_with_qty))
        return res
