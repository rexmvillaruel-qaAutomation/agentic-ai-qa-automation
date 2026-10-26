
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PLAYWRIGHT_ROOT = (
    PROJECT_ROOT.parent / "playwright-ecommerce-framework"
)


def run_regression_tests():
    if not PLAYWRIGHT_ROOT.is_dir():
        raise FileNotFoundError(
            f"Playwright framework not found: {PLAYWRIGHT_ROOT}"
        )

    command = [
        "npx.cmd",
        "--no-install",
        "playwright",
        "test",
        "tests/regression",
        "--project=chromium",
        "--reporter=line",
    ]

    print("Starting Playwright regression tests...", flush=True)

# Pinapatakbo ng Python ang Playwright CLI
    result = subprocess.run(
        command,
        
# Ginagamit ang Project #1 directory para mahanap ang existing tests at configuration.
        cwd=PLAYWRIGHT_ROOT,
        check=False,
    )

    print(
        f"Playwright execution finished with exit code: "
        f"{result.returncode}"
    )

    return result.returncode


if __name__ == "__main__":
    run_regression_tests()
