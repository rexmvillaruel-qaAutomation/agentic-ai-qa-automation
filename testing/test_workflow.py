import unittest

from agent.workflow_state import WorkflowState
from agent.workflow import can_start_execution


class TestWorkflow(unittest.TestCase):
    def test_idle_allows_execution(self):
        result = can_start_execution(WorkflowState.IDLE)

        self.assertTrue(result)

    def test_executing_rejects_execution(self):
        result = can_start_execution(WorkflowState.EXECUTING)

        self.assertFalse(result)

    def test_remaining_workflow_states(self):
        test_cases = [
            (WorkflowState.ANALYZING, False),
            (WorkflowState.INVESTIGATING, False),
            (WorkflowState.REPORTING, False),
            (WorkflowState.COMPLETED, True),
            (WorkflowState.PARTIALLY_COMPLETED, True),
            (WorkflowState.ERROR, True),
        ]

        for state, expected_result in test_cases:
            with self.subTest(state=state):
                result = can_start_execution(state)
                self.assertEqual(result, expected_result)
