from odoo import api, fields, models, _


class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    lot_ids = fields.Many2many('stock.production.lot',string='Lot', copy=False)