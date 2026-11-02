import unittest

from agent.workflow_state import WorkflowState
from agent.workflow_transitions import is_valid_transition


class TestWorkflowTransitions(unittest.TestCase):

    def test_idle_to_executing_is_valid(self):
        result = is_valid_transition(
            WorkflowState.IDLE,
            WorkflowState.EXECUTING
        )

        self.assertTrue(result)

    def test_idle_to_reporting_is_invalid(self):
        result = is_valid_transition(
            WorkflowState.IDLE,
            WorkflowState.REPORTING
        )
        
        self.assertFalse(result)