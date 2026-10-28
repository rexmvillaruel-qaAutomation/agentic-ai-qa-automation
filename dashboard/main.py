
"""
NiceGUI dashboard for the Agentic AI QA Automation project.

Displays actual regression metrics from the Playwright JSON report.
"""

import json
from pathlib import Path

from nicegui import ui


# Resolve the CSS file relative to this dashboard module.
STYLES_PATH = Path(__file__).resolve().parent / "styles.css"

# Load the stylesheet so NiceGUI components can use custom classes.
ui.add_css(STYLES_PATH.read_text(encoding="utf-8"))

# Resolve the project root independently of the terminal's directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "reports" / "regression-results.json"


def load_regression_metrics():
    """
    Read the latest Playwright JSON report and return summary metrics.

    Return None when no report exists so the dashboard can display
    an appropriate empty state instead of fabricated test results.
    """
    if not REPORT_PATH.exists():
        return None

    try:
        with REPORT_PATH.open(encoding="utf-8") as report_file:
            report = json.load(report_file)

        stats = report.get("stats", {})

        return {
            "passed": stats.get("expected", 0),
            "failed": stats.get("unexpected", 0),
            "skipped": stats.get("skipped", 0),
            "flaky": stats.get("flaky", 0),
            "duration_ms": stats.get("duration", 0),
        }

    except (OSError, json.JSONDecodeError):
        # Keep the dashboard usable if the report is missing or invalid.
        return None



def create_dashboard():
    """
    Build the modern QA dashboard using actual Playwright metrics.

    The layout separates test results from the future animated
    agent workspace so each feature can evolve independently.
    """
    ui.dark_mode().enable()

    # Load the latest saved Playwright regression report.
    metrics = load_regression_metrics()

    with ui.column().classes("dashboard-container gap-6"):

        # Application header and dashboard description.
        with ui.column().classes("gap-1"):
            ui.label("AGENTIC AI QA AUTOMATION").classes(
                "dashboard-title"
            )
            ui.label(
                "Automation Control Center | Playwright + Python"
            ).classes("dashboard-subtitle")

        # Show the current dashboard initialization status.
        with ui.card().classes("dashboard-panel w-full"):
            ui.label("SYSTEM STATUS").classes("panel-heading")
            ui.label(
                "Dashboard initialized successfully"
            ).classes("text-green-400")

        # Regression metrics are sourced from the JSON report.
        with ui.card().classes("dashboard-panel w-full"):
            ui.label("REGRESSION SUMMARY").classes("panel-heading")

            if metrics is None:
                ui.label("No valid Playwright report found.").classes(
                    "text-yellow-400"
                )
            else:
                duration_seconds = metrics["duration_ms"] / 1000

                # Each metric card displays a value from the report.
                with ui.element("div").classes("metrics-grid"):
                    for label, value, color_class in [
                        ("Passed", metrics["passed"], "metric-passed"),
                        ("Failed", metrics["failed"], "metric-failed"),
                        ("Skipped", metrics["skipped"], ""),
                        ("Duration", f"{duration_seconds:.2f}s", "metric-duration"),
                    ]:
                        with ui.card().classes("metric-card"):
                            ui.label(label).classes("metric-label")
                            ui.label(str(value)).classes(
                                f"metric-value {color_class}"
                            )

                # Flaky tests are tracked separately from failed tests.
                ui.label(
                    f"Flaky tests: {metrics['flaky']}"
                ).classes("dashboard-subtitle")

        # Placeholder for the upcoming pixel-art agent animation.
        with ui.card().classes("dashboard-panel w-full"):
            ui.label("AGENT WORKSPACE").classes("panel-heading")

            with ui.element("div").classes("agent-workspace w-full"):
                ui.label(
                    "Pixel-art agent workstation — coming next!"
                )

# Initialize the dashboard and start its local web server.
create_dashboard()

ui.run(
    title="Agentic AI QA Automation",
    host="127.0.0.1",
    port=8080,
    reload=False,
)
