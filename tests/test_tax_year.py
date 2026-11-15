from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import InvestingCase


@tagged("post_install", "-at_install")
class TestTaxYear(InvestingCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.other = cls.env["investing.company"].create(
            {"name": "Telefonica", "ticker": "TEF.MC", "currency": "EUR"}
        )

    def _tax_year(self, **vals):
        vals.setdefault("fiscal_year", 2025)
        return self.env["investing.tax.year"].create(vals)

    def test_resident_estimation(self):
        self._buy(100, 50, "2024-03-01 10:00:00")
        self._position().sell(100, 150, "2025-04-01 10:00:00")  # +10 000
        tax_year = self._tax_year()
        tax_year.action_compute()
        self.assertEqual(tax_year.state, "computed")
        self.assertAlmostEqual(tax_year.net_gain, 10000.0)
        self.assertAlmostEqual(tax_year.tax_attributable, 1980.0)
        self.assertEqual(len(tax_year.line_ids), 1)

    def test_only_sales_of_the_fiscal_year(self):
        self._buy(10, 100, "2024-01-01 10:00:00")
        self._position().sell(5, 200, "2024-06-01 10:00:00")
        # 31 Dec 23:30 UTC is already 1 Jan 2026 in Madrid -> belongs to 2026.
        self._position().sell(5, 200, "2025-12-31 23:30:00")
        tax_year = self._tax_year()
        tax_year.action_compute()
        self.assertFalse(tax_year.line_ids)
        self.assertAlmostEqual(tax_year.tax_attributable, 0.0)

    def test_two_month_rule_defers_loss(self):
        # Loss on TEF with a repurchase one month later -> loss not computable.
        self._buy(100, 10, "2025-01-10 10:00:00", asset=self.other)
        self._position(self.other).sell(100, 8, "2025-05-01 10:00:00")  # -200
        self._buy(100, 8, "2025-06-01 10:00:00", asset=self.other)
        # Gain on AAPL.
        self._buy(10, 100, "2025-01-10 10:00:00")
        self._position().sell(10, 200, "2025-07-01 10:00:00")  # +1000
        tax_year = self._tax_year()
        tax_year.action_compute()
        self.assertAlmostEqual(tax_year.deferred_losses, 200.0)
        self.assertAlmostEqual(tax_year.net_gain, 1000.0)
        self.assertAlmostEqual(tax_year.tax_attributable, 190.0)

    def test_non_resident_flat_rate_without_netting(self):
        self._buy(10, 100, "2025-01-10 10:00:00", asset=self.other)
        self._position(self.other).sell(10, 80, "2025-05-01 10:00:00")  # -200
        self._buy(10, 100, "2025-01-10 10:00:00")
        self._position().sell(10, 200, "2025-07-01 10:00:00")  # +1000
        tax_year = self._tax_year(regime="non_resident")
        tax_year.action_compute()
        self.assertAlmostEqual(tax_year.tax_attributable, 190.0)
        tax_year.action_reset_draft()
        tax_year.nonresident_exempt = True
        tax_year.action_compute()
        self.assertAlmostEqual(tax_year.tax_attributable, 0.0)

    def test_missing_scale_raises(self):
        with self.assertRaises(UserError):
            self._tax_year(fiscal_year=2015).action_compute()

    def test_foreign_currency_warning(self):
        usd = self.env["investing.company"].create(
            {"name": "Nvidia", "ticker": "NVDA", "currency": "USD"}
        )
        self._buy(1, 100, "2025-01-10 10:00:00", asset=usd)
        self._position(usd).sell(1, 120, "2025-02-10 10:00:00")
        tax_year = self._tax_year()
        tax_year.action_compute()
        self.assertTrue(tax_year.has_foreign_currency)
