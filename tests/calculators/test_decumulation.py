from __future__ import annotations

import unittest

from fire_engine.calculators.decumulation import sequence_withdrawals
from fire_engine.models.investment_account import InvestmentAccount
from fire_engine.parameters.loader import get_params


class DecumulationTests(unittest.TestCase):
    def test_taxable_then_rrsp_then_tfsa_order(self) -> None:
        accounts = [
            InvestmentAccount(account_type="tfsa", current_balance=1000),
            InvestmentAccount(account_type="rrsp", current_balance=2000),
            InvestmentAccount(account_type="taxable", current_balance=500),
        ]
        result = sequence_withdrawals(2200, accounts)
        self.assertEqual(result.withdrawals["taxable"], 500)
        self.assertEqual(result.withdrawals["rrsp"], 1700)
        self.assertEqual(result.unmet_need, 0)

    def test_gis_loss_causes_tfsa_to_be_used_before_rrsp(self) -> None:
        accounts = [
            InvestmentAccount(account_type="rrsp", current_balance=5000),
            InvestmentAccount(account_type="tfsa", current_balance=5000),
        ]

        result = sequence_withdrawals(
            2000,
            accounts,
            baseline_taxable_income=10000,
            baseline_gis_income=10000,
            is_gis_eligible=True,
            resolved_params=get_params(2026, "ON"),
        )

        self.assertEqual(result.withdrawals, {"tfsa": 2000.0})
        self.assertTrue(any("GIS loss" in note for note in result.notes))

    def test_ordinary_income_uses_rrsp_before_tfsa(self) -> None:
        accounts = [
            InvestmentAccount(account_type="rrsp", current_balance=5000),
            InvestmentAccount(account_type="tfsa", current_balance=5000),
        ]

        result = sequence_withdrawals(
            2000,
            accounts,
            baseline_taxable_income=40000,
            baseline_gis_income=40000,
            resolved_params=get_params(2026, "ON"),
        )

        self.assertEqual(result.withdrawals, {"rrsp": 2000.0})

    def test_strategy_rechecks_cost_when_oas_threshold_is_crossed(self) -> None:
        resolved = get_params(2026, "ON")
        accounts = [
            InvestmentAccount(account_type="rrsp", current_balance=5000),
            InvestmentAccount(account_type="tfsa", current_balance=5000),
        ]

        result = sequence_withdrawals(
            2000,
            accounts,
            baseline_taxable_income=resolved.params.oas_recovery_threshold - 1500,
            baseline_gis_income=resolved.params.oas_recovery_threshold - 1500,
            oas_received=9000,
            resolved_params=resolved,
        )

        self.assertEqual(result.withdrawals, {"rrsp": 1000.0, "tfsa": 1000.0})
        self.assertTrue(any("preferring registered" in note for note in result.notes))
        self.assertTrue(any("preferring tax-free" in note for note in result.notes))
        self.assertTrue(all(account.current_balance >= 0 for account in accounts))


if __name__ == "__main__":
    unittest.main()
