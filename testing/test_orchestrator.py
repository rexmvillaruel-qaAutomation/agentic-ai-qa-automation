import unittest

from agent.workflow import WorkflowOrchestrator
from agent.workflow_state import WorkflowState
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch



class TestWorkflowOrchestrator(unittest.TestCase):
    def setUp(self):
        self.orchestrator = WorkflowOrchestrator()

    def test_initial_state_is_idle(self):
        result = self.orchestrator.get_state()

        self.assertEqual(result, WorkflowState.IDLE)

    def test_orchestrator_reflects_state_manager_transition(self):
        transition_result = self.orchestrator.state_manager.transition_to(
        WorkflowState.EXECUTING
        )
        result = self.orchestrator.get_state()

        self.assertTrue(transition_result)
        self.assertEqual(result, WorkflowState.EXECUTING)

    def test_duplicate_execution_is_rejected(self):
        first_result = self.orchestrator.try_start()
        second_result = self.orchestrator.try_start()

        self.assertTrue(first_result)
        self.assertFalse(second_result)

        current_state = self.orchestrator.get_state()

        self.assertEqual(
            current_state,
            WorkflowState.EXECUTING
        )

    def test_concurrent_execution_requests(self):
        barrier = Barrier(2)

        def request_execution():
            barrier.wait(timeout=5)
            return self.orchestrator.try_start()

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_a = executor.submit(request_execution)
            future_b = executor.submit(request_execution)

            results = [
                future_a.result(timeout=10),
                future_b.result(timeout=10)
            ]

        self.assertCountEqual(results, [True, False])

        current_state = self.orchestrator.get_state()
        
        self.assertEqual(
            current_state,
            WorkflowState.EXECUTING
        )

    def test_successful_regression_execution(self):
        with patch(
            "agent.workflow.run_regression_tests",
            return_value=0
        ) as mock_controller, patch(
            "agent.workflow.JSON_REPORT"
        ) as mock_report:

            mock_report.is_file.return_value = True

            result = self.orchestrator.execute_regression()

            self.assertEqual(result, 0)

            self.assertEqual(
                 self.orchestrator.get_state(),
                 WorkflowState.ANALYZING
                )

            mock_controller.assert_called_once()

    def test_failed_regression_still_proceeds_to_analysis(self):
        with patch(
            "agent.workflow.run_regression_tests",
            return_value=1
        ) as mock_controller, patch(
        "agent.workflow.JSON_REPORT"
        ) as mock_report:

            mock_report.is_file.return_value = True

            result = self.orchestrator.execute_regression()

            self.assertEqual(result, 1)

            self.assertEqual(
                 self.orchestrator.get_state(),
                WorkflowState.ANALYZING
                )

            mock_controller.assert_called_once()

    def test_missing_json_report_sets_error_state(self):
        with patch(
            "agent.workflow.run_regression_tests",
            return_value=0
        ) as mock_controller, patch(
        "agent.workflow.JSON_REPORT"
        ) as mock_report:

            mock_report.is_file.return_value = False

            with self.assertRaises(FileNotFoundError):
                self.orchestrator.execute_regression()

            self.assertEqual(
                self.orchestrator.get_state(),
                WorkflowState.ERROR
            )

            mock_controller.assert_called_once()

    def test_controller_exception_sets_error_state(self):
        with patch(
            "agent.workflow.run_regression_tests",
            side_effect=FileNotFoundError(
                "Playwright framework not found"
            )
        ) as mock_controller:

        # Verify that the controller exception is propagated.
            with self.assertRaises(FileNotFoundError):
                self.orchestrator.execute_regression()

        # Verify that the workflow transitions to ERROR.
            self.assertEqual(
                self.orchestrator.get_state(),
                WorkflowState.ERROR
            )

        # Verify that the controller was called exactly once.
            mock_controller.assert_called_once()

    def test_duplicate_regression_execution_is_rejected(self):
        with patch(
            "agent.workflow.run_regression_tests",
            return_value=0
        ) as mock_controller, patch(
            "agent.workflow.JSON_REPORT"
        ) as mock_report:

            mock_report.is_file.return_value = True

            # First execution request should be accepted.
            first_result = self.orchestrator.execute_regression()

        # Second request should be rejected because the workflow is active.
            second_result = self.orchestrator.execute_regression()

        # Verify that the first execution returns exit code 0.
            self.assertEqual(first_result, 0)

        # Verify that the duplicate execution is rejected.
            self.assertIsNone(second_result)

        # Verify that the workflow remains in ANALYZING.
            self.assertEqual(
                self.orchestrator.get_state(),
                WorkflowState.ANALYZING
            )

        # Verify that Playwright controller was called only once.
            mock_controller.assert_called_once()
    
    def test_analyze_report_returns_summary(self):
        # Start the workflow and transition to EXECUTING.
        self.assertTrue(self.orchestrator.try_start())

        # Move the workflow to the ANALYZING state.
        self.assertTrue(
            self.orchestrator.state_manager.transition_to(
                WorkflowState.ANALYZING
            )
        )

        # Prepare a sample Playwright regression summary.
        sample_summary = {
            "passed": 3,
            "failed": 1,
            "skipped": 0,
            "flaky": 0,
            "duration_ms": 1500,
            "failures": [
                {
                    "name": "Checkout test",
                    "project": "chromium",
                    "errors": ["Assertion failed"],
                }
            ],
        }

        # Mock the parser to avoid reading the actual JSON report.
        with patch(
            "agent.workflow.parse_report",
            return_value=sample_summary
        ) as mock_parser:

            # Execute report analysis through the orchestrator.
            result = self.orchestrator.analyze_report()

            # Verify that the parser was called exactly once.
            mock_parser.assert_called_once()

            # Verify that the returned summary matches the expected data.
            self.assertEqual(result, sample_summary)

            # Verify that the orchestrator stores the parsed summary.
            self.assertEqual(
                self.orchestrator.report_summary,
                sample_summary
            )

            # Verify that the workflow remains in ANALYZING.
            self.assertEqual(
                self.orchestrator.get_state(),
                WorkflowState.ANALYZING
            )
    
    def test_analyze_report_failure_sets_error_state(self):
        # Start the workflow.
        self.assertTrue(self.orchestrator.try_start())

        # Move the workflow to ANALYZING.
        self.assertTrue(
            self.orchestrator.state_manager.transition_to(
                WorkflowState.ANALYZING
            )
        )

        # Simulate a parsing failure caused by an invalid report.
        with patch(
            "agent.workflow.parse_report",
            side_effect=ValueError("Invalid Playwright report")
        ) as mock_parser:

            # Verify that the parser exception is propagated.
            with self.assertRaises(ValueError):
                self.orchestrator.analyze_report()

            # Verify that the parser was called exactly once.
            mock_parser.assert_called_once()

            # Verify that no report summary was stored.
            self.assertIsNone(self.orchestrator.report_summary)

            # Verify that the workflow enters ERROR state.
            self.assertEqual(
                self.orchestrator.get_state(),
                WorkflowState.ERROR
            )


    def test_build_investigation_plans_for_failed_test(self):
        # Start a new workflow execution.
        self.assertTrue(self.orchestrator.try_start())

        # Move the workflow to the analysis stage.
        self.assertTrue(
            self.orchestrator.state_manager.transition_to(
                WorkflowState.ANALYZING
            )
        )
        # Move to INVESTIGATING before testing investigation planning.
        self.assertTrue(
            self.orchestrator.state_manager.transition_to(
                WorkflowState.INVESTIGATING
            )
        )

        # Simulate a previously parsed report with one failed test.
        self.orchestrator.report_summary = {
            "passed": 2,
            "failed": 1,
            "skipped": 0,
            "flaky": 0,
            "duration_ms": 1500,
            "failures": [
                {
                    "name": "Checkout button test",
                    "project": "chromium",
                    "errors": [
                        "locator.click: Timeout 30000ms exceeded"
                    ],
                }
            ],
        }

        # Generate investigation plans using the existing modules.
        plans = self.orchestrator.build_investigation_plans()

        # Verify that one investigation plan was generated.
        self.assertEqual(len(plans), 1)

        # Verify that the failure was classified correctly.
        self.assertEqual(
            plans[0]["classification"],
            "LOCATOR_TIMEOUT"
        )

        # Verify the failed test details.
        self.assertEqual(
            plans[0]["test_name"],
            "Checkout button test"
        )

        # Verify that the investigation strategy contains actions.
        self.assertGreater(len(plans[0]["actions"]), 0)

        # Verify that investigation plans were stored.
        self.assertEqual(
            self.orchestrator.investigation_plans,
            plans
        )

    
    def test_build_investigation_plans_without_failures(self):
        # Start a new workflow execution.
        self.assertTrue(self.orchestrator.try_start())

        # Move the workflow to the analysis stage.
        self.assertTrue(
            self.orchestrator.state_manager.transition_to(
                WorkflowState.ANALYZING
            )
        )

      # Move to INVESTIGATING before testing investigation planning.
        self.assertTrue(
            self.orchestrator.state_manager.transition_to(
                WorkflowState.INVESTIGATING
            )
        )
        

        # Simulate a parsed report where all tests passed.
        self.orchestrator.report_summary = {
            "passed": 3,
            "failed": 0,
            "skipped": 0,
            "flaky": 0,
            "duration_ms": 1500,
            "failures": [],
        }

        # Generate investigation plans from the report summary.
        plans = self.orchestrator.build_investigation_plans()

        # Verify that no investigation plans were generated.
        self.assertEqual(plans, [])

        # Verify that the empty result was stored correctly.
        self.assertEqual(
            self.orchestrator.investigation_plans,
            []
        )

    
    def test_failed_tests_proceed_to_investigating(self):
        # Start a new workflow execution.
        self.assertTrue(self.orchestrator.try_start())

        # Simulate successful completion of the execution stage.
        self.assertTrue(
            self.orchestrator.state_manager.transition_to(
                WorkflowState.ANALYZING
            )
        )

        # Simulate a parsed report containing one failed test.
        self.orchestrator.report_summary = {
            "failed": 1,
            "failures": [
                {
                    "name": "Checkout test",
                    "project": "chromium",
                    "errors": ["locator.click: Timeout exceeded"],
                }
            ],
        }

        # Advance the workflow based on the parsed results.
        next_state = self.orchestrator.advance_after_analysis()

        # Verify that failed tests require investigation.
        self.assertEqual(next_state, WorkflowState.INVESTIGATING)

        # Verify that the state manager stores the new state.
        self.assertEqual(
            self.orchestrator.get_state(),
            WorkflowState.INVESTIGATING
        )

    
    def test_no_failures_proceed_to_reporting(self):
        # Start a new workflow execution.
        self.assertTrue(self.orchestrator.try_start())

        # Move the workflow to the analysis stage.
        self.assertTrue(
            self.orchestrator.state_manager.transition_to(
                WorkflowState.ANALYZING
            )
        )

        # Simulate a report where all tests passed.
        self.orchestrator.report_summary = {
            "failed": 0,
            "failures": [],
        }

        # Advance the workflow after analysis.
        next_state = self.orchestrator.advance_after_analysis()

        # Verify that workflows without failures skip investigation.
        self.assertEqual(next_state, WorkflowState.REPORTING)

        # Verify that the current state is REPORTING.
        self.assertEqual(
            self.orchestrator.get_state(),
            WorkflowState.REPORTING
        )


    def test_cannot_advance_without_report_summary(self):
        # Start a new workflow execution.
        self.assertTrue(self.orchestrator.try_start())

        # Move to ANALYZING without storing a report summary.
        self.assertTrue(
            self.orchestrator.state_manager.transition_to(
                WorkflowState.ANALYZING
            )
        )

        # Verify that advancing without parsed results is rejected.
        with self.assertRaises(RuntimeError):
            self.orchestrator.advance_after_analysis()

        # Verify that the rejected request preserves the current state.
        self.assertEqual(
            self.orchestrator.get_state(),
            WorkflowState.ANALYZING
        )

    
    def test_investigation_advances_to_reporting(self):
        # Start the workflow.
        self.assertTrue(self.orchestrator.try_start())

        # Move to the analysis stage.
        self.assertTrue(
            self.orchestrator.state_manager.transition_to(
                WorkflowState.ANALYZING
            )
        )

        # Simulate parsed results containing one failed test.
        self.orchestrator.report_summary = {
            "failed": 1,
            "failures": [
                {
                    "name": "Checkout test",
                    "project": "chromium",
                    "errors": [
                        "locator.click: Timeout 30000ms exceeded"
                    ],
                }
            ],
        }

        # Route the workflow to INVESTIGATING.
        self.assertEqual(
            self.orchestrator.advance_after_analysis(),
            WorkflowState.INVESTIGATING
        )

        # Generate rule-based investigation recommendations.
        plans = self.orchestrator.build_investigation_plans()

        # Verify that an investigation plan exists.
        self.assertEqual(len(plans), 1)

        # Advance to reporting after investigation planning.
        next_state = self.orchestrator.advance_after_investigation()

        # Verify the final state for this stage.
        self.assertEqual(
            next_state,
            WorkflowState.REPORTING
        )


    def test_cannot_advance_investigation_without_plans(self):
        # Start the workflow.
        self.assertTrue(self.orchestrator.try_start())

        # Move to the analysis stage.
        self.assertTrue(
            self.orchestrator.state_manager.transition_to(
                WorkflowState.ANALYZING
            )
        )

        # Enter INVESTIGATING without generating plans.
        self.assertTrue(
            self.orchestrator.state_manager.transition_to(
                WorkflowState.INVESTIGATING
            )
        )

        # Verify that reporting cannot start without plans.
        with self.assertRaises(RuntimeError):
            self.orchestrator.advance_after_investigation()

        # Verify that the workflow state remains unchanged.
        self.assertEqual(
            self.orchestrator.get_state(),
            WorkflowState.INVESTIGATING
        )


    def test_complete_reporting_without_failures(self):
        # Start the workflow execution.
        self.assertTrue(self.orchestrator.try_start())

        # Move to the analysis stage.
        self.assertTrue(
            self.orchestrator.state_manager.transition_to(
                WorkflowState.ANALYZING
            )
        )

        # Simulate a valid report with all tests passing.
        self.orchestrator.report_summary = {
            "passed": 3,
            "failed": 0,
            "skipped": 0,
            "flaky": 0,
            "duration_ms": 1500,
            "failures": [],
        }

        # Skip investigation and proceed to reporting.
        self.assertEqual(
            self.orchestrator.advance_after_analysis(),
            WorkflowState.REPORTING
        )

        # Generate the final workflow result.
        result = self.orchestrator.complete_reporting()

        # Verify successful workflow completion.
        self.assertEqual(
            result["workflow_status"],
            "COMPLETED"
        )

        # Verify that no investigation plans were needed.
        self.assertEqual(
            result["investigation_plans"],
            []
        )

        # Verify the final state and saved result.
        self.assertEqual(
            self.orchestrator.get_state(),
            WorkflowState.COMPLETED
        )
        self.assertEqual(
            self.orchestrator.workflow_result,
            result
        )


    def test_complete_reporting_with_failed_tests(self):
        # Start execution and enter the analysis stage.
        self.assertTrue(self.orchestrator.try_start())
        self.assertTrue(
            self.orchestrator.state_manager.transition_to(
                WorkflowState.ANALYZING
            )
        )

        # Simulate a report containing one failed Playwright test.
        self.orchestrator.report_summary = {
            "passed": 2,
            "failed": 1,
            "skipped": 0,
            "flaky": 0,
            "duration_ms": 1500,
            "failures": [
                {
                    "name": "Checkout test",
                    "project": "chromium",
                    "errors": [
                        "locator.click: Timeout 30000ms exceeded"
                    ],
                }
            ],
        }

        # Route failed tests to investigation.
        self.assertEqual(
            self.orchestrator.advance_after_analysis(),
            WorkflowState.INVESTIGATING
        )

        # Generate investigation recommendations.
        plans = self.orchestrator.build_investigation_plans()
        self.assertEqual(len(plans), 1)

        # Finish investigation and proceed to reporting.
        self.assertEqual(
            self.orchestrator.advance_after_investigation(),
            WorkflowState.REPORTING
        )

        # Prepare the final result.
        result = self.orchestrator.complete_reporting()

        # Verify that the workflow completed successfully.
        self.assertEqual(
            result["workflow_status"],
            "COMPLETED"
        )

        # Verify that failed test information is preserved.
        self.assertEqual(
            result["test_summary"]["failed"],
            1
        )

        # Verify that the investigation plan is included.
        self.assertEqual(
            result["investigation_plans"][0]["classification"],
            "LOCATOR_TIMEOUT"
        )

        # Verify the final workflow state.
        self.assertEqual(
            self.orchestrator.get_state(),
            WorkflowState.COMPLETED
        )


    def test_new_execution_clears_previous_results(self):
        # Start the first workflow execution.
        self.assertTrue(self.orchestrator.try_start())

        # Move the workflow to ANALYZING.
        self.assertTrue(
            self.orchestrator.state_manager.transition_to(
                WorkflowState.ANALYZING
            )
        )

        # Simulate a previously analyzed regression report.
        self.orchestrator.report_summary = {
            "passed": 3,
            "failed": 0,
            "failures": [],
        }

        # Move the workflow to REPORTING.
        self.assertEqual(
            self.orchestrator.advance_after_analysis(),
            WorkflowState.REPORTING
        )

        # Complete the first workflow.
        self.orchestrator.complete_reporting()

        # Verify that the first workflow has saved results.
        self.assertIsNotNone(self.orchestrator.workflow_result)
        self.assertIsNotNone(self.orchestrator.report_summary)

        # Simulate investigation data retained from a previous run.
        self.orchestrator.investigation_plans = [
            {"test_name": "Previous test"}
        ]

        # Start a new execution after completion.
        second_result = self.orchestrator.try_start()

        # Verify that the new execution is accepted.
        self.assertTrue(second_result)

        # Verify that all previous execution data is cleared.
        self.assertIsNone(self.orchestrator.report_summary)
        self.assertIsNone(self.orchestrator.investigation_plans)
        self.assertIsNone(self.orchestrator.workflow_result)

        # Verify that the new workflow is EXECUTING.
        self.assertEqual(
            self.orchestrator.get_state(),
            WorkflowState.EXECUTING
        )


    def test_rejected_execution_preserves_current_results(self):
        # Start the first execution request.
        self.assertTrue(self.orchestrator.try_start())

        # Move to ANALYZING to represent an active workflow.
        self.assertTrue(
            self.orchestrator.state_manager.transition_to(
                WorkflowState.ANALYZING
            )
        )

        # Store the active workflow's report summary.
        current_summary = {
            "passed": 2,
            "failed": 0,
            "failures": [],
        }

        self.orchestrator.report_summary = current_summary

        # Attempt another execution while the workflow is active.
        second_result = self.orchestrator.try_start()

        # Verify that the duplicate request is rejected.
        self.assertFalse(second_result)

        # Verify that the current report summary is preserved.
        self.assertEqual(
            self.orchestrator.report_summary,
            current_summary
        )

        # Verify that the active workflow state remains unchanged.
        self.assertEqual(
            self.orchestrator.get_state(),
            WorkflowState.ANALYZING
        )



    def test_investigation_failure_preserves_partial_results(self):
        # Start the workflow and enter the analysis stage.
        self.assertTrue(self.orchestrator.try_start())

        self.assertTrue(
            self.orchestrator.state_manager.transition_to(
                WorkflowState.ANALYZING
            )
        )

        # Store a valid parsed report containing one failed test.
        self.orchestrator.report_summary = {
            "passed": 2,
            "failed": 1,
            "skipped": 0,
            "flaky": 0,
            "duration_ms": 1500,
            "failures": [
                {
                    "name": "Checkout test",
                    "project": "chromium",
                    "errors": [
                        "locator.click: Timeout 30000ms exceeded"
                    ],
                }
            ],
        }

        # Advance the workflow to the investigation stage.
        self.assertEqual(
            self.orchestrator.advance_after_analysis(),
            WorkflowState.INVESTIGATING
        )

        # Simulate an unexpected investigation strategy failure.
        with patch(
            "agent.workflow.select_investigation_strategy",
            side_effect=RuntimeError("Investigation service unavailable")
        ):
            # Capture the investigation exception for recovery.
            with self.assertRaises(RuntimeError) as caught:
                self.orchestrator.build_investigation_plans()

        # Generate a partial report using the captured error.
        result = self.orchestrator.complete_partial_reporting(
            caught.exception
        )

        # Verify that the workflow is marked partially completed.
        self.assertEqual(
            result["workflow_status"],
            "PARTIALLY_COMPLETED"
        )

        # Verify that the original failed test information is preserved.
        self.assertEqual(
            result["test_summary"]["failed"],
            1
        )

        # Verify that the investigation error is recorded.
        self.assertEqual(
            result["investigation_error"],
            "Investigation service unavailable"
        )

        # Verify that no investigation plans were fabricated.
        self.assertEqual(result["investigation_plans"], [])

        # Verify the final workflow state.
        self.assertEqual(
            self.orchestrator.get_state(),
            WorkflowState.PARTIALLY_COMPLETED
        )

        # Verify that the partial report was saved.
        self.assertEqual(
            self.orchestrator.workflow_result,
            result
        )


    def test_partial_reporting_rejects_invalid_state(self):
        # A new orchestrator begins in the IDLE state.
        self.assertEqual(
            self.orchestrator.get_state(),
            WorkflowState.IDLE
        )

        # Attempt partial completion before investigation begins.
        with self.assertRaises(RuntimeError):
            self.orchestrator.complete_partial_reporting(
                RuntimeError("Investigation failed")
            )

        # Verify that the rejected request preserves IDLE.
        self.assertEqual(
            self.orchestrator.get_state(),
            WorkflowState.IDLE
        )

        # Verify that no workflow result was generated.
        self.assertIsNone(self.orchestrator.workflow_result)


    def test_reporting_without_summary_sets_error_state(self):
        # Start a new workflow execution.
        self.assertTrue(self.orchestrator.try_start())

        # Move the workflow to the analysis stage.
        self.assertTrue(
            self.orchestrator.state_manager.transition_to(
                WorkflowState.ANALYZING
            )
        )

        # Enter REPORTING without a parsed report summary.
        self.assertTrue(
            self.orchestrator.state_manager.transition_to(
                WorkflowState.REPORTING
            )
        )

        # Verify that reporting fails without required test results.
        with self.assertRaises(RuntimeError):
            self.orchestrator.complete_reporting()

        # Verify that the workflow transitions to ERROR.
        self.assertEqual(
            self.orchestrator.get_state(),
            WorkflowState.ERROR
        )

        # Verify that no final report was saved.
        self.assertIsNone(self.orchestrator.workflow_result)


    def test_reporting_without_investigation_plans_sets_error_state(self):
        # Start the workflow and enter ANALYZING.
        self.assertTrue(self.orchestrator.try_start())

        self.assertTrue(
            self.orchestrator.state_manager.transition_to(
                WorkflowState.ANALYZING
            )
        )

        # Simulate a parsed report containing a failed test.
        self.orchestrator.report_summary = {
            "passed": 2,
            "failed": 1,
            "skipped": 0,
            "flaky": 0,
            "duration_ms": 1500,
            "failures": [
                {
                    "name": "Checkout test",
                    "project": "chromium",
                    "errors": ["Assertion failed"],
                }
            ],
        }

        # Simulate an incorrect workflow that reaches REPORTING
        # without completing the required investigation planning.
        self.assertTrue(
            self.orchestrator.state_manager.transition_to(
                WorkflowState.REPORTING
            )
        )

        # Verify that incomplete reporting is rejected.
        with self.assertRaises(RuntimeError):
            self.orchestrator.complete_reporting()

        # Verify that the workflow enters ERROR.
        self.assertEqual(
            self.orchestrator.get_state(),
            WorkflowState.ERROR
        )

        # Verify that the original test results remain available.
        self.assertEqual(
            self.orchestrator.report_summary["failed"],
            1
        )

        # Verify that no successful final report was generated.
        self.assertIsNone(self.orchestrator.workflow_result)
