# Copyright 2026 Daniel Cejudo Echeverry
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..services.tax_engine import Bracket

TAX_REGIMES = [
    ("resident_common", "Resident - IRPF (common territory)"),
    ("non_resident", "Non resident - IRNR (no permanent establishment)"),
]


class InvestingTaxScale(models.Model):
    """Tax scale for one regime and fiscal year.

    Rates live in data records instead of code: updating them for a new
    fiscal year is a configuration task (duplicate + edit), not a release.
    """

    _name = "investing.tax.scale"
    _description = "Investing Tax Scale"
    _order = "fiscal_year desc, regime"

    name = fields.Char(compute="_compute_name", store=True)
    regime = fields.Selection(selection=TAX_REGIMES, required=True)
    fiscal_year = fields.Integer(required=True)
    line_ids = fields.One2many(
        "investing.tax.scale.line", "scale_id", string="Brackets", copy=True
    )
    legal_reference = fields.Char(
        help="Legal basis of the scale, e.g. 'arts. 66 y 76 LIRPF'."
    )
    active = fields.Boolean(default=True)

    _regime_year_uniq = models.Constraint(
        "UNIQUE (regime, fiscal_year)",
        "There is already a tax scale for this regime and fiscal year.",
    )

    @api.depends("regime", "fiscal_year")
    def _compute_name(self) -> None:
        labels = dict(TAX_REGIMES)
        for scale in self:
            scale.name = (
                f"{labels.get(scale.regime, '')} {scale.fiscal_year or ''}".strip()
            )

    @api.constrains("line_ids")
    def _check_starts_at_zero(self) -> None:
        for scale in self:
            if scale.line_ids and min(scale.line_ids.mapped("lower_bound")) != 0:
                raise ValidationError(
                    self.env._("The first bracket of a tax scale must start at 0.")
                )

    def copy(self, default=None):
        # Duplicating is the expected way to prepare next year's scale.
        default = dict(default or {})
        default.setdefault("fiscal_year", max(self.mapped("fiscal_year")) + 1)
        return super().copy(default)

    @api.model
    def _get_for(self, regime: str, fiscal_year: int) -> "InvestingTaxScale":
        scale = self.search(
            [("regime", "=", regime), ("fiscal_year", "=", fiscal_year)], limit=1
        )
        if not scale or not scale.line_ids:
            raise UserError(
                self.env._(
                    "No tax scale is configured for %(regime)s in %(year)s. "
                    "Duplicate the previous year's scale in Investing > "
                    "Configuration > Tax Scales and verify the rates against "
                    "the official sources.",
                    regime=dict(TAX_REGIMES)[regime],
                    year=fiscal_year,
                )
            )
        return scale

    def _get_brackets(self) -> list[Bracket]:
        self.ensure_one()
        return [
            Bracket(line.lower_bound, line.rate)
            for line in self.line_ids.sorted("lower_bound")
        ]


class InvestingTaxScaleLine(models.Model):
    _name = "investing.tax.scale.line"
    _description = "Investing Tax Scale Bracket"
    _order = "scale_id, lower_bound"

    scale_id = fields.Many2one(
        "investing.tax.scale", required=True, ondelete="cascade", index=True
    )
    lower_bound = fields.Float(
        string="From (EUR)", required=True, help="Inclusive lower bound of the bracket."
    )
    rate = fields.Float(string="Rate (%)", required=True, digits=(5, 2))

    _rate_range = models.Constraint(
        "CHECK (rate >= 0 AND rate <= 100)",
        "The rate must be between 0 and 100.",
    )
    _lower_positive = models.Constraint(
        "CHECK (lower_bound >= 0)",
        "The lower bound cannot be negative.",
    )
