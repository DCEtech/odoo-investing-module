from odoo import models, fields

class PriceHistory(models.Model):
    _name = 'investing.price.history'
    _description = 'Investing Price History'
    _order = 'date desc'
    
    company_id = fields.Many2one('investing.company', string='Company', required=True)
    date = fields.Date(string='Date', required=True)
    close_price = fields.Float(string='Close Price')
    volume = fields.Float(string='Volume')
    