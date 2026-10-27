
import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PLAYWRIGHT_ROOT = (
    PROJECT_ROOT.parent / "playwright-ecommerce-framework"
)

REPORTS_DIR = PROJECT_ROOT / "reports"
JSON_REPORT = REPORTS_DIR / "regression-results.json"


def run_regression_tests():
    if not PLAYWRIGHT_ROOT.is_dir():
        raise FileNotFoundError(
            f"Playwright framework not found: {PLAYWRIGHT_ROOT}"
        )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Remove previous report to avoid reading stale results.
    JSON_REPORT.unlink(missing_ok=True)

    command = [
        "npx.cmd",
        "--no-install",
        "playwright",
        "test",
        "tests/regression",
        "--project=chromium",
        "--reporter=json",
        "--workers=1",
    ]

    # Direct the JSON reporter to Project #2.
    env = os.environ.copy()
    env["PLAYWRIGHT_JSON_OUTPUT_FILE"] = str(JSON_REPORT)

    print("Starting Playwright regression tests...", flush=True)

# Pinapatakbo ng Python ang Playwright CLI
    result = subprocess.run(
        command,
        
# Ginagamit ang Project #1 directory para mahanap ang existing tests at configuration.
        cwd=PLAYWRIGHT_ROOT,
        env=env,
        check=False,
    )

    print(
        f"Playwright execution finished with exit code: "
        f"{result.returncode}"
    )

    if JSON_REPORT.exists():
        print(f"JSON report generated: {JSON_REPORT}")
    else:
        print("WARNING: JSON report was not generated.")

    return result.returncode


if __name__ == "__main__":
    run_regression_tests()
