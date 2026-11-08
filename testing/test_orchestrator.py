import unittest

from agent.workflow import WorkflowOrchestrator
from agent.workflow_state import WorkflowState
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier


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