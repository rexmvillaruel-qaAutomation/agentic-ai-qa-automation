
from agent.result_parser import parse_report


def classify_failure(error_messages):
    """
    Classify a Playwright failure using known error patterns.

    This function uses deterministic rules, not an AI model.
    The classification helps the agent select an appropriate
    investigation strategy later.
    """
    error_text = " ".join(error_messages).lower()

    # Detect timeout failures related to Playwright locators.
    if "locator." in error_text and "timeout" in error_text:
        return "LOCATOR_TIMEOUT"

    # Detect assertion failures before checking generic timeouts.
    if "expect(" in error_text or "expect(received)" in error_text:
        return "ASSERTION_FAILURE"

    # Detect navigation or page-loading failures.
    if "page.goto" in error_text or "net::err_" in error_text:
        return "NAVIGATION_FAILURE"

    # Detect timeouts that do not match a more specific pattern.
    if "timeout" in error_text or "timed out" in error_text:
        return "GENERAL_TIMEOUT"

    # Keep unrecognized failures available for further investigation.
    return "UNKNOWN_FAILURE"


def analyze_failures():
    """
    Read the Playwright report and classify each failed test.

    Returns a list of failure records that can later be passed
    to an AI model for evidence-based investigation.
    """
    summary = parse_report()
    analyzed_failures = []

    for failure in summary["failures"]:
        classification = classify_failure(failure["errors"])

        analyzed_failures.append({
            "test_name": failure["name"],
            "project": failure["project"],
            "classification": classification,
            "errors": failure["errors"],
        })

    return analyzed_failures


if __name__ == "__main__":
    failures = analyze_failures()

    if not failures:
        print("No failed tests found in the current report.")

    for failure in failures:
        print("FAILURE ANALYSIS")
        print(f"Test: {failure['test_name']}")
        print(f"Project: {failure['project']}")
        print(f"Classification: {failure['classification']}")
        print("Investigation Status: Pending AI analysis")
