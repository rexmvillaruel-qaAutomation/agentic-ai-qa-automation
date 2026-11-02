from agent.workflow_state import WorkflowState


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