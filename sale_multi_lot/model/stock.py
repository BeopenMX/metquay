from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from odoo.exceptions import UserError

class StockMove(models.Model):
    _inherit = 'stock.move'

    assign_lot = fields.Boolean(string='Assign Lot')
    lot_id = fields.Many2many('stock.production.lot', string='N/S o Lote', copy=False)
    move_from_sale = fields.Boolean(string='Assign Lot')

    def _update_reserved_quantity(self, need, available_quantity, location_id, lot_id=None, package_id=None, owner_id=None, strict=True):
        self.ensure_one()

        if not lot_id:
            lot_id = self.env['stock.production.lot']
        if not package_id:
            package_id = self.env['stock.quant.package']
        if not owner_id:
            owner_id = self.env['res.partner']

        taken_quantity = min(available_quantity, need)
        if not strict:
            taken_quantity_move_uom = self.product_id.uom_id._compute_quantity(taken_quantity, self.product_uom, rounding_method='DOWN')
            taken_quantity = self.product_uom._compute_quantity(taken_quantity_move_uom, self.product_id.uom_id, rounding_method='HALF-UP')

        quants = []

        if self.product_id.tracking == 'serial':
            rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            if float_compare(taken_quantity, int(taken_quantity), precision_digits=rounding) != 0:
                taken_quantity = 0

        try:
            if not float_is_zero(taken_quantity, precision_rounding=self.product_id.uom_id.rounding):
                if self.product_id.tracking == 'serial' and taken_quantity >=1 and need>=1:
                    for lot in self.env['stock.production.lot'].browse(self.lot_id.ids):
                        if lot:
                            quant = self.env['stock.quant']._update_reserved_quantity(
                                self.product_id, location_id, 1, lot_id=lot,
                                package_id=package_id, owner_id=owner_id, strict=strict
                            )
                            taken_quantity-=1
                            quants.append(quant[0])
                else:
                    quants = self.env['stock.quant']._update_reserved_quantity(
                        self.product_id, location_id, taken_quantity, lot_id=lot_id,
                        package_id=package_id, owner_id=owner_id, strict=strict
                    )

        except UserError:
            taken_quantity = 0

        for reserved_quant, quantity in quants:
            to_update = self.move_line_ids.filtered(lambda ml: ml._reservation_is_updatable(quantity, reserved_quant))
            if to_update:
                to_update[0].with_context(bypass_reservation_update=True).product_uom_qty += self.product_id.uom_id._compute_quantity(quantity, to_update[0].product_uom_id, rounding_method='HALF-UP')
            else:
                if self.product_id.tracking == 'serial':
                    for i in range(0, int(quantity)):
                        self.env['stock.move.line'].create(self._prepare_move_line_vals(quantity=1, reserved_quant=reserved_quant))

                else:
                    self.env['stock.move.line'].create(self._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant))
        return taken_quantity

    def create_stock_move_line(self):
        for move in self:
            if move.move_line_ids:
                if move.sale_line_id and move.sale_line_id.lot_ids:
                    move.move_line_ids.unlink()
                    for lot_id in move.sale_line_id.lot_ids:
                        vals = {
                                'move_id': move.id,
                                'product_id': move.product_id.id,
                                'product_uom_id': move.product_uom.id,
                                'location_id': move.location_id.id,
                                'location_dest_id': move.location_dest_id.id,
                                'picking_id': move.picking_id.id,
                                'lot_id':lot_id.id,
                            #    'product_uom_qty':lot_id.product_qty,
                                'qty_done':lot_id.product_qty
                                }
                        self.env['stock.move.line'].create(vals)
     
    def action_confirm(self):
         for move in self:
            move.create_stock_move_line()
            self._action_assign()
         res = super(StockMove, self).action_confirm()
         return res

