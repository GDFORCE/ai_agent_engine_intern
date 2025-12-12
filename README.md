# AI Agent Engineering Intern Case Study - Workflow Engine

A minimal workflow/graph engine built with FastAPI, designed as a simplified version of LangGraph. This project demonstrates how to build a system with nodes, edges, shared state, branching, and looping logic.

## Project Structure

```
ai_agent_engine_intern/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application and endpoints
│   ├── models.py         # Pydantic models (WorkflowState, GraphDefinition, etc.)
│   ├── engine.py         # Core workflow engine logic
│   ├── tools.py          # Tool registry and tool implementations
│   └── test_workflow.py  # Test script for the workflow
├── requirements.txt      # Python dependencies
├── .gitignore           # Git ignore file
└── README.md            # This file
```

## Features

### 1. Workflow Engine
- **Nodes**: Python async functions that read and modify shared state
- **State**: Pydantic model (`WorkflowState`) that flows through the pipeline
- **Edges**: Define transitions between nodes with optional conditional routing
- **Branching**: Route to different nodes based on state conditions
- **Looping**: Support for repeating nodes until a condition is met
- **Execution Logging**: Track each step's inputs, outputs, and timing

### 2. Tool Registry
A dictionary-based registry mapping tool names to async functions:
- `extract_functions` - Extract function definitions from code
- `check_complexity` - Calculate cyclomatic complexity proxy
- `detect_basic_issues` - Identify code style and maintainability issues
- `suggest_improvements` - Generate refactoring suggestions

### 3. Sample Workflow: Code Review Agent
Analyzes Python code through a pipeline:
1. **Extract**: Find all function definitions in the code
2. **Complexity**: Calculate control flow complexity score
3. **Detect Issues**: Identify style, length, and naming problems
4. **Suggest**: Generate improvement recommendations
5. **Loop**: Re-run detection if quality score < 100, otherwise stop

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. **Create and activate virtual environment** (optional but recommended):
```bash
python -m venv venv

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On macOS/Linux:
source venv/bin/activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## Running the Application

### Start the FastAPI Server

```bash
cd ai_agent_engine_intern
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will be available at `http://localhost:8000`

**API Documentation**: Open `http://localhost:8000/docs` in your browser for Swagger UI

### Run Tests

```bash
python -m app.test_workflow
```

This runs a complete test of the Code Review Agent with sample code.

## API Endpoints

### 1. Get Sample Graph ID
```http
GET /graph/sample-id
```
Returns the pre-loaded Code Review Agent ID for easy testing.

**Response**:
```json
{
  "graph_id": "code-review-agent-v1",
  "message": "Use this ID in the /graph/run endpoint."
}
```

### 2. Create a New Workflow Graph
```http
POST /graph/create
```
Define and create a new workflow graph dynamically.

**Request Body**:
```json
{
  "id": "my-workflow",
  "nodes": [
    {"name": "node1", "tool_name": "extract_functions"},
    {"name": "node2", "tool_name": "check_complexity"}
  ],
  "edges": [
    [
      {"source": "node1", "target": "node2", "condition": null}
    ]
  ],
  "initial_node": "node1"
}
```

**Response**:
```json
{
  "graph_id": "my-workflow",
  "message": "Graph created successfully."
}
```

### 3. Run a Workflow
```http
POST /graph/run/{graph_id}
```
Execute a workflow graph with initial state.

**URL Parameters**:
- `graph_id`: The ID of the graph to run (e.g., `code-review-agent-v1`)

**Request Body**:
```json
{
  "code_snippet": "def add(a, b):\n    if a > 0:\n        for i in range(a):\n            b += i\n    return b"
}
```

**Response**:
```json
{
  "run_id": "run-12345678-abcd",
  "final_state": {
    "code_snippet": "def add(a, b):\n    if a > 0:\n        for i in range(a):\n            b += i\n    return b",
    "functions_extracted": ["add"],
    "complexity_score": 30,
    "issues_found": [
      "Found 1 possible single-letter variables. Use descriptive names."
    ],
    "suggestions": [
      "Consider refactoring the detected issue: Found 1 possible single-letter variables. Use descriptive names."
    ],
    "quality_score": 80,
    "loop_count": 1
  },
  "execution_log": [
    {
      "node": "extract",
      "status": "completed",
      "input": {...},
      "output": {...},
      "timestamp": "2025-12-12T10:30:45.123456"
    },
    ...
  ]
}
```

### 4. Get Workflow State (Optional)
```http
GET /graph/state/{run_id}
```
Retrieve the state of a completed workflow run.

**Response**:
```json
{
  "run_id": "run-12345678-abcd",
  "final_state": {...},
  "execution_log": [...]
}
```

## How the Engine Works

### State Flow

```
Initial State
    ↓
[Extract Node] → Extract functions from code
    ↓
[Complexity Node] → Calculate complexity score
    ↓
[Detect Node] → Find issues
    ↓
    Branch: if issues > 0 → [Suggest Node] else → STOP
    ↓
[Suggest Node] → Generate suggestions
    ↓
    Loop: if quality_score < 100 → back to [Detect] else → STOP
```

### Key Components

**engine.py**:
- `WorkflowEngine`: Core engine managing graph execution
- Graph storage in memory
- Conditional routing via Python `eval()` on state
- Run tracking with execution logs

**tools.py**:
- Tool implementations as async functions
- `TOOL_REGISTRY`: Dictionary mapping tool names to functions
- Each tool takes state and returns updates as dict

**models.py**:
- `WorkflowState`: Shared state model with Pydantic validation
- `Node`: Represents a workflow node
- `Edge`: Represents transitions with optional conditions
- `GraphDefinition`: Complete workflow definition
- `RunResult`: Execution result with logs

**main.py**:
- FastAPI application setup
- Three endpoints for graph management and execution
- Pre-loads sample Code Review Agent on startup

## Example Usage (Python)

```python
import asyncio
import httpx

async def test_workflow():
    async with httpx.AsyncClient() as client:
        # 1. Get sample graph ID
        resp = await client.get("http://localhost:8000/graph/sample-id")
        graph_id = resp.json()["graph_id"]
        
        # 2. Run workflow
        code = """
def process(data):
    if len(data) > 0:
        for item in data:
            print(item)
    return data
"""
        
        resp = await client.post(
            f"http://localhost:8000/graph/run/{graph_id}",
            json={"code_snippet": code}
        )
        
        result = resp.json()
        print(f"Final Quality Score: {result['final_state']['quality_score']}")
        print(f"Issues Found: {result['final_state']['issues_found']}")
        print(f"Suggestions: {result['final_state']['suggestions']}")

asyncio.run(test_workflow())
```

## What Works Now

✅ Core workflow engine with branching and looping  
✅ Tool registry system  
✅ Code Review Agent (Option A) fully implemented  
✅ Three main API endpoints  
✅ Pydantic validation for type safety  
✅ Execution logging with timestamps  
✅ Async/await throughout  
✅ Clean code structure and separation of concerns  

## Future Improvements (With More Time)

1. **Persistence**: Store graphs and runs in SQLite/PostgreSQL instead of memory
2. **WebSocket Support**: Stream execution logs in real-time to clients
3. **Background Tasks**: Use Celery or APScheduler for async job management
4. **Enhanced Monitoring**: Add Prometheus metrics for execution times and success rates
5. **Graph Visualization**: API endpoint to export graph as JSON for visualization
6. **Advanced Routing**: Support loop limits, error handlers, and fallback nodes
7. **Tool Timeout**: Add timeout handling for long-running tools
8. **Dynamic Tool Registration**: Allow runtime tool registration via API
9. **State Persistence**: Save intermediate states to enable resumable workflows
10. **Testing**: Add comprehensive unit and integration tests

## Dependencies

See `requirements.txt`:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `httpx` - Async HTTP client (for testing)

## Notes

- The engine uses Python's `eval()` for conditional routing. For production, consider a safer expression evaluator.
- All state is stored in memory. Restart the server to clear all graphs and runs.
- Tools are async functions but currently run sequentially. For true parallelism, modify the engine.

## License

This is an educational project for the Tredence AI Engineering Internship.
