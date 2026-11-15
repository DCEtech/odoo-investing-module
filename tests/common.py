from odoo.tests import TransactionCase


class InvestingCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, tracking_disable=True, tz="Europe/Madrid")
        )
        cls.env.user.tz = "Europe/Madrid"
        cls.asset = cls.env["investing.company"].create(
            {"name": "Apple", "ticker": "AAPL", "currency": "EUR"}
        )
        cls.Portfolio = cls.env["investing.portfolio"]

    @classmethod
    def _buy(cls, shares: float, price: float, date: str, asset=None):
        return cls.Portfolio.create(
            {
                "company_id": (asset or cls.asset).id,
                "date": date,
                "shares": shares,
                "purchase_price": price,
            }
        )

    @classmethod
    def _position(cls, asset=None):
        return cls.Portfolio.search(
            [("company_id", "=", (asset or cls.asset).id)], limit=1
        )
