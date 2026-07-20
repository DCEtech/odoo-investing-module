from odoo import models, fields, api

class SellPortfolioWizard(models.TransientModel): 
    _name = 'investing.portfolio.sell.wizard'
    _description = 'Wizard in portfolio for sell action'

    portfolio_id = fields.Many2one('investing.portfolio', string= 'Portfolio', required = True)
    shares = fields.Float(string = 'number of shares', required=True)
    price = fields.Float(string = 'price', required = True)  
    date  = fields.Datetime(string = 'date', required = True)
    
    def action_confirm_sell(self):
        self.ensure_one()
        self.portfolio_id.sell(self.shares, self.price, self.date)