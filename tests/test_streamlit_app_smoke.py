"""End-to-end smoke coverage for the primary Streamlit beta workflow."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

import shared.db as db_module
from shared.beta_policy import SYNTHETIC_DATA_NOTICE


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "app.py"
SAMPLE_CSV_PATH = PROJECT_ROOT / "csv samples" / "RBC SAMPLE CSV.csv"


class StreamlitAppSmokeTests(unittest.TestCase):
    """Exercise the beta's primary user path without touching the user's database."""

    def setUp(self):
        temporary_database = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temporary_database.close()
        self.database_path = Path(temporary_database.name)
        self.original_database_path = db_module.DB_PATH
        db_module.DB_PATH = str(self.database_path)

        self.environment = patch.dict(
            os.environ,
            {
                "FINANCIAL_GPS_ENV": "development",
                "FINANCIAL_GPS_TEST_LOGIN": "1",
            },
        )
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        db_module.DB_PATH = self.original_database_path
        self.database_path.unlink(missing_ok=True)

    def assert_no_streamlit_exception(self, app):
        messages = [exception.value for exception in app.exception]
        self.assertEqual(messages, [], f"Streamlit raised exceptions: {messages}")

    @staticmethod
    def click_button(app, label):
        button = next(button for button in app.button if button.label == label)
        return button.click().run(timeout=30)

    def test_primary_beta_workflow(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        self.assert_no_streamlit_exception(app)

        app = self.click_button(app, "Continue as Beta Tester")
        self.assertEqual(app.session_state["page"], "Onboarding")
        self.assert_no_streamlit_exception(app)

        app = self.click_button(app, "💸  Spending")
        app = self.click_button(app, "Import CSV")
        self.assertTrue(
            any("Synthetic sample data only" in message.value for message in app.warning),
            "The CSV import did not display the synthetic-data restriction.",
        )
        app.file_uploader[0].upload(
            SAMPLE_CSV_PATH.name,
            SAMPLE_CSV_PATH.read_bytes(),
            "text/csv",
        )
        app = app.run(timeout=30)
        app = self.click_button(app, "Confirm and import")
        self.assert_no_streamlit_exception(app)
        self.assertTrue(
            any("Imported 118 transactions" in message.value for message in app.success),
            "The sample import did not report the expected transaction count.",
        )

        with db_module.get_connection() as connection:
            transaction_count = connection.execute(
                "SELECT COUNT(*) FROM transactions"
            ).fetchone()[0]
            account_count = connection.execute(
                "SELECT COUNT(*) FROM accounts"
            ).fetchone()[0]
            transfer_count = connection.execute(
                "SELECT COUNT(*) FROM transactions WHERE transfer_match_id IS NOT NULL"
            ).fetchone()[0]

        self.assertEqual(transaction_count, 118)
        self.assertEqual(account_count, 4)
        self.assertGreaterEqual(transfer_count, 10)

        pages = {
            "🏠  Home": "Home",
            "💸  Spending": "Spending",
            "🎯  Goals": "Goals",
            "🧭  Plans": "Plans",
            "⚠️  Data Quality": "Data Quality",
            "⚙️  Settings": "Settings",
        }

        for navigation_label, expected_page in pages.items():
            with self.subTest(page=expected_page):
                app = self.click_button(app, navigation_label)
                self.assertEqual(app.session_state["page"], expected_page)
                self.assert_no_streamlit_exception(app)

                if expected_page == "Plans":
                    app = self.click_button(app, "Create plan")
                    self.assert_no_streamlit_exception(app)
                    self.assertTrue(any(tab.label == "Projection" for tab in app.tabs))
                elif expected_page == "Settings":
                    self.assertEqual(
                        [tab.label for tab in app.tabs],
                        [
                            "Profile",
                            "Assumptions",
                            "Rules",
                            "Categories",
                            "Account & data",
                        ],
                    )
                    self.assertTrue(
                        any(button.label == "Permanently delete account" for button in app.button)
                    )
                    name = next(field for field in app.text_input if field.label == "Name")
                    name.set_value("Settings Tester")
                    app = self.click_button(app, "Save profile")
                    self.assert_no_streamlit_exception(app)
                    self.assertTrue(any(message.value == "Profile saved." for message in app.success))

                    variant = next(
                        field
                        for field in app.selectbox
                        if field.label == "Default FIRE variant"
                    )
                    variant.select("coast")
                    app = self.click_button(app, "Save financial assumptions")
                    self.assert_no_streamlit_exception(app)
                    self.assertTrue(
                        any(
                            message.value == "Financial assumptions saved."
                            for message in app.success
                        )
                    )

                    with db_module.get_connection() as connection:
                        saved_settings = connection.execute(
                            """
                            SELECT users.name, fire_profiles.fire_variant
                            FROM users
                            JOIN fire_profiles ON fire_profiles.user_id = users.id
                            WHERE users.id = ?
                            """,
                            (int(app.session_state["user"]["id"]),),
                        ).fetchone()
                    self.assertEqual(saved_settings["name"], "Settings Tester")
                    self.assertEqual(saved_settings["fire_variant"], "coast")

    def test_registration_displays_synthetic_data_notice(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)

        app = self.click_button(app, "Create an account")

        self.assert_no_streamlit_exception(app)
        self.assertTrue(
            any(message.value == SYNTHETIC_DATA_NOTICE for message in app.warning)
        )


if __name__ == "__main__":
    unittest.main()
