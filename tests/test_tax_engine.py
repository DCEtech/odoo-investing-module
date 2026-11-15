from odoo.tests import BaseCase, tagged

from ..services.tax_engine import (
    Bracket,
    compute_nonresident_tax,
    compute_resident_savings_tax,
    progressive_tax,
)

SCALE_2025 = [
    Bracket(0, 19),
    Bracket(6000, 21),
    Bracket(50000, 23),
    Bracket(200000, 27),
    Bracket(300000, 30),
]


@tagged("post_install", "-at_install")
class TestTaxEngine(BaseCase):
    def test_progressive_first_brackets(self):
        # 6000 * 19 % + 4000 * 21 %
        self.assertAlmostEqual(progressive_tax(10000, SCALE_2025), 1980.0)

    def test_progressive_top_bracket(self):
        # Official cumulative quota at 300 000 is 71 880; + 50 000 * 30 %
        self.assertAlmostEqual(progressive_tax(350000, SCALE_2025), 86880.0)

    def test_progressive_zero_or_negative(self):
        self.assertEqual(progressive_tax(0, SCALE_2025), 0.0)
        self.assertEqual(progressive_tax(-500, SCALE_2025), 0.0)

    def test_scale_must_start_at_zero(self):
        with self.assertRaises(ValueError):
            progressive_tax(100, [Bracket(10, 19)])

    def test_gains_stacked_on_other_income(self):
        # 5000 of dividends already fill most of the 19 % bracket.
        result = compute_resident_savings_tax(
            3000, SCALE_2025, other_savings_income=5000
        )
        # 1000 at 19 % + 2000 at 21 %
        self.assertAlmostEqual(result.tax_attributable, 610.0)
        self.assertAlmostEqual(result.taxable_base, 8000.0)

    def test_carryforward_reduces_gain(self):
        result = compute_resident_savings_tax(4000, SCALE_2025, loss_carryforward=1500)
        self.assertAlmostEqual(result.carryforward_used, 1500.0)
        self.assertAlmostEqual(result.tax_attributable, 2500 * 0.19)

    def test_loss_offsets_25pct_of_capital_income(self):
        result = compute_resident_savings_tax(
            -2000, SCALE_2025, other_savings_income=4000
        )
        self.assertAlmostEqual(result.rcm_offset_used, 1000.0)  # 25 % of 4000
        self.assertAlmostEqual(result.loss_to_carryforward, 1000.0)
        self.assertAlmostEqual(result.tax_attributable, -1000 * 0.19)

    def test_nonresident_ignores_losses(self):
        self.assertAlmostEqual(compute_nonresident_tax([1000, -400, 500], 19), 285.0)
