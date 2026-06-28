from odoo import models, fields, api

class Portfolio(models.Model):
    _name = 'investing.portfolio'
    _description = 'Investing Portfolio'
    
    company_id = fields.Many2one('investing.company', string='Company', required=True)
    shares = fields.Float(string='Number of Shares')
    purchase_price = fields.Float(string='Purchase Price')
    current_value = fields.Float(string='Current Value', compute='_compute_current_value')
    profit_loss = fields.Float(string='Profit / Loss', compute='_compute_profit_loss')
    roi = fields.Float(string='ROI (%)', compute='_compute_roi', digits=(10, 2))
    
    @api.model_create_multi
    def create(self, vals_list):
        result = self.env['investing.portfolio']
        for vals in vals_list: 
            existing = self.search([('company_id', '=', vals.get('company_id'))], limit=1)
            if existing: 
                new_shares = vals.get('shares', 0)
                new_price = vals.get('purchase_price', 0)
                total_shares = existing.shares + new_shares
                avg_price = (
                    (existing.shares * existing.purchase_price + new_shares * new_price) / total_shares
                    if total_shares else 0
                ) 
                existing.write({'shares': total_shares, 'purchase_price': avg_price})
                result |= existing
            else: 
                result |= super().create([vals])
        return result


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

