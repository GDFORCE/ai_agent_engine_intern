from typing import Dict, Any, Optional
from .models import WorkflowState, GraphDefinition, RunResult
from .tools import TOOL_REGISTRY
import uuid
import logging
import copy # Used for creating deep copies of state
from datetime import datetime

logger = logging.getLogger("WorkflowEngine")
logger.setLevel(logging.INFO)

class WorkflowEngine:
    """The core engine to manage and run workflows."""
    
    graphs: Dict[str, GraphDefinition] = {}
    runs: Dict[str, RunResult] = {}  # Store completed runs for retrieval
    
    async def create_graph(self, definition: GraphDefinition) -> str:
        """Stores a new graph definition."""
        self.graphs[definition.id] = definition
        return definition.id

    def get_run(self, run_id: str) -> Optional[RunResult]:
        """Retrieve a completed run by ID."""
        return self.runs.get(run_id)

    def _find_next_node(self, graph: GraphDefinition, current_node_name: str, state: WorkflowState) -> Optional[str]:
        """Finds the next node name based on edges and conditions."""
        
        # Iterate over all edge groups defined in the graph
        for edge_group in graph.edges:
            for edge in edge_group:
                if edge.source == current_node_name:
                    
                    # 1. Check for branching condition
                    if edge.condition:
                        try:
                            # Execute the condition string against the state dictionary
                            state_dict = state.model_dump() 
                            # Use a restricted global scope for safety in eval
                            condition_result = eval(edge.condition, {"__builtins__": None}, {"state": state_dict})
                            
                            if condition_result is True:
                                logger.info(f"Transition: {current_node_name} -> {edge.target} via condition: {edge.condition}")
                                return edge.target
                        except Exception as e:
                            logger.error(f"Error evaluating condition '{edge.condition}': {e}")
                            # If an error occurs during evaluation, skip this edge and check the next one.
                            continue
                    else:
                        # 2. No condition means it's a default transition (always taken if reached)
                        logger.info(f"Transition: {current_node_name} -> {edge.target} (default).")
                        return edge.target
                
        return None # Workflow ends or dead end if not found

    async def run_graph(self, graph_id: str, initial_state: WorkflowState) -> RunResult:
        """Executes the workflow graph end-to-end."""
        graph = self.graphs.get(graph_id)
        if not graph:
            raise ValueError(f"Graph ID '{graph_id}' not found.")
            
        run_id = str(uuid.uuid4())
        # Use deep copy to ensure the original state object is not mutated outside the engine
        current_state = copy.deepcopy(initial_state)
        current_node_name = graph.initial_node
        execution_log = []
        
        MAX_STEPS = 20 # Safety break to prevent genuine infinite loops
        step_count = 0 
        
        while current_node_name != "STOP" and step_count < MAX_STEPS:
            step_count += 1
            node = next((n for n in graph.nodes if n.name == current_node_name), None)
            
            if not node:
                logger.warning(f"Workflow ended prematurely: Node '{current_node_name}' not found.")
                break

            tool_func = TOOL_REGISTRY.get(node.tool_name)
            if not tool_func:
                logger.error(f"Workflow ended prematurely: Tool '{node.tool_name}' not registered.")
                break

            # --- 1. Execute Tool ---
            state_updates: Dict[str, Any] = await tool_func(current_state)
            
            # --- 2. Update State ---
            current_state = current_state.model_copy(update=state_updates)
            
            # --- 3. Find Next Node ---
            next_node_name = self._find_next_node(graph, current_node_name, current_state)
            
            # Record step in log
            execution_log.append({
                "step": step_count,
                "node": node.name,
                "tool_used": node.tool_name,
                "updates": state_updates,
                "next_node": next_node_name 
            })
            
            current_node_name = next_node_name
            
        if step_count >= MAX_STEPS:
             logger.warning("Workflow stopped due to max step limit (potential infinite loop detected).")

        result = RunResult(run_id=run_id, final_state=current_state, execution_log=execution_log)
        self.runs[run_id] = result  # Store the run for later retrieval
        return result