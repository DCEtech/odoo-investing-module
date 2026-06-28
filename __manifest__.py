{
    'name': 'Investing',
    'summary': 'Portfolio and investment tracking for companies',
    'author': 'Daniel Cejudo Echeverry',
    'category': 'Finance',
    'license': 'LGPL-3',
    'version': '19.0.1.0.0',
    'depends': ['base'],
    'data': [
        "security/groups.xml", 
        "security/ir.model.access.csv", 
        "data/cron.xml",
        "views/company_views.xml", 
        "views/portfolio_views.xml", 
        "views/price_history_views.xml", 
        "views/menus.xml"
        ],
    'installable': True,
    'application': True,
}