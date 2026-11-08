from agent.workflow_state import WorkflowState
from agent.workflow_transitions import is_valid_transition


class WorkflowStateManager:
    def __init__(self):
        self._current_state = WorkflowState.IDLE

    def get_state(self) -> WorkflowState:
        return self._current_state

    def transition_to(self, next_state: WorkflowState) -> bool:
        if not is_valid_transition(self._current_state, next_state):
            return False

        self._current_state = next_state
        return True
    