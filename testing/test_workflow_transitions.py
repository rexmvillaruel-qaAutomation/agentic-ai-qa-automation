import unittest

from agent.workflow_state import WorkflowState
from agent.workflow_transitions import (
    ALLOWED_TRANSITIONS,
    is_valid_transition
)

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


    def test_valid_transitions(self):
        test_cases = [
            (WorkflowState.IDLE, WorkflowState.EXECUTING),
            (WorkflowState.EXECUTING, WorkflowState.ANALYZING),
            (WorkflowState.ANALYZING, WorkflowState.INVESTIGATING),
            (WorkflowState.EXECUTING, WorkflowState.ERROR),
            (WorkflowState.ANALYZING, WorkflowState.REPORTING),
            (WorkflowState.ANALYZING, WorkflowState.ERROR),
            (WorkflowState.INVESTIGATING, WorkflowState.REPORTING),
            (WorkflowState.INVESTIGATING, WorkflowState.ERROR),
            (WorkflowState.REPORTING, WorkflowState.COMPLETED),
            (WorkflowState.REPORTING, WorkflowState.PARTIALLY_COMPLETED),
            (WorkflowState.REPORTING, WorkflowState.ERROR),
            (WorkflowState.COMPLETED, WorkflowState.EXECUTING),
            (WorkflowState.PARTIALLY_COMPLETED, WorkflowState.EXECUTING),
            (WorkflowState.ERROR, WorkflowState.EXECUTING),
        ]

        for current_state, next_state in test_cases:
            with self.subTest(
                current=current_state,
                next=next_state
            ):
                result = is_valid_transition(
                    current_state,
                    next_state
                )
                self.assertTrue(result)

    def test_invalid_transitions(self):
        for current_state in WorkflowState:
            for next_state in WorkflowState:
                allowed_states = ALLOWED_TRANSITIONS.get(
                current_state,
                set()
            )

            if next_state not in allowed_states:
                with self.subTest(
                    current=current_state,
                    next=next_state
                ):
                    result = is_valid_transition(
                    current_state,
                    next_state
                )
                self.assertFalse(result)

