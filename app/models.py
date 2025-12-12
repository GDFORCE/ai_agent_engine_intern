from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import uuid

# --- 1. The Shared State (For Code Review Agent) ---
class WorkflowState(BaseModel):
    """The shared state that flows between nodes for the Code Review Agent."""
    code_snippet: str = Field(..., description="The code to be analyzed.")
    functions_extracted: List[str] = Field(default_factory=list)
    complexity_score: int = 0
    issues_found: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    quality_score: int = 0 # Target for looping: Stop when this reaches 100
    loop_count: int = 0

# --- 2. Graph Definition Models ---
class Node(BaseModel):
    name: str # e.g., "extract_functions_node"
    tool_name: str # Name of the function to call from TOOL_REGISTRY

class Edge(BaseModel):
    source: str
    target: str
    # Condition is a simple string expression that must evaluate to True/False against the state
    condition: Optional[str] = None 

class GraphDefinition(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nodes: List[Node]
    # Edges are grouped: a list of groups, where each group is a list of edges
    # This structure is designed to hold conditional branches clearly.
    edges: List[List[Edge]] 
    initial_node: str

# --- 3. Run Result Model ---
class RunResult(BaseModel):
    run_id: str
    final_state: WorkflowState
    execution_log: List[Dict[str, Any]]