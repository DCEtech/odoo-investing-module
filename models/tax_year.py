# Copyright 2026 Daniel Cejudo Echeverry
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from datetime import datetime

import pytz
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models

from ..services.tax_engine import compute_nonresident_tax, compute_resident_savings_tax
from .tax_scale import TAX_REGIMES

AMOUNT_DIGITS = (16, 2)
# Art. 33.5.f LIRPF: window for listed securities. Unlisted ones use one year
# (art. 33.5.g); the module does not distinguish asset types yet.
LOSS_DEFERRAL_WINDOW = relativedelta(months=2)


class InvestingTaxYear(models.Model):
    """Estimation of the tax due for the realized investment results of a year.

    The computation is a snapshot: lines and totals are stored so the user
    keeps the figures shown when filing, even if history changes later.
    """

    _name = "investing.tax.year"
    _description = "Investing Fiscal Year Tax Estimation"
    _order = "fiscal_year desc"

    name = fields.Char(compute="_compute_name", store=True)
    fiscal_year = fields.Integer(
        required=True, default=lambda self: fields.Date.today().year
    )
    regime = fields.Selection(
        selection=TAX_REGIMES, required=True, default="resident_common"
    )
    state = fields.Selection(
        selection=[("draft", "Draft"), ("computed", "Computed")],
        default="draft",
        readonly=True,
        copy=False,
    )
    computed_on = fields.Datetime(readonly=True, copy=False)
    scale_id = fields.Many2one("investing.tax.scale", readonly=True, copy=False)

    # Inputs that the module cannot know and the user takes from other sources.
    other_savings_income = fields.Float(
        digits=AMOUNT_DIGITS,
        help="Net positive capital income of the year taxed in the savings base "
        "(dividends, interest). Investments are stacked on top of it.",
    )
    loss_carryforward = fields.Float(
        string="Losses Pending from Previous Years",
        digits=AMOUNT_DIGITS,
        help="Capital losses of the previous 4 years still pending offset, as shown "
        "in last year's tax return.",
    )
    nonresident_exempt = fields.Boolean(
        string="Exempt by Treaty / EU Rule",
        help="Tick if the gains are exempt in Spain (e.g. residents of an EU/EEA State "
        "or a double taxation treaty assigning taxation to the residence State).",
    )

    line_ids = fields.One2many(
        "investing.tax.year.line", "tax_year_id", readonly=True, copy=False
    )

    total_gains = fields.Float(digits=AMOUNT_DIGITS, readonly=True, copy=False)
    total_losses = fields.Float(digits=AMOUNT_DIGITS, readonly=True, copy=False)
    deferred_losses = fields.Float(
        digits=AMOUNT_DIGITS,
        readonly=True,
        copy=False,
        help="Losses not computable this year because homogeneous shares were bought "
        "within two months before or after the sale (art. 33.5.f LIRPF).",
    )
    net_gain = fields.Float(digits=AMOUNT_DIGITS, readonly=True, copy=False)
    carryforward_used = fields.Float(digits=AMOUNT_DIGITS, readonly=True, copy=False)
    rcm_offset_used = fields.Float(
        string="Loss Offset Against Capital Income",
        digits=AMOUNT_DIGITS,
        readonly=True,
        copy=False,
    )
    loss_to_carryforward = fields.Float(digits=AMOUNT_DIGITS, readonly=True, copy=False)
    taxable_base = fields.Float(digits=AMOUNT_DIGITS, readonly=True, copy=False)
    tax_total = fields.Float(
        string="Total Savings Tax", digits=AMOUNT_DIGITS, readonly=True, copy=False
    )
    tax_attributable = fields.Float(
        string="Tax Due for Investments",
        digits=AMOUNT_DIGITS,
        readonly=True,
        copy=False,
        help="Additional tax caused by the investment results. A negative value means "
        "the losses reduce the tax on other savings income.",
    )
    effective_rate = fields.Float(
        string="Effective Rate (%)", digits=(5, 2), readonly=True, copy=False
    )
    has_foreign_currency = fields.Boolean(readonly=True, copy=False)

    _year_regime_uniq = models.Constraint(
        "UNIQUE (fiscal_year, regime)",
        "There is already an estimation for this fiscal year and regime.",
    )

    @api.depends("fiscal_year", "regime")
    def _compute_name(self) -> None:
        for tax_year in self:
            tax_year.name = self.env._("Fiscal year %s", tax_year.fiscal_year)

    def action_compute(self) -> bool:
        for tax_year in self:
            tax_year._compute_estimation()
        return True

    def action_reset_draft(self) -> bool:
        self.line_ids.unlink()
        self.write({"state": "draft", "computed_on": False})
        return True

    # ------------------------------------------------------------------
    # Business logic
    # ------------------------------------------------------------------
    def _get_utc_bounds(self) -> tuple[datetime, datetime]:
        """Return [1 Jan, 1 Jan next year) in naive UTC, as stored by Odoo.

        Datetimes are stored in UTC, but the fiscal year follows Spanish local
        time: a sale at 00:30 on 1 January in Madrid is 23:30 UTC on 31 December.
        """
        self.ensure_one()
        tz = pytz.timezone(self.env.user.tz or "Europe/Madrid")

        def to_utc(local: datetime) -> datetime:
            return tz.localize(local).astimezone(pytz.utc).replace(tzinfo=None)

        return to_utc(datetime(self.fiscal_year, 1, 1)), to_utc(
            datetime(self.fiscal_year + 1, 1, 1)
        )

    def _prepare_line_vals(self, sells) -> list[dict]:
        """Build one line per sale, applying the two-month rule to losses."""
        History = self.env["investing.buy.sell.history"]
        # One query for all buys inside any deferral window (no search in a loop).
        buys = History.search(
            [
                ("order_type", "=", "buy"),
                ("company_id", "in", sells.company_id.ids),
                ("date", ">=", min(sells.mapped("date")) - LOSS_DEFERRAL_WINDOW),
                ("date", "<=", max(sells.mapped("date")) + LOSS_DEFERRAL_WINDOW),
            ]
        )
        vals_list = []
        for sell in sells:
            gain = sell.realized_profit
            deferred = 0.0
            if gain < 0 and self.regime == "resident_common":
                window_qty = sum(
                    buys.filtered(
                        lambda b, s=sell: (
                            b.company_id == s.company_id
                            and s.date - LOSS_DEFERRAL_WINDOW
                            <= b.date
                            <= s.date + LOSS_DEFERRAL_WINDOW
                        )
                    ).mapped("shares")
                )
                # Conservative simplification: the deferred part is proportional to the
                # homogeneous shares bought in the window (see README > Limitations).
                fraction = min(1.0, window_qty / sell.shares) if sell.shares else 0.0
                deferred = -gain * fraction
            vals_list.append(
                {
                    "tax_year_id": self.id,
                    "history_id": sell.id,
                    "gain": gain,
                    "deferred_loss": deferred,
                }
            )
        return vals_list

    def _compute_estimation(self) -> None:
        self.ensure_one()
        scale = self.env["investing.tax.scale"]._get_for(self.regime, self.fiscal_year)
        start, end = self._get_utc_bounds()
        sells = self.env["investing.buy.sell.history"].search(
            [("order_type", "=", "sell"), ("date", ">=", start), ("date", "<", end)],
            order="date asc, id asc",
        )
        self.line_ids.unlink()
        lines = self.env["investing.tax.year.line"].create(
            self._prepare_line_vals(sells) if sells else []
        )

        computable = lines.mapped("computable_gain")
        total_gains = sum(g for g in computable if g > 0)
        total_losses = -sum(g for g in computable if g < 0)
        vals = {
            "state": "computed",
            "computed_on": fields.Datetime.now(),
            "scale_id": scale.id,
            "total_gains": total_gains,
            "total_losses": total_losses,
            "deferred_losses": sum(lines.mapped("deferred_loss")),
            "net_gain": total_gains - total_losses,
            "has_foreign_currency": any(
                (cur or "EUR").upper() != "EUR"
                for cur in sells.company_id.mapped("currency")
            ),
        }
        if self.regime == "resident_common":
            result = compute_resident_savings_tax(
                net_gain=vals["net_gain"],
                brackets=scale._get_brackets(),
                other_savings_income=self.other_savings_income,
                loss_carryforward=self.loss_carryforward,
            )
            vals.update(
                carryforward_used=result.carryforward_used,
                rcm_offset_used=result.rcm_offset_used,
                loss_to_carryforward=result.loss_to_carryforward,
                taxable_base=result.taxable_base,
                tax_total=result.tax_total,
                tax_attributable=result.tax_attributable,
                effective_rate=result.effective_rate,
            )
        else:
            # IRNR: flat rate per operation, no netting, no other income stacking.
            rate = scale._get_brackets()[0].rate
            tax = (
                0.0
                if self.nonresident_exempt
                else compute_nonresident_tax(computable, rate)
            )
            vals.update(
                carryforward_used=0.0,
                rcm_offset_used=0.0,
                loss_to_carryforward=0.0,
                taxable_base=total_gains,
                tax_total=tax,
                tax_attributable=tax,
                effective_rate=tax / total_gains * 100.0 if total_gains else 0.0,
            )
        self.write(vals)


class InvestingTaxYearLine(models.Model):
    _name = "investing.tax.year.line"
    _description = "Investing Fiscal Year Sale Line"
    _order = "date, id"

    tax_year_id = fields.Many2one(
        "investing.tax.year", required=True, ondelete="cascade", index=True
    )
    history_id = fields.Many2one(
        "investing.buy.sell.history", string="Sale", required=True, ondelete="restrict"
    )
    company_id = fields.Many2one(related="history_id.company_id", string="Asset")
    date = fields.Datetime(related="history_id.date", store=True)
    shares = fields.Float(related="history_id.shares")
    price = fields.Float(related="history_id.price", string="Sale Price")
    gain = fields.Float(string="Gain / Loss", digits=AMOUNT_DIGITS)
    deferred_loss = fields.Float(digits=AMOUNT_DIGITS)
    computable_gain = fields.Float(
        compute="_compute_computable_gain", store=True, digits=AMOUNT_DIGITS
    )

    @api.depends("gain", "deferred_loss")
    def _compute_computable_gain(self) -> None:
        for line in self:
            line.computable_gain = line.gain + line.deferred_loss
