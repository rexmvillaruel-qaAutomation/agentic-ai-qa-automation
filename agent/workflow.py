from agent.workflow_state import WorkflowState
from agent.workflow_manager import WorkflowStateManager
from threading import Lock


ACTIVE_STATES = {
    WorkflowState.EXECUTING,
    WorkflowState.ANALYZING,
    WorkflowState.INVESTIGATING,
    WorkflowState.REPORTING,
}


TERMINAL_STATES = {
    WorkflowState.COMPLETED,
    WorkflowState.PARTIALLY_COMPLETED,
    WorkflowState.ERROR,
}

def can_start_execution(current_state: WorkflowState) -> bool:
   
    if current_state == WorkflowState.IDLE:
        return True
    
    if current_state in TERMINAL_STATES:
        return True
    
    return False

class WorkflowOrchestrator:
    def __init__(self):
        self.state_manager = WorkflowStateManager()
        self._admission_lock = Lock()

    def get_state(self) -> WorkflowState:
        return self.state_manager.get_state()

    def try_start(self) -> bool:
        with self._admission_lock:
            current_state = self.get_state()
            if not can_start_execution(current_state):
                return False

            return self.state_manager.transition_to(
            WorkflowState.EXECUTING
        )
    