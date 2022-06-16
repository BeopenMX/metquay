from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _action_confirm(self):

        if self.type_id.name in ['Calibracion', 'Reparacion']:
            pass
        else:
            order_line_lots = [x.lot_ids.ids for x in self.order_line]
            used_lots = [id for ids in order_line_lots for id in ids]
            remain_lot_qty={}
            for line in self.order_line:
                if not line.lot_ids:
                    lot_id = self.env['stock.production.lot'].search([('product_id', '=', line.product_id.id)])
                    lot = lot_id.filtered(lambda lot: lot.product_qty > 0 and lot.product_id.id == line.product_id.id)
                    quant_obj = self.env['stock.quant'].search(
                        [('location_id.usage', '=', 'internal'), ('lot_id', 'in', lot.ids)])
                    quant_objs2 = self.env['stock.quant'].search(
                        [('location_id.id', '=', self.warehouse_id.lot_stock_id.id), ('lot_id', 'in', lot.ids)]).ids
                    quant_id = quant_obj.filtered(
                        lambda qt: qt.reserved_quantity != qt.quantity and qt.quantity != 0 and qt.id in quant_objs2)
                    ids = quant_id.mapped('lot_id').ids
                    remain = line.product_uom_qty
                    new_ids = []
                    remaining_qty_before_order = quant_id.mapped(lambda qt:(str(qt.lot_id.id),qt.quantity- qt.reserved_quantity) if qt.reserved_quantity>0 else False)
                    used_lots_before_order=[lote for lote in remaining_qty_before_order if lote]
                    remain_lot_qty.update(dict(used_lots_before_order))

                    if line.product_id.tracking == 'serial':
                        for ids_qty in  lot.filtered(
                            lambda x: x.id in ids and line.product_uom_qty > 0 and x.id not in used_lots):
                            if remain >= 1:
                                new_ids.append(ids_qty.id)
                                used_lots.append(ids_qty.id)
                                remain -= 1
                            else:
                                break
                        line.update({'lot_ids': [(6, 0, new_ids)]})

                    elif line.product_id.tracking == 'lot':
                        for ids_qty in lot.filtered(
                            lambda x: x.id in ids and line.product_uom_qty > 0 and x.id not in used_lots):
                            if remain >= 1:
                                if str(ids_qty.id) not in remain_lot_qty:
                                    if ids_qty.product_qty <remain:
                                        new_ids.append(ids_qty.id)
                                        used_lots.append(ids_qty.id)
                                        remain -= ids_qty.product_qty
                                    else:
                                        remain_lot_qty[str(ids_qty.id)]=ids_qty.product_qty - remain
                                        new_ids.append(ids_qty.id)
                                        remain=0
                                else:
                                    if remain_lot_qty[str(ids_qty.id)] <remain:
                                        new_ids.append(ids_qty.id)
                                        used_lots.append(ids_qty.id)
                                        remain -= remain_lot_qty[str(ids_qty.id)]
                                    else:
                                        new_ids.append(ids_qty.id)
                                        remain_lot_qty[str(ids_qty.id)]=ids_qty.product_qty - remain
                                        remain = 0
                            else:
                                break
                        line.update({'lot_ids': [(6, 0, new_ids)]})
        res = super(SaleOrder, self)._action_confirm()
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('lot_ids', 'product_id')
    def _get_related_product_lot(self):
        for line in self:
            lot_id = self.env['stock.production.lot'].search([('product_id', '=', line.product_id.id)])
            lot = lot_id.filtered(lambda lot: lot.product_qty > 0 and lot.product_id.id == line.product_id.id)
            quant_obj = self.env['stock.quant'].search(
                [('location_id.usage', '=', 'internal'), ('lot_id', 'in', lot.ids)])
            quant_id = quant_obj.filtered(lambda qt: qt.reserved_quantity == 0.00 and qt.quantity != 0)
            lot_ids = quant_id.mapped('lot_id').ids
            line.related_lot_ids = [(6, 0, lot_ids)]

    lot_ids = fields.Many2many('stock.production.lot', string='Lot', copy=False)

    related_lot_ids = fields.Many2many('stock.production.lot', 'stock_production_lot_order_line', 'lot_id',
                                       'order_line_id', string='Lot', compute='_get_related_product_lot')

 
 
    def _prepare_invoice_line(self):

        res = super(SaleOrderLine, self)._prepare_invoice_line()
        if self.lot_ids:
            res.update({'lot_ids': [(6, 0, self.lot_ids.ids)]})
        return res

    def _prepare_procurement_values(self, group_id=False):
        res = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        if self.calibracion:
            res['lot_id'] = [(6, 0, self.lot_ids.ids)]
        return res


class StockRuleInherit(models.Model):
    _inherit = 'stock.rule'

    @api.model
    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, company_id,
                               values):
        res = super(StockRuleInherit, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id,
                                                                   name, origin, company_id, values)
        res['lot_id'] = values.get('lot_id')

        return res

    # @api.onchange('product_id')
    # def product_id_change(self):
    #   result = super(SaleOrderLine, self).product_id_change()
    #  lot_id = self.env['stock.production.lot'].search([('product_id', '=', self.product_id.id)])
    # lot = lot_id.filtered(lambda lot: lot.product_qty > 0 and lot.product_id.id == self.product_id.id)
    # quant_obj = self.env['stock.quant'].search([('location_id.usage', '=', 'internal'), ('lot_id', 'in', lot.ids)])
    # quant_id = quant_obj.filtered(lambda qt: qt.reserved_quantity == 0.00 and qt.quantity != 0)
    # result['domain'].update({'lot_ids': [('id', 'in', quant_id.mapped('lot_id').ids)]})
    # return result
