from agent.workflow_state import WorkflowState

ALLOWED_TRANSITIONS = {
    
    WorkflowState.IDLE: {
        WorkflowState.EXECUTING,
    },
    WorkflowState.EXECUTING: {
        WorkflowState.ANALYZING,
        WorkflowState.ERROR,
    },
    WorkflowState.ANALYZING: {
        WorkflowState.INVESTIGATING,
        WorkflowState.REPORTING,
        WorkflowState.ERROR,
    },
    WorkflowState.INVESTIGATING: {
        WorkflowState.REPORTING,
        WorkflowState.ERROR,
    },
    WorkflowState.REPORTING: {
        WorkflowState.COMPLETED,
        WorkflowState.PARTIALLY_COMPLETED,
        WorkflowState.ERROR,
    },
    WorkflowState.COMPLETED: {
        WorkflowState.EXECUTING,
    },
    WorkflowState.PARTIALLY_COMPLETED: {
        WorkflowState.EXECUTING,
    },
    WorkflowState.ERROR: {
        WorkflowState.EXECUTING,
    },
}

def is_valid_transition(
    current_state: WorkflowState,
    next_state: WorkflowState
) -> bool:

    allowed_states = ALLOWED_TRANSITIONS.get(current_state, set())
    return next_state in allowed_states

if __name__ == "__main__":
    result = is_valid_transition(
        WorkflowState.EXECUTING,
        WorkflowState.REPORTING
    )

    print(result)