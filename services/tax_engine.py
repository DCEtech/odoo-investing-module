# Copyright 2026 Daniel Cejudo Echeverry
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""Pure tax computation helpers.

This module has NO dependency on Odoo on purpose: the arithmetic of the
Spanish savings tax ("base del ahorro") can be unit tested in isolation and
reused from scripts. Rates and brackets are NOT hardcoded here; they come
from ``investing.tax.scale`` records so a consultant can update them every
fiscal year without a code release.

Legal references (verify yearly with the ``hacienda-inversiones`` skill):

* IRPF (resident, common territory): progressive savings scale, arts. 66 and
  76 LIRPF. Netting of gains and losses and 25 % cross-offset against
  positive capital income, art. 49 LIRPF. Losses carried forward 4 years.
* IRNR (non resident without permanent establishment): flat rate per
  operation, no netting between gains and losses (art. 24-25 TRLIRNR).
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Bracket:
    """One step of a progressive scale.

    :param lower: inclusive lower bound of the bracket, in EUR.
    :param rate: marginal rate in percent (19.0 means 19 %).
    """

    lower: float
    rate: float


@dataclass(frozen=True)
class SavingsTaxResult:
    """Outcome of the savings tax estimation for one fiscal year."""

    net_gain: float  # computable gains - computable losses of the year
    carryforward_used: float  # prior-year losses offset against this year's gains
    rcm_offset_used: float  # year loss offset against 25 % of capital income
    loss_to_carryforward: float  # loss left for the next 4 years
    taxable_base: float  # total savings base (investments + other income)
    tax_total: float  # tax on the whole savings base
    tax_without_investments: float  # tax the other income would pay alone
    tax_attributable: float  # extra tax caused by the investments (can be < 0)
    effective_rate: float  # tax_attributable / net_gain, in percent


def progressive_tax(base: float, brackets: Sequence[Bracket]) -> float:
    """Apply a progressive scale to ``base``.

    >>> scale = [Bracket(0, 19), Bracket(6000, 21)]
    >>> round(progressive_tax(10000, scale), 2)
    1980.0
    """
    if base <= 0:
        return 0.0
    ordered = sorted(brackets, key=lambda b: b.lower)
    if not ordered or ordered[0].lower != 0:
        raise ValueError("A tax scale must start at 0.")
    tax = 0.0
    for index, bracket in enumerate(ordered):
        if base <= bracket.lower:
            break
        upper = ordered[index + 1].lower if index + 1 < len(ordered) else math.inf
        tax += (min(base, upper) - bracket.lower) * bracket.rate / 100.0
    return tax


def compute_resident_savings_tax(
    net_gain: float,
    brackets: Sequence[Bracket],
    other_savings_income: float = 0.0,
    loss_carryforward: float = 0.0,
    cross_offset_pct: float = 25.0,
) -> SavingsTaxResult:
    """Estimate the IRPF savings tax attributable to realized investment results.

    :param net_gain: computable gains minus computable losses of the year
        (losses deferred by the two-month rule must already be excluded).
    :param other_savings_income: positive net capital income of the year
        (dividends, interest). Investments are stacked on top of it, so the
        attributable tax is the *marginal* tax they generate.
    :param loss_carryforward: capital losses pending from the 4 previous years.
    :param cross_offset_pct: share of positive capital income that a net loss
        may offset (25 % since 2018, art. 49 LIRPF).
    """
    other = max(other_savings_income, 0.0)
    carry_available = max(loss_carryforward, 0.0)
    carryforward_used = rcm_offset_used = loss_left = 0.0

    if net_gain > 0:
        carryforward_used = min(carry_available, net_gain)
        gains_after = net_gain - carryforward_used
        other_after = other
    else:
        gains_after = 0.0
        loss = -net_gain
        rcm_offset_used = min(loss, other * cross_offset_pct / 100.0)
        other_after = other - rcm_offset_used
        loss_left = loss - rcm_offset_used

    taxable_base = other_after + gains_after
    tax_total = progressive_tax(taxable_base, brackets)
    tax_alone = progressive_tax(other, brackets)
    attributable = tax_total - tax_alone
    effective = attributable / net_gain * 100.0 if net_gain > 0 else 0.0
    return SavingsTaxResult(
        net_gain=net_gain,
        carryforward_used=carryforward_used,
        rcm_offset_used=rcm_offset_used,
        loss_to_carryforward=loss_left,
        taxable_base=taxable_base,
        tax_total=tax_total,
        tax_without_investments=tax_alone,
        tax_attributable=attributable,
        effective_rate=effective,
    )


def compute_nonresident_tax(gains: Iterable[float], rate: float) -> float:
    """IRNR without permanent establishment: flat rate on each positive gain.

    Losses are ignored because IRNR is computed operation by operation and
    does not allow netting gains with losses.
    """
    return sum(gain for gain in gains if gain > 0) * rate / 100.0
