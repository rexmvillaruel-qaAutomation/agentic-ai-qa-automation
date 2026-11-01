
"""
NiceGUI dashboard for the Agentic AI QA Automation project.

Displays actual regression metrics from the Playwright JSON report.
"""

import json
from pathlib import Path

# Import the NiceGUI application server and UI components.
# app serves static robot assets, while ui builds the dashboard.
from nicegui import app, ui


# Resolve the CSS file relative to this dashboard module.
STYLES_PATH = Path(__file__).resolve().parent / "styles.css"

# Load the stylesheet so NiceGUI components can use custom classes.
ui.add_css(STYLES_PATH.read_text(encoding="utf-8"))

# Resolve the project root independently of the terminal's directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "reports" / "regression-results.json"

# Expose only the dashboard asset directory to the local web server.
# This allows CSS to load the robot PNG files through /assets/.
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
app.add_static_files("/assets", str(ASSETS_DIR))

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
        # Build the animated workspace without changing the regression cards.
        with ui.card().classes("dashboard-panel w-full"):
            ui.label("AGENT WORKSPACE").classes("panel-heading")

            # Workstation positions correspond to the agent's workflow stages.
           
            # Define the four QA workflow workstations.
            # Each workstation has a distinct visual identity.
            stations = [
                ("▶", "EXECUTE", "execute"),
                ("▥", "ANALYZE", "analyze"),
                ("⌕", "INVESTIGATE", "investigate"),
                ("▤", "REPORT", "report"),
            ]


            with ui.element("div").classes("pixel-workspace"):

                # Display the four stations in execution order.
                with ui.element("div").classes("workstation-grid"):
                    
                    # Render each station with its workflow-specific theme.
                    for symbol, name, station_type in stations:
                        with ui.element("div").classes(
                            f"workstation workstation-{station_type}"
                        ):
                            ui.label(symbol).classes("workstation-icon")
                            ui.label(name).classes("workstation-name")


                # Keep a reference so Python can update the robot's position.
                robot = ui.element("div").classes(
                    "pixel-agent station-0"
                )

            # This button demonstrates movement only.
            # Actual execution-state integration comes in a later step.
            current_station = {"index": 0}

          
            def move_agent():
                """
                Move the robot to the next workstation.

                Stop the current work animation before walking,
                then return to idle when the movement finishes.
                """
                # Prevent starting another movement while already walking.
                if "walking" in robot._classes:
                    return

                
                # Stop all four work animations before the robot walks.
                robot.classes(
                    remove=(
                        "working-execute "
                        "working-analyze "
                        "working-investigate "
                        "working-report"
                    )
                )
                
                # Calculate the next workstation position.
                previous_index = current_station["index"]
                next_index = (previous_index + 1) % len(stations)

                # Change position and activate the walking sprite.
                robot.classes(
                    remove=f"station-{previous_index}",
                    add=f"station-{next_index} walking",
                )

                # Save the updated position.
                current_station["index"] = next_index

                # Return to the idle sprite after walking finishes.
                ui.timer(
                    1.2,
                    lambda: robot.classes(remove="walking"),
                    once=True,
                )

            ui.button(
                "Move Agent (Demo)",
                on_click=move_agent,
                icon="directions_walk",
            ).props("outline color=primary")

            ui.label(
                "Demo mode — workstation movement is not yet linked to test execution."
            ).classes("dashboard-subtitle")

        

            def toggle_execute_work():
                """
                Toggle the Execute workstation's typing animation.

                This is a visual prototype. It does not start a real
                Playwright test run or modify the Python agent backend.
                """
                # Work animation is only available at the Execute station.
                if current_station["index"] != 0:
                    ui.notify(
                        "Move the robot to Execute before starting work.",
                        type="warning",
                    )
                    return

                # Switch between the idle and typing sprite sheets.
                if "working-execute" in robot._classes:
                    robot.classes(remove="working-execute")
                else:
                    robot.classes(remove="walking", add="working-execute")

            ui.button(
                "Start / Stop Typing (Demo)",
                on_click=toggle_execute_work,
                icon="keyboard",
            ).props("outline color=secondary")


            def toggle_analyze_work():
                """
                Toggle the robot's test-result analysis animation.

                This demonstrates the visual analysis state only.
                It does not parse or modify Playwright reports.
                """
                # Analyze is the second workstation (index 1).
                if current_station["index"] != 1:
                    ui.notify(
                        "Move the robot to Analyze before starting work.",
                        type="warning",
                    )
                    return

                # Switch between idle and the analysis sprite.
                if "working-analyze" in robot._classes:
                    robot.classes(remove="working-analyze")
                else:
                    robot.classes(
                        remove="walking working-execute",
                        add="working-analyze",
                    )

            ui.button(
                "Start / Stop Analyze (Demo)",
                on_click=toggle_analyze_work,
                icon="analytics",
            ).props("outline color=secondary")

            
            def toggle_investigate_work():
                """
                Toggle the robot's failure-investigation animation.

                This demonstrates the visual investigation state.
                It does not execute actual failure analysis.
                """
                # Prevent changing work states while the robot is walking.
                if "walking" in robot._classes:
                    ui.notify(
                        "Wait until the robot finishes walking.",
                        type="warning",
                    )
                    return

                # Investigate is the third workstation (index 2).
                if current_station["index"] != 2:
                    ui.notify(
                        "Move the robot to Investigate first.",
                        type="warning",
                    )
                    return

                # Switch between the idle and investigation sprites.
                if "working-investigate" in robot._classes:
                    robot.classes(remove="working-investigate")
                else:
                    robot.classes(
                        remove="working-execute working-analyze",
                        add="working-investigate",
                    )

            ui.button(
                "Start / Stop Investigate (Demo)",
                on_click=toggle_investigate_work,
                icon="search",
            ).props("outline color=secondary")


            
            def toggle_report_work():
                """
                Toggle the robot's report-writing animation.

                This is a visual demonstration only.
                Actual report generation will be connected later.
                """
                # Prevent starting work while the robot is walking.
                if "walking" in robot._classes:
                    ui.notify(
                        "Wait until the robot finishes walking.",
                        type="warning",
                    )
                    return

                # Report is the fourth workstation (index 3).
                if current_station["index"] != 3:
                    ui.notify(
                        "Move the robot to Report first.",
                        type="warning",
                    )
                    return

                # Toggle between the reporting and idle sprites.
                if "working-report" in robot._classes:
                    robot.classes(remove="working-report")
                else:
                    robot.classes(
                        remove=(
                            "working-execute "
                            "working-analyze "
                            "working-investigate"
                        ),
                        add="working-report",
                    )

            ui.button(
                "Start / Stop Report (Demo)",
                on_click=toggle_report_work,
                icon="description",
            ).props("outline color=secondary")

# Initialize the dashboard and start its local web server.
create_dashboard()

ui.run(
    title="Agentic AI QA Automation",
    host="127.0.0.1",
    port=8080,
    reload=False,
)
