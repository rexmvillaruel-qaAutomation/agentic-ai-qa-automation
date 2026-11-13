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