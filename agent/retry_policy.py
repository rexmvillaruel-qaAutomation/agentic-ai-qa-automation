
"""
Define safety rules for automated Playwright test retries.

The retry policy determines whether a failed test is eligible
for another execution. It does not execute tests itself.
"""

MAX_RETRIES = 1

RETRYABLE_FAILURES = {
    "LOCATOR_TIMEOUT",
    "NAVIGATION_FAILURE",
    "GENERAL_TIMEOUT",
}

def should_retry(classification: str, retry_count: int) -> bool:
    """
    Determine whether a failed test is eligible for retry.

    Args:
        classification: The failure category detected by the analyzer.
        retry_count: Number of retries already attempted.

    Returns:
        True if another retry is allowed; otherwise False.
    """

    # Never exceed the configured retry limit.
    if retry_count >= MAX_RETRIES:
        return False

    # Only retry failures that match an approved category.
    return classification in RETRYABLE_FAILURES


if __name__ == "__main__":
    # Verify the retry policy using representative failure cases.
    test_cases = [
        ("LOCATOR_TIMEOUT", 0),
        ("LOCATOR_TIMEOUT", 1),
        ("ASSERTION_FAILURE", 0),
        ("NAVIGATION_FAILURE", 0),
        ("UNKNOWN_FAILURE", 0),
    ]

    for classification, retry_count in test_cases:
        decision = should_retry(classification, retry_count)

        print(
            f"Classification: {classification} | "
            f"Retries: {retry_count} | "
            f"Allowed: {decision}"
        )
