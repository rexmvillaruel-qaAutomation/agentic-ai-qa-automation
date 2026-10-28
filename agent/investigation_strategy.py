
from agent.failure_analyzer import analyze_failures

def select_investigation_strategy(classification):
    """
    Select investigation actions based on the failure classification.

    This function defines rule-based decisions. It does not
    perform retries, modify tests, or invoke an AI model.
    """

    strategies = {
        "LOCATOR_TIMEOUT": [
            "Inspect the failed locator and source line.",
            "Check whether the expected page was reached.",
            "Review available navigation and execution evidence.",
            "Consider a controlled retry after evidence collection.",
        ],
        "ASSERTION_FAILURE": [
            "Identify the expected and actual values.",
            "Review the assertion and relevant application state.",
            "Check whether the test data matches the scenario.",
        ],
        "NAVIGATION_FAILURE": [
            "Inspect the target URL and navigation error.",
            "Check available network and page-loading evidence.",
            "Verify whether the application was reachable.",
        ],
        "GENERAL_TIMEOUT": [
            "Identify the operation that exceeded its timeout.",
            "Review execution timing and available logs.",
        ],
        "UNKNOWN_FAILURE": [
            "Collect the full error message and stack trace.",
            "Request additional evidence before suggesting a fix.",
        ],
    }

    # Use a safe fallback when the classification is not recognized.
    return strategies.get(
        classification,
        strategies["UNKNOWN_FAILURE"],
    )


def create_investigation_plans():
    """
    Generate investigation plans for failures in the JSON report.

    Returns structured plans that a future agent can execute
    or use when requesting AI-powered analysis.
    """
    failures = analyze_failures()
    plans = []

    for failure in failures:
        actions = select_investigation_strategy(
            failure["classification"]
        )

        plans.append({
            "test_name": failure["test_name"],
            "classification": failure["classification"],
            "actions": actions,
        })

    return plans


if __name__ == "__main__":
    plans = create_investigation_plans()

    if not plans:
        print("No failures require investigation.")

    for plan in plans:
        print(f"TEST: {plan['test_name']}")
        print(f"CLASSIFICATION: {plan['classification']}")
        print("INVESTIGATION PLAN:")

        for number, action in enumerate(plan["actions"], start=1):
            print(f"{number}. {action}")
