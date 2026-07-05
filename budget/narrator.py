"""Dry financial narration helpers for dashboard copy."""

from __future__ import annotations


def first_login_message() -> str:
    return "Welcome. Let's figure out where you're actually headed."


def home_message(transaction_count: int, goal_count: int) -> str:
    if transaction_count == 0:
        return first_login_message()
    if goal_count == 0:
        return "Your money has opinions, but no destination. That seems suboptimal."
    return "The numbers are in motion. Now we can ask them slightly uncomfortable questions."


def spending_message(spending_total: float, top_category: str | None = None) -> str:
    if spending_total <= 0:
        return "Nothing to critique yet. An unusual, almost suspicious state."
    category = top_category or "miscellaneous"
    return f"Most of this month went to {category}. Future You has made a note."


def forecast_message(monthly_surplus: float, conservative_years: int | None = None) -> str:
    if monthly_surplus < 0:
        return "The forecast is leaking money. That detail may become important."
    if conservative_years is not None and conservative_years <= 10:
        return "The conservative line is being rude, but at least it's being honest."
    return "The bands diverge politely, which is finance's way of saying 'there are assumptions here.'"


def goal_message(goal_name: str, progress_pct: float) -> str:
    if progress_pct >= 100:
        return f"{goal_name} is complete. Future You can stop pacing."
    if progress_pct >= 75:
        return f"{goal_name} is mostly there. The remaining distance has opinions."
    if progress_pct >= 25:
        return f"{goal_name} has started moving. Momentum is finally doing a little work."
    return f"{goal_name} is still near the launchpad. Tiny steps, regrettably, still count."


def no_goals_message() -> str:
    return "Future You is waiting for direction. What are we even doing this for?"


def scenario_message(scenario_type: str, monthly_delta: float, net_worth_impact: float) -> str:
    if scenario_type == "new_job":
        if monthly_delta > 0:
            return "Congratulations. Future You approves of this salary increase."
        return "The new title is doing a lot of emotional labor here."
    if scenario_type == "buy_house":
        if monthly_delta < 0:
            return "The house is affordable if the roof remains emotionally supportive."
        return "Monthly cash flow improves. The spreadsheet is suspicious but interested."
    if scenario_type == "side_hustle":
        if monthly_delta > 0:
            return "Side income detected. Future You is cautiously adding another tab to the spreadsheet."
        return "This side hustle currently appears to be a hobby with invoices."
    if scenario_type == "major_purchase":
        if net_worth_impact < 0:
            return "Financial impact: noticeable. Emotional impact: presumably shiny."
        return "The purchase survived the math. That is not legal advice."
    return "Saved. Future You is watching this one closely."


def fire_date_message(fire_year: int | None) -> str:
    if fire_year is None:
        return "No FIRE date yet. The spreadsheet requires a few more facts before it makes promises."
    return f"Projected retirement: {fire_year}. The fifth monitor remains under review."


def cpp_delay_message(age_65_amount: float, age_70_amount: float) -> str:
    increase = max(age_70_amount - age_65_amount, 0.0)
    return f"Delaying CPP to 70 adds ${increase:,.2f}/month. Future You took the deal."


def gis_message(annual_amount: float) -> str:
    if annual_amount > 0:
        return "You qualify for GIS. The bad news is what that says about income. Let's fix that."
    return "GIS is currently out of the picture, which is cleaner even if less dramatic."


def csv_sync_message(updated: int, preserved: int) -> str:
    return f"Your transactions updated your FIRE baseline: {updated} field(s) updated, {preserved} preserved."
