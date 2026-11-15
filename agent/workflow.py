
from threading import Lock

from agent.workflow_state import WorkflowState
from agent.workflow_manager import WorkflowStateManager
from agent.controller import run_regression_tests, JSON_REPORT
from agent.result_parser import parse_report


# Define states where a workflow is actively processing.
ACTIVE_STATES = {
    WorkflowState.EXECUTING,
    WorkflowState.ANALYZING,
    WorkflowState.INVESTIGATING,
    WorkflowState.REPORTING,
}


# Define states where a workflow has finished processing.
TERMINAL_STATES = {
    WorkflowState.COMPLETED,
    WorkflowState.PARTIALLY_COMPLETED,
    WorkflowState.ERROR,
}


def can_start_execution(current_state: WorkflowState) -> bool:
    """Check whether a new workflow execution is allowed."""

    # Allow execution when no workflow has started.
    if current_state == WorkflowState.IDLE:
        return True

    # Allow a new execution after a previous workflow has finished.
    if current_state in TERMINAL_STATES:
        return True

    # Reject execution requests for all other states.
    return False


class WorkflowOrchestrator:
    def __init__(self):
        # Manage the current workflow state and transitions.
        self.state_manager = WorkflowStateManager()

        # Prevent simultaneous execution admission requests.
        self._admission_lock = Lock()

        # Store the parsed Playwright report summary.
        # None indicates that no report has been analyzed yet.
        self.report_summary = None

    def get_state(self) -> WorkflowState:
        """Return the current workflow state."""

        # Retrieve the state managed by WorkflowStateManager.
        return self.state_manager.get_state()

    def try_start(self) -> bool:
        """Attempt to start a new workflow execution."""

        # Protect the admission check and state transition.
        with self._admission_lock:
            current_state = self.get_state()

            # Reject the request if a workflow is already active.
            if not can_start_execution(current_state):
                return False

            # Reserve execution by transitioning to EXECUTING.
            return self.state_manager.transition_to(
                WorkflowState.EXECUTING
            )

    def execute_regression(self) -> int | None:
        """Execute Playwright and prepare the workflow for analysis."""

        # Reject duplicate execution requests.
        if not self.try_start():
            return None

        try:
            # Execute the existing Playwright regression controller.
            exit_code = run_regression_tests()

            # Verify that the controller generated a JSON report.
            if not JSON_REPORT.is_file():
                raise FileNotFoundError(
                    f"Playwright JSON report missing: {JSON_REPORT}"
                )

            # Move the workflow to the analysis stage.
            if not self.state_manager.transition_to(
                WorkflowState.ANALYZING
            ):
                raise RuntimeError(
                    "Cannot transition to ANALYZING"
                )

            # Return the Playwright process exit code.
            return exit_code

        except Exception:
            # Move the workflow to ERROR if execution fails.
            self.state_manager.transition_to(WorkflowState.ERROR)
            raise

    def analyze_report(self) -> dict:
        """Parse and store the Playwright regression summary."""

        # Allow report analysis only during the ANALYZING state.
        if self.get_state() != WorkflowState.ANALYZING:
            raise RuntimeError(
                "Cannot analyze report outside ANALYZING state"
            )

        try:
            # Parse and validate the Playwright JSON report.
            summary = parse_report()

            # Store the summary for future workflow stages.
            self.report_summary = summary

            # Return the parsed summary to the caller.
            return summary

        except Exception:
            # Move the workflow to ERROR if report parsing fails.
            self.state_manager.transition_to(WorkflowState.ERROR)

            # Propagate the original exception for debugging.
            raise
