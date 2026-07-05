from __future__ import annotations

import unittest

from fire_engine.calculators.decumulation import sequence_withdrawals
from fire_engine.models.investment_account import InvestmentAccount


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


if __name__ == "__main__":
    unittest.main()
