
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json

from agent.result_parser import parse_report


class TestResultParserValidation(unittest.TestCase):

    def test_invalid_report_structure_is_rejected(self):
        # Create an isolated temporary directory for the test.
        with TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "regression-results.json"

            # Write an incomplete JSON report.
            report_path.write_text("{}", encoding="utf-8")

            # Redirect the parser to the temporary report file.
            with patch(
                "agent.result_parser.JSON_REPORT",
                report_path
            ):
                # Verify that an invalid report raises ValueError.
                with self.assertRaises(ValueError):
                    parse_report()

    def test_valid_report_returns_correct_summary(self):
        # Create a temporary directory to avoid modifying real reports.
        with TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "regression-results.json"

            # Prepare a sample Playwright report with one passed
            # test and one failed test.
            sample_report = {
                "stats": {
                    "expected": 1,
                    "unexpected": 1,
                    "skipped": 0,
                    "flaky": 0,
                    "duration": 1500,
                },
                "suites": [
                    {
                        "title": "Regression Tests",
                        "specs": [
                            {
                                "title": "Successful checkout",
                                "tests": [
                                    {
                                        "projectName": "chromium",
                                        "status": "expected",
                                        "results": [],
                                    }
                                ],
                            },
                            {
                                "title": "Failed checkout",
                                "tests": [
                                    {
                                        "projectName": "chromium",
                                        "status": "unexpected",
                                        "results": [
                                            {
                                                "errors": [
                                                    {
                                                        "message": "Checkout assertion failed"
                                                    }
                                                ]
                                            }
                                        ],
                                    }
                                ],
                            },
                        ],
                    }
                ],
            }

            # Write the sample report to the temporary JSON file.
            report_path.write_text(
                json.dumps(sample_report),
                encoding="utf-8"
            )

            # Redirect the parser to the temporary report.
            with patch(
                "agent.result_parser.JSON_REPORT",
                report_path
            ):
                # Execute the real parser against the sample report.
                summary = parse_report()

            # Verify the execution statistics.
            self.assertEqual(summary["passed"], 1)
            self.assertEqual(summary["failed"], 1)
            self.assertEqual(summary["skipped"], 0)
            self.assertEqual(summary["flaky"], 0)
            self.assertEqual(summary["duration_ms"], 1500)

            # Verify that exactly one failure was collected.
            self.assertEqual(len(summary["failures"]), 1)

            # Verify the failed test details.
            failure = summary["failures"][0]

            self.assertEqual(failure["name"], "Failed checkout")
            self.assertEqual(failure["project"], "chromium")
            self.assertEqual(
                failure["errors"],
                ["Checkout assertion failed"]
            )
        
        