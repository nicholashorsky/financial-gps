"""Deployment configuration and development-login safety tests."""

from __future__ import annotations

import os
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

from auth.login import _test_login_enabled


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DevelopmentLoginSafetyTests(unittest.TestCase):
    def test_explicit_development_flag_enables_shortcut(self) -> None:
        with patch.dict(
            os.environ,
            {"FINANCIAL_GPS_ENV": "development", "FINANCIAL_GPS_TEST_LOGIN": "1"},
            clear=True,
        ):
            self.assertTrue(_test_login_enabled())

    def test_production_environment_overrides_development_flag(self) -> None:
        with patch.dict(
            os.environ,
            {"FINANCIAL_GPS_ENV": "production", "FINANCIAL_GPS_TEST_LOGIN": "1"},
            clear=True,
        ):
            self.assertFalse(_test_login_enabled())

    def test_missing_flags_fail_closed(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(_test_login_enabled())


class StreamlitNavigationConfigurationTests(unittest.TestCase):
    def test_native_multipage_sidebar_is_disabled(self) -> None:
        with (PROJECT_ROOT / ".streamlit" / "config.toml").open("rb") as config_file:
            config = tomllib.load(config_file)

        self.assertFalse(config["client"]["showSidebarNavigation"])

if __name__ == "__main__":
    unittest.main()
