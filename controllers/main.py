from odoo import http
from odoo.http import request 

class InvestingController(http.Controller):

    @http.route('/investing/companies', type='jsonrpc',
    auth='bearer', methods=['GET'])
    def list_companies(self):
        companies = request.env['investing.company'].search([])
        return companies.read(['id', 'name', 'ticker', 'current_price'])

    @http.route('/investing/company/<int:company_id>', type='jsonrpc', 
    auth='bearer', methods=['GET'])
    def get_company(self, company_id): 
        company = request.env['investing.company'].browse(company_id)
        if not company.exists():
            return {'error': 'not found'}
        return company.read(['name', 'ticker', 'current_price'])[0]