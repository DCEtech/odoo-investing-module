from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero

# Precision used to compare share quantities (supports fractional crypto units).
QTY_DIGITS = 8

class Portfolio(models.Model):
    _name = 'investing.portfolio'
    _description = 'Investing Portfolio'
    
    company_id = fields.Many2one('investing.company', string='Company', required=True)
    date = fields.Datetime(string='date time', required=True)
    shares = fields.Float(string='Number of Shares')
    purchase_price = fields.Float(string='Purchase Price')
    current_value = fields.Float(string='Current Value', compute='_compute_current_value')
    profit_loss = fields.Float(string='Profit / Loss', compute='_compute_profit_loss')
    roi = fields.Float(string='ROI (%)', compute='_compute_roi', digits=(10, 2))
    
    @api.model_create_multi
    def create(self, vals_list):
        result = self.env['investing.portfolio']
        for vals in vals_list: 

            new_buy = self.env['investing.buy.sell.history']
    
            new_buy.create([{
                'company_id': vals.get('company_id'),
                'date': vals.get('date'),
                'order_type': 'buy',
                'shares': vals.get('shares'),
                'price': vals.get('purchase_price'),
                'remaining_shares': vals.get('shares')
            }])

            existing = self.search([('company_id', '=', vals.get('company_id'))], limit=1)
            if existing: 
                new_shares = vals.get('shares', 0)
                new_price = vals.get('purchase_price', 0)
                total_shares = existing.shares + new_shares
                avg_price = (
                    (existing.shares * existing.purchase_price + new_shares * new_price) / total_shares
                    if total_shares else 0
                ) 
                existing.write({'shares': total_shares, 'purchase_price': avg_price, 'date': vals.get('date')})
                result |= existing
            else: 
                result |= super().create([vals])
        
        return result

    def sell(self, shares: float, price: float, date) -> float:
        """Sell ``shares`` consuming buy lots in FIFO order (art. 37.2 LIRPF).

        Only lots acquired on or before ``date`` can be consumed, and the
        sale is rejected if it exceeds the shares held at that date.

        :return: realized profit of the sale.
        """
        self.ensure_one()
        if float_compare(shares, 0.0, precision_digits=QTY_DIGITS) <= 0:
            raise UserError(self.env._("The number of shares to sell must be positive."))
        if price < 0:
            raise UserError(self.env._("The sale price cannot be negative."))
        History = self.env["investing.buy.sell.history"]
        lots = History.search(
            [
                ("company_id", "=", self.company_id.id),
                ("order_type", "=", "buy"),
                ("remaining_shares", ">", 0),
                ("date", "<=", date),
            ],
            order="date asc, id asc",  # deterministic tie-break for same-time buys
        )
        available = sum(lots.mapped("remaining_shares"))
        if float_compare(shares, available, precision_digits=QTY_DIGITS) > 0:
            raise UserError(
                self.env._(
                    "You cannot sell %(shares)s shares of %(asset)s: only %(available)s "
                    "were held on that date.",
                    shares=shares,
                    asset=self.company_id.display_name,
                    available=available,
                )
            )

        pending = shares
        profit = 0.0
        for lot in lots:
            if float_is_zero(pending, precision_digits=QTY_DIGITS):
                break
            consumed = min(lot.remaining_shares, pending)
            profit += (price - lot.price) * consumed
            remaining = lot.remaining_shares - consumed
            # Avoid "ghost" lots of 1e-15 shares caused by float arithmetic.
            lot.remaining_shares = (
                0.0 if float_is_zero(remaining, precision_digits=QTY_DIGITS) else remaining
            )
            pending -= consumed

        History.create(
            [
                {
                    "company_id": self.company_id.id,
                    "date": date,
                    "order_type": "sell",
                    "shares": shares,
                    "price": price,
                    "realized_profit": profit,
                }
            ]
        )

        open_lots = History.search(
            [
                ("company_id", "=", self.company_id.id),
                ("order_type", "=", "buy"),
                ("remaining_shares", ">", 0),
            ]
        )
        held = sum(open_lots.mapped("remaining_shares"))
        cost = sum(lot.price * lot.remaining_shares for lot in open_lots)
        self.write(
            {
                "shares": held,
                "purchase_price": cost / held if held else 0.0,
                "date": date,
            }
        )
        return profit

    def action_open_sell_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'investing.portfolio.sell.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_portfolio_id': self.id} 
        }
         
    @api.depends('shares', 'company_id.current_price')
    def _compute_current_value(self):    
        for record in self:
            record.current_value = record.shares * record.company_id.current_price
    
    @api.depends('shares', 'current_value', 'purchase_price')
    def _compute_profit_loss(self):
        for record in self: 
            record.profit_loss = record.current_value - (record.shares * record.purchase_price)
    
    @api.depends('shares', 'profit_loss', 'purchase_price')
    def _compute_roi(self):
        for record in self: 
            cost = record.shares * record.purchase_price
            record.roi = (record.profit_loss / cost) * 100 if cost else 0.0

    