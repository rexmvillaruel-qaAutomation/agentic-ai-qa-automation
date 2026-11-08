import unittest

from agent.workflow_state import WorkflowState
from agent.workflow_manager import WorkflowStateManager


class TestWorkflowStateManager(unittest.TestCase):
    def setUp(self):
        self.manager = WorkflowStateManager()

    def test_initial_state_is_idle(self):
        result = self.manager.get_state()
        self.assertEqual(result, WorkflowState.IDLE)

    def test_valid_transition_updates_state(self):
        result = self.manager.transition_to(WorkflowState.EXECUTING)

        self.assertTrue(result)
        self.assertEqual(
            self.manager.get_state(),
            WorkflowState.EXECUTING
        )

    def test_invalid_transition_preserves_state(self):
        result = self.manager.transition_to(WorkflowState.REPORTING)
        
        self.assertFalse(result)
        self.assertEqual(
            self.manager.get_state(),
            WorkflowState.IDLE
        )

        