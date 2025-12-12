from fastapi import FastAPI, HTTPException
from typing import Dict
from .models import GraphDefinition, WorkflowState, RunResult, Node, Edge
from .engine import WorkflowEngine
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AI Agent Engineering Intern Case Study")
engine = WorkflowEngine()

# --- 1. Define the Sample Workflow (Option A: Code Review Agent) ---
SAMPLE_GRAPH_ID = "code-review-agent-v1"

nodes = [
    {"name": "extract", "tool_name": "extract_functions"},
    {"name": "complexity", "tool_name": "check_complexity"},
    {"name": "detect", "tool_name": "detect_basic_issues"},
    {"name": "suggest", "tool_name": "suggest_improvements"}
]

# Edges for Branching and Looping (Defined in groups for clarity)
edges = [
    # Group 1: Linear Transitions
    [
        {"source": "extract", "target": "complexity"},
        {"source": "complexity", "target": "detect"},
    ],
    # Group 2: Branching based on issue detection
    [
        # BRANCH 1: If issues are found, go to 'suggest' (Loop Start)
        {"source": "detect", "target": "suggest", "condition": "len(state['issues_found']) > 0"},
        # BRANCH 2: If no issues are found, STOP
        {"source": "detect", "target": "STOP", "condition": "len(state['issues_found']) == 0"},
    ],
    # Group 3: Looping based on quality score
    [
        # LOOP BACK: If quality score is insufficient, loop back to 'detect'
        {"source": "suggest", "target": "detect", "condition": "state['quality_score'] < 100"},
        # EXIT LOOP: If quality score is sufficient, STOP
        {"source": "suggest", "target": "STOP", "condition": "state['quality_score'] >= 100"},
    ]
]

sample_graph_def = GraphDefinition(
    id=SAMPLE_GRAPH_ID,
    nodes=[Node(**n) for n in nodes],
    edges=[[Edge(**e) for e in group] for group in edges],
    initial_node="extract"
)
# Pre-load the sample graph on startup
engine.create_graph(sample_graph_def)


# --- 2. API Endpoints ---
@app.post("/graph/create", response_model=Dict[str, str], summary="Create a new workflow graph")
async def create_workflow_graph(definition: GraphDefinition):
    """Allows dynamic creation of new workflow definitions."""
    graph_id = await engine.create_graph(definition)
    return {"graph_id": graph_id, "message": "Graph created successfully."}

@app.post("/graph/run/{graph_id}", response_model=RunResult, summary="Execute a workflow graph")
async def run_workflow(graph_id: str, initial_state: WorkflowState):
    """Executes the workflow end-to-end, returning the final state and execution log."""
    try:
        # Note: For simplicity and assignment requirements, this runs synchronously.
        # See README for suggested asynchronous improvement.
        result = await engine.run_graph(graph_id, initial_state)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Engine Error: {e}")

@app.get("/graph/sample-id", summary="Get the ID for the pre-loaded Code Review Agent")
def get_sample_id():
    """Returns the ID of the pre-loaded sample workflow for easy testing."""
    return {"graph_id": SAMPLE_GRAPH_ID, "message": "Use this ID in the /graph/run endpoint."}

@app.get("/graph/state/{run_id}", response_model=RunResult, summary="Get the state of a completed workflow run")
def get_run_state(run_id: str):
    """Retrieves the final state and execution log of a completed workflow."""
    result = engine.get_run(run_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found.")
    return result