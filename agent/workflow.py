
from threading import Lock

from agent.workflow_state import WorkflowState
from agent.workflow_manager import WorkflowStateManager
from agent.controller import run_regression_tests, JSON_REPORT
from agent.result_parser import parse_report
from agent.failure_analyzer import classify_failure
from agent.investigation_strategy import select_investigation_strategy


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

        # Store recommended investigation plans for failed tests.
        self.investigation_plans = None

        # Store the final structured workflow result for the dashboard.
        self.workflow_result = None

    def get_state(self) -> WorkflowState:
        """Return the current workflow state."""

        # Retrieve the state managed by WorkflowStateManager.
        return self.state_manager.get_state()

    
    def try_start(self) -> bool:
        """
        Attempt to start a new workflow execution.

        Reject concurrent requests and reset previous execution
        data only after a new workflow has been accepted.
        """

        # Protect the execution admission process.
        with self._admission_lock:
            current_state = self.get_state()

            # Reject requests while another workflow is active.
            if not can_start_execution(current_state):
                return False

            # Transition to EXECUTING before resetting previous results.
            if not self.state_manager.transition_to(
                WorkflowState.EXECUTING
            ):
                return False

            # Clear the previous Playwright report summary.
            self.report_summary = None

            # Clear investigation plans from the previous execution.
            self.investigation_plans = None

            # Clear the previous final workflow result.
            self.workflow_result = None

            # Confirm that the new execution request was accepted.
            return True


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


    def build_investigation_plans(self) -> list[dict]:
        """
        Classify failed tests and generate investigation plans.

        This method reuses the parsed report summary instead of
        reading the Playwright JSON report again.
        """

        # Generate investigation plans only during the INVESTIGATING stage.
        if self.get_state() != WorkflowState.INVESTIGATING:
            raise RuntimeError(
                "Cannot build investigation plans outside INVESTIGATING state"
            )

        # Verify that the regression report has already been parsed.
        if self.report_summary is None:
            raise RuntimeError(
                "Cannot build investigation plans without a report summary"
            )

        # Prepare a collection for investigation recommendations.
        plans = []

        # Process each failed test from the existing report summary.
        for failure in self.report_summary["failures"]:

            # Classify the failure using predefined error patterns.
            classification = classify_failure(
                failure["errors"]
            )

            # Select recommended actions for the identified failure.
            actions = select_investigation_strategy(
                classification
            )

            # Store the classification and recommended actions.
            plans.append({
                "test_name": failure["name"],
                "project": failure["project"],
                "classification": classification,
                "errors": failure["errors"],
                "actions": actions,
            })

        # Save investigation plans for later workflow stages.
        self.investigation_plans = plans

        # Return the generated investigation plans.
        return plans


    def advance_after_investigation(self) -> WorkflowState:
        """
        Move the workflow to REPORTING after investigation
        plans have been generated successfully.
        """

        # Verify that the workflow is in the investigation stage.
        if self.get_state() != WorkflowState.INVESTIGATING:
            raise RuntimeError(
                "Cannot advance outside INVESTIGATING state"
            )

        # Ensure that investigation planning has completed.
        if self.investigation_plans is None:
            raise RuntimeError(
                "Investigation plans have not been generated"
            )

        # Transition to the reporting stage.
        if not self.state_manager.transition_to(
            WorkflowState.REPORTING
        ):
            raise RuntimeError(
                "Cannot transition to REPORTING"
            )

        # Return the updated workflow state.
        return self.get_state()


    
    def complete_reporting(self) -> dict:
        """
        Generate the final workflow result and mark processing complete.

        If reporting fails after reaching REPORTING, transition
        the workflow to ERROR and propagate the exception.
        """

        # Reject reporting requests from an invalid workflow state.
        if self.get_state() != WorkflowState.REPORTING:
            raise RuntimeError(
                "Cannot complete workflow outside REPORTING state"
            )

        try:
            # Verify that a parsed regression report is available.
            if self.report_summary is None:
                raise RuntimeError(
                    "Cannot complete workflow without a report summary"
                )

            # Require investigation plans when failed tests are present.
            if (
                self.report_summary["failures"]
                and self.investigation_plans is None
            ):
                raise RuntimeError(
                    "Cannot complete reporting without investigation plans"
                )

            # Prepare a structured result for the NiceGUI dashboard.
            final_result = {
                "workflow_status": WorkflowState.COMPLETED.value,
                "test_summary": self.report_summary,
                "investigation_plans": self.investigation_plans or [],
            }

            # Transition to COMPLETED only after preparing the report.
            if not self.state_manager.transition_to(
                WorkflowState.COMPLETED
            ):
                raise RuntimeError(
                    "Cannot transition to COMPLETED"
                )

            # Save the final result for future dashboard access.
            self.workflow_result = final_result

            # Return the completed workflow report.
            return final_result

        except Exception:
            # Mark an active reporting failure as a workflow error.
            self.state_manager.transition_to(WorkflowState.ERROR)

            # Preserve the original exception for troubleshooting.
            raise



    def complete_partial_reporting(
        self,
        investigation_error: Exception
    ) -> dict:
        """
        Preserve valid test results when investigation planning fails.

        A workflow is PARTIALLY_COMPLETED only when a usable
        partial report has been generated successfully.
        """

        # Allow recovery only when the investigation stage is active.
        if self.get_state() != WorkflowState.INVESTIGATING:
            raise RuntimeError(
                "Cannot recover outside INVESTIGATING state"
            )

        # A valid parsed report is required for partial completion.
        if self.report_summary is None:
            raise RuntimeError(
                "Cannot create partial report without test results"
            )

        try:
            # Move to reporting to preserve available execution data.
            if not self.state_manager.transition_to(
                WorkflowState.REPORTING
            ):
                raise RuntimeError(
                    "Cannot transition to REPORTING"
                )

            # Prepare a partial report with the investigation error.
            partial_result = {
                "workflow_status": WorkflowState.PARTIALLY_COMPLETED.value,
                "test_summary": self.report_summary,
                "investigation_plans": self.investigation_plans or [],
                "failed_stage": WorkflowState.INVESTIGATING.value,
                "investigation_error": (
                    str(investigation_error)
                    or type(investigation_error).__name__
                ),
            }

            # Mark the workflow as partially completed.
            if not self.state_manager.transition_to(
                WorkflowState.PARTIALLY_COMPLETED
            ):
                raise RuntimeError(
                    "Cannot transition to PARTIALLY_COMPLETED"
                )

            # Save the partial result for the dashboard.
            self.workflow_result = partial_result

            # Return the available workflow results.
            return partial_result

        except Exception:
            # Mark the workflow as ERROR if partial reporting also fails.
            self.state_manager.transition_to(WorkflowState.ERROR)

            # Propagate the reporting exception for debugging.
            raise



    def advance_after_analysis(self) -> WorkflowState:
        """
        Select the next workflow stage based on parsed test results.

        Failed tests require investigation planning.
        Reports without failed tests proceed directly to reporting.
        """

        # Verify that the workflow is currently analyzing results.
        if self.get_state() != WorkflowState.ANALYZING:
            raise RuntimeError(
                "Cannot advance workflow outside ANALYZING state"
            )

        # Ensure that the JSON report has already been parsed.
        if self.report_summary is None:
            raise RuntimeError(
                "Cannot advance workflow without a report summary"
            )

        # Choose the next workflow state based on failed test records.
        if self.report_summary["failures"]:
            next_state = WorkflowState.INVESTIGATING
        else:
            next_state = WorkflowState.REPORTING

        # Validate and perform the workflow state transition.
        if not self.state_manager.transition_to(next_state):
            raise RuntimeError(
                f"Cannot transition to {next_state.value}"
            )

        # Return the updated state for the calling component.
        return self.get_state()



    def run_workflow(self) -> dict | None:
        """
        Coordinate the complete Playwright regression workflow.

        Return the final workflow result when processing finishes.
        Return None when a new execution request is rejected.
        """

        # Execute Playwright and reject duplicate execution requests.
        # The controller returns an integer exit code when accepted.
        exit_code = self.execute_regression()

        # None indicates that another workflow is already active.
        if exit_code is None:
            return None

        try:
            # Parse and validate the generated Playwright JSON report.
            self.analyze_report()

            # Choose INVESTIGATING or REPORTING based on test failures.
            next_state = self.advance_after_analysis()

            # Generate investigation recommendations only when needed.
            if next_state == WorkflowState.INVESTIGATING:
                try:
                    # Classify failures and generate rule-based plans.
                    self.build_investigation_plans()

                    # Move to REPORTING after investigation planning.
                    self.advance_after_investigation()

                except Exception as investigation_error:
                    # Preserve valid test results if investigation fails.
                    # The recovery method produces a partial report.
                    return self.complete_partial_reporting(
                        investigation_error
                    )

            # Generate the final report and mark the workflow COMPLETED.
            return self.complete_reporting()

        except Exception:
            # Move an unfinished workflow to ERROR on unrecoverable failure.
            # Existing stage methods may have already set ERROR.
            if self.get_state() in ACTIVE_STATES:
                self.state_manager.transition_to(
                    WorkflowState.ERROR
                )

            # Preserve the original exception for troubleshooting.
            raise

