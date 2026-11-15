from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import InvestingCase


@tagged("post_install", "-at_install")
class TestFifo(InvestingCase):
    def test_sell_consumes_oldest_lot_first(self):
        self._buy(10, 100, "2025-01-10 10:00:00")
        self._buy(10, 150, "2025-03-10 10:00:00")
        profit = self._position().sell(15, 200, "2025-06-01 10:00:00")
        # 10 * (200 - 100) + 5 * (200 - 150)
        self.assertAlmostEqual(profit, 1250.0)
        position = self._position()
        self.assertAlmostEqual(position.shares, 5.0)
        self.assertAlmostEqual(position.purchase_price, 150.0)

    def test_oversell_is_rejected(self):
        self._buy(5, 100, "2025-01-10 10:00:00")
        with self.assertRaises(UserError):
            self._position().sell(6, 100, "2025-02-01 10:00:00")

    def test_backdated_sale_cannot_consume_future_lots(self):
        self._buy(5, 100, "2025-01-10 10:00:00")
        self._buy(5, 100, "2025-05-10 10:00:00")
        with self.assertRaises(UserError):
            # Only 5 shares were held on 1 March.
            self._position().sell(8, 120, "2025-03-01 10:00:00")

    def test_fractional_units_leave_no_ghost_lot(self):
        self._buy(0.1, 100, "2025-01-10 10:00:00")
        self._buy(0.2, 100, "2025-01-11 10:00:00")
        self._position().sell(0.3, 110, "2025-02-01 10:00:00")
        open_lots = self.env["investing.buy.sell.history"].search(
            [("order_type", "=", "buy"), ("remaining_shares", ">", 0)]
        )
        self.assertFalse(open_lots)
