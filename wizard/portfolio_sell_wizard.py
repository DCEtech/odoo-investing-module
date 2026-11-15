from odoo import api, fields, models


class SellPortfolioWizard(models.TransientModel):
    _name = "investing.portfolio.sell.wizard"
    _description = "Wizard in portfolio for sell action"

    portfolio_id = fields.Many2one("investing.portfolio", required=True)
    available_shares = fields.Float(
        related="portfolio_id.shares", string="Available Shares"
    )
    shares = fields.Float(string="Number of Shares", required=True)
    price = fields.Float(required=True)
    date = fields.Datetime(required=True, default=fields.Datetime.now)

    @api.onchange("portfolio_id")
    def _onchange_portfolio_id(self) -> None:
        # Suggest the last synced market price; the user can still override it.
        if self.portfolio_id and not self.price:
            self.price = self.portfolio_id.company_id.current_price

    def action_confirm_sell(self) -> None:
        self.ensure_one()
        self.portfolio_id.sell(self.shares, self.price, self.date)
