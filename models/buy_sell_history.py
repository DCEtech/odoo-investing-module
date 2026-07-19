from odoo import models, fields, api 

class BuySellHistory(models.Model): 
    _name = "investing.buy.sell.history"
    _description = "Historical buy/sell"

    company_id = fields.Many2one('investing.company', string='Company', required=True)
    date = fields.Datetime(string='Date time', required=True)
    order_type = fields.Selection([('buy', 'Buy'), ('sell', 'Sell')], string='Order Type', required=True)
    shares = fields.Float(string='Shares')
    price = fields.Float(string='Price per Share', aggregator=None)
    remaining_shares = fields.Float(string='Remaining Shares')
    realized_profit = fields.Float(string='Realized Profit')



    
