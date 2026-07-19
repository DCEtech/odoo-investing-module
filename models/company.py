from odoo import models, fields, api
import logging
from ..services.yfinance_service import YFinanceService

_logger = logging.getLogger(__name__)

class InvestingCompany(models.Model):
    _name = 'investing.company'
    _description = 'Investing Company'

    name = fields.Char(string="Company Name", required=True)
    ticker = fields.Char(string="Ticker", required=True)
    sector = fields.Char(string="Sector")
    currency = fields.Char(string="Currency")
    current_price = fields.Float(string="Current Price")
    last_update = fields.Datetime(string="Last Update")

    def action_sync_data(self):
        service = YFinanceService()
        data = service.get_company_data(self.ticker)
        price = data.get('currentPrice') or data.get('regularMarketPrice') or 0.0
        self.write({
            'current_price': price,
            'sector': data.get('sector', ''),
            'currency': data.get('currency', ''),
            'last_update': fields.Datetime.now(),
        })
        history = service.get_price_history(self.ticker)
        self.env['investing.price.history'].search([('company_id', '=', self.id)]).unlink()
        records = []
        for date, row in history.iterrows():
            records.append({
                'company_id': self.id,
                'date': date.date(),
                'close_price': row['Close'],
                'volume': row['Volume'],
            })
        self.env['investing.price.history'].create(records)


    @api.model
    def action_sync_all_companies(self): 
        companies = self.search([])
        for company in companies:
            try: 
                company.action_sync_data()
            except Exception as e:
                _logger.error("Failed to sync comapny %s: %s", company.ticker, str(e))
    
