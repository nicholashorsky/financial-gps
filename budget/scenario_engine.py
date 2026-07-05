"""Budget what-if scenario calculators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from budget.narrator import scenario_message


SCENARIO_TYPES = {
    "new_job": "New Job",
    "buy_house": "Buy a House",
    "side_hustle": "Side Hustle",
    "major_purchase": "Major Purchase",
}


@dataclass(frozen=True)
class ScenarioResult:
    scenario_type: str
    monthly_cash_flow_delta: float
    five_year_net_worth_impact: float
    goal_date_delta_months: int
    verdict: str
    details: dict[str, float | str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_type": self.scenario_type,
            "monthly_cash_flow_delta": round(self.monthly_cash_flow_delta, 2),
            "five_year_net_worth_impact": round(self.five_year_net_worth_impact, 2),
            "goal_date_delta_months": self.goal_date_delta_months,
            "verdict": self.verdict,
            "details": self.details,
        }


def _goal_month_delta(monthly_delta: float, target_gap: float = 10000.0) -> int:
    """Estimate goal acceleration/delay against a default $10k remaining gap."""

    if abs(monthly_delta) < 1:
        return 0
    return int(round(-(target_gap / abs(monthly_delta)) if monthly_delta > 0 else target_gap / abs(monthly_delta)))


def new_job(inputs: dict[str, Any]) -> ScenarioResult:
    current_salary = float(inputs.get("current_salary", 0) or 0)
    new_salary = float(inputs.get("new_salary", 0) or 0)
    commute_cost_change = float(inputs.get("commute_cost_change", 0) or 0)
    benefits_value_change = float(inputs.get("benefits_value_change", 0) or 0)
    remote_work_savings = float(inputs.get("remote_work_savings", 0) or 0)
    tax_rate = float(inputs.get("tax_rate", 0.30) or 0.30)

    after_tax_salary_delta = (new_salary - current_salary) * (1 - tax_rate) / 12
    monthly_delta = after_tax_salary_delta - commute_cost_change + remote_work_savings + (benefits_value_change / 12)
    net_impact = monthly_delta * 60
    return ScenarioResult(
        scenario_type="new_job",
        monthly_cash_flow_delta=monthly_delta,
        five_year_net_worth_impact=net_impact,
        goal_date_delta_months=_goal_month_delta(monthly_delta),
        verdict=scenario_message("new_job", monthly_delta, net_impact),
        details={
            "after_tax_salary_delta_monthly": round(after_tax_salary_delta, 2),
            "tax_rate": tax_rate,
        },
    )


def buy_house(inputs: dict[str, Any]) -> ScenarioResult:
    purchase_price = float(inputs.get("purchase_price", 0) or 0)
    down_payment_pct = float(inputs.get("down_payment_pct", 20) or 20) / 100
    mortgage_rate = float(inputs.get("mortgage_rate", 5.0) or 5.0) / 100
    amortization_years = int(inputs.get("amortization_years", 25) or 25)
    property_tax_annual = float(inputs.get("property_tax_annual", 0) or 0)
    maintenance_pct = float(inputs.get("maintenance_pct", 1.0) or 1.0) / 100
    current_rent = float(inputs.get("current_rent", 0) or 0)

    down_payment = purchase_price * down_payment_pct
    principal = max(purchase_price - down_payment, 0)
    monthly_rate = mortgage_rate / 12
    months = amortization_years * 12
    if principal <= 0:
        mortgage_payment = 0
    elif monthly_rate == 0:
        mortgage_payment = principal / months
    else:
        mortgage_payment = principal * monthly_rate * (1 + monthly_rate) ** months / ((1 + monthly_rate) ** months - 1)

    monthly_owner_cost = mortgage_payment + property_tax_annual / 12 + (purchase_price * maintenance_pct / 12)
    monthly_delta = current_rent - monthly_owner_cost
    equity_build = down_payment + max(mortgage_payment * 60 * 0.35, 0)
    net_impact = monthly_delta * 60 + equity_build - down_payment
    return ScenarioResult(
        scenario_type="buy_house",
        monthly_cash_flow_delta=monthly_delta,
        five_year_net_worth_impact=net_impact,
        goal_date_delta_months=_goal_month_delta(monthly_delta),
        verdict=scenario_message("buy_house", monthly_delta, net_impact),
        details={
            "mortgage_payment": round(mortgage_payment, 2),
            "down_payment": round(down_payment, 2),
            "monthly_owner_cost": round(monthly_owner_cost, 2),
        },
    )


def side_hustle(inputs: dict[str, Any]) -> ScenarioResult:
    monthly_revenue = float(inputs.get("monthly_revenue", 0) or 0)
    monthly_expenses = float(inputs.get("monthly_expenses", 0) or 0)
    growth_rate = float(inputs.get("growth_rate", 0) or 0) / 100
    tax_rate = float(inputs.get("tax_rate", 25) or 25) / 100

    monthly_profit = max(monthly_revenue - monthly_expenses, 0)
    after_tax_monthly = monthly_profit * (1 - tax_rate)
    five_year_impact = 0.0
    for year in range(5):
        five_year_impact += after_tax_monthly * 12 * ((1 + growth_rate) ** year)
    return ScenarioResult(
        scenario_type="side_hustle",
        monthly_cash_flow_delta=after_tax_monthly,
        five_year_net_worth_impact=five_year_impact,
        goal_date_delta_months=_goal_month_delta(after_tax_monthly),
        verdict=scenario_message("side_hustle", after_tax_monthly, five_year_impact),
        details={
            "monthly_profit_before_tax": round(monthly_profit, 2),
            "tax_rate": tax_rate,
        },
    )


def major_purchase(inputs: dict[str, Any]) -> ScenarioResult:
    purchase_price = float(inputs.get("purchase_price", 0) or 0)
    financing_rate = float(inputs.get("financing_rate", 0) or 0) / 100
    financing_term_months = int(inputs.get("financing_term_months", 0) or 0)
    cash_paid = float(inputs.get("cash_paid", purchase_price) or 0)

    financed_amount = max(purchase_price - cash_paid, 0)
    monthly_rate = financing_rate / 12
    if financed_amount <= 0 or financing_term_months <= 0:
        payment = 0.0
        total_interest = 0.0
    elif monthly_rate == 0:
        payment = financed_amount / financing_term_months
        total_interest = 0.0
    else:
        payment = financed_amount * monthly_rate * (1 + monthly_rate) ** financing_term_months / (
            (1 + monthly_rate) ** financing_term_months - 1
        )
        total_interest = payment * financing_term_months - financed_amount

    monthly_delta = -payment
    net_impact = -cash_paid - min(payment * 60, payment * financing_term_months)
    return ScenarioResult(
        scenario_type="major_purchase",
        monthly_cash_flow_delta=monthly_delta,
        five_year_net_worth_impact=net_impact,
        goal_date_delta_months=_goal_month_delta(monthly_delta),
        verdict=scenario_message("major_purchase", monthly_delta, net_impact),
        details={
            "financed_amount": round(financed_amount, 2),
            "monthly_payment": round(payment, 2),
            "total_interest": round(total_interest, 2),
        },
    )


def run_scenario(scenario_type: str, inputs: dict[str, Any]) -> ScenarioResult:
    calculators = {
        "new_job": new_job,
        "buy_house": buy_house,
        "side_hustle": side_hustle,
        "major_purchase": major_purchase,
    }
    if scenario_type not in calculators:
        raise ValueError(f"Unsupported scenario type: {scenario_type}")
    return calculators[scenario_type](inputs)
