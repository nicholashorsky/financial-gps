"""Old Age Security recovery-tax calculation."""

from __future__ import annotations

from fire_engine.parameters.loader import ResolvedParams, get_params


def calculate_oas_recovery_tax(
    net_income: float,
    oas_received: float,
    resolved: ResolvedParams | None = None,
) -> float:
    """Return recovery tax, capped at the OAS benefit received.

    The model uses taxable income as its net-income proxy. The 15% recovery
    rate and threshold come from the resolved CRA parameter set.

    Source: https://www.canada.ca/en/services/benefits/publicpensions/
    cpp/old-age-security/recovery-tax.html
    """

    resolved = resolved or get_params(2026, "ON")
    params = resolved.params
    recovery = max(net_income - params.oas_recovery_threshold, 0.0) * params.oas_recovery_rate
    return round(min(recovery, max(oas_received, 0.0)), 2)
