from odoo import fields, models, api 

class BuyPortfolioWizard(models.TransientModel):
    _name = 'investing.portfolio.buy.wizard'
    _description ='Wizard in portfolio for buy action'

    company_id = fields.Many2one('inversting.comapny', string='caompany_id', required=True)
    date = fields.Datetime(string='date', required=True) 
    shares = fields.Float(string='shares', required=True)
    price = fields.Float(string='price', required=True)
    


