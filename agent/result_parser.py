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
    """Read a Playwright JSON report and return a summary."""
    if not JSON_REPORT.exists():
        raise FileNotFoundError(f"JSON report not found: {JSON_REPORT}")

    with JSON_REPORT.open("r", encoding="utf-8") as file:
        report = json.load(file)

    stats = report.get("stats", {})
    tests = collect_tests(report.get("suites", []))

    failures = []

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

    return {
        "passed": stats.get("expected", 0),
        "failed": stats.get("unexpected", 0),
        "skipped": stats.get("skipped", 0),
        "flaky": stats.get("flaky", 0),
        "duration_ms": stats.get("duration", 0),
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
