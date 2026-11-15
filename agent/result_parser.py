import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
JSON_REPORT = PROJECT_ROOT / "reports" / "regression-results.json"



def collect_tests(suites):
    """
    Recursively collect test results from nested Playwright suites.

    Playwright groups tests into suites, so this function
    traverses each level to retrieve all test results.
    """
    tests = []

    for suite in suites:
        for spec in suite.get("specs", []):
            for test in spec.get("tests", []):
                tests.append({
                    "name": spec.get("title"),
                    "project": test.get("projectName"),
                    "status": test.get("status"),
                    "results": test.get("results", []),
                })

        tests.extend(collect_tests(suite.get("suites", [])))

    return tests


def parse_report():
    
    """Read, validate, and summarize a Playwright JSON report."""

    # Verify that the JSON report exists before reading it.
    if not JSON_REPORT.is_file():
        raise FileNotFoundError(
            f"JSON report not found: {JSON_REPORT}"
        )

    # Load the JSON report from the filesystem.
    with JSON_REPORT.open("r", encoding="utf-8") as file:
        report = json.load(file)

    # Verify that the report contains a JSON object.
    if not isinstance(report, dict):
        raise ValueError("Invalid Playwright report: expected a JSON object")

    # Retrieve the required report sections.
    stats = report.get("stats")
    suites = report.get("suites")

    # Reject reports with missing or incorrect section types.
    if not isinstance(stats, dict):
        raise ValueError("Invalid Playwright report: missing stats")

    if not isinstance(suites, list):
        raise ValueError("Invalid Playwright report: missing suites")

    # Verify that the required execution statistics are present.
    required_stats = (
        "expected",
        "unexpected",
        "skipped",
        "flaky",
        "duration",
    )

    for field in required_stats:
        if field not in stats:
            raise ValueError(
                f"Invalid Playwright report: missing statistic '{field}'"
            )

        # Reject non-numeric execution statistics.
        value = stats[field]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or value < 0
        ):
            raise ValueError(
                f"Invalid Playwright report: invalid statistic '{field}'"
            )

    # Collect all tests from nested Playwright suites.
    tests = collect_tests(suites)

    # Reject reports that contain no test entries.
    if not tests:
        raise ValueError("Invalid Playwright report: no tests found")

    failures = []

    # Extract error messages from unexpectedly failed tests.
    for test in tests:
        if test["status"] == "unexpected":
            errors = []

            for result in test["results"]:
                for error in result.get("errors", []):
                    errors.append(error.get("message", ""))

            failures.append({
                "name": test["name"],
                "project": test["project"],
                "errors": errors,
            })

    # Return a consistent summary for the workflow orchestrator.
    return {
        "passed": stats["expected"],
        "failed": stats["unexpected"],
        "skipped": stats["skipped"],
        "flaky": stats["flaky"],
        "duration_ms": stats["duration"],
        "failures": failures,
    }


if __name__ == "__main__":
    summary = parse_report()

    print("PLAYWRIGHT REGRESSION SUMMARY")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Skipped: {summary['skipped']}")
    print(f"Flaky: {summary['flaky']}")
    print(f"Duration: {summary['duration_ms'] / 1000:.2f}s")

    for failure in summary["failures"]:
        print(f"\nFailed Test: {failure['name']}")
        print(f"Project: {failure['project']}")

        for error in failure["errors"]:
            print(f"Error: {error}")
