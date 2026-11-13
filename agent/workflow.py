from agent.workflow_state import WorkflowState
from agent.workflow_manager import WorkflowStateManager
from threading import Lock
from agent.controller import run_regression_tests, JSON_REPORT


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

    def execute_regression(self) -> int | None:
        if not self.try_start():
            return None

        try:
   
            exit_code = run_regression_tests()
            
            if not JSON_REPORT.is_file():
                raise FileNotFoundError(
                    f"Playwright JSON report missing: {JSON_REPORT}"
                )

            if not self.state_manager.transition_to(
                WorkflowState.ANALYZING
            ):
                raise RuntimeError("Cannot transition to ANALYZING")

            return exit_code

        except Exception:
            self.state_manager.transition_to(WorkflowState.ERROR)
            raise
    