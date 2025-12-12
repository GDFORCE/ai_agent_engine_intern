#!/usr/bin/env python
"""
Test script for the AI Agent Workflow Engine.
Tests all endpoints and verifies the Code Review Agent works correctly.
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"


async def test_workflow():
    """Test the complete workflow from start to finish."""
    async with httpx.AsyncClient() as client:
        print("\n" + "="*70)
        print("AI AGENT WORKFLOW ENGINE - TEST SUITE")
        print("="*70)
        
        # Test 1: Get sample graph ID
        print("\n[TEST 1] Get Sample Graph ID")
        print("-" * 70)
        try:
            resp = await client.get(f"{BASE_URL}/graph/sample-id")
            resp.raise_for_status()
            sample_data = resp.json()
            graph_id = sample_data["graph_id"]
            print(f"✓ Sample graph ID retrieved: {graph_id}")
            print(f"  Message: {sample_data['message']}")
        except Exception as e:
            print(f"✗ Failed to get sample ID: {e}")
            return
        
        # Test 2: Run the workflow with sample code
        print("\n[TEST 2] Execute Code Review Workflow")
        print("-" * 70)
        
        sample_code = '''
def calculate_total(items):
    """Calculate the total of all items."""
    total = 0
    for item in items:
        if item > 0:
            total = total + item
        else:
            print("Warning: negative item")
    return total

def process_data(data):
    x = len(data)
    for i in range(x):
        data[i] = data[i] * 2
    return data
'''
        
        try:
            resp = await client.post(
                f"{BASE_URL}/graph/run/{graph_id}",
                json={"code_snippet": sample_code},
                timeout=30.0
            )
            resp.raise_for_status()
            result = resp.json()
            run_id = result["run_id"]
            
            print(f"✓ Workflow executed successfully")
            print(f"  Run ID: {run_id}")
            print(f"\n  Final State:")
            print(f"    Functions Extracted: {result['final_state']['functions_extracted']}")
            print(f"    Complexity Score: {result['final_state']['complexity_score']}")
            print(f"    Quality Score: {result['final_state']['quality_score']}")
            print(f"    Loop Count: {result['final_state']['loop_count']}")
            
            if result['final_state']['issues_found']:
                print(f"\n  Issues Found:")
                for issue in result['final_state']['issues_found']:
                    print(f"    - {issue}")
            
            if result['final_state']['suggestions']:
                print(f"\n  Suggestions:")
                for suggestion in result['final_state']['suggestions']:
                    print(f"    - {suggestion}")
            
            print(f"\n  Execution Log ({len(result['execution_log'])} steps):")
            for log_entry in result['execution_log']:
                print(f"    Step {log_entry['step']}: {log_entry['node']} ({log_entry['tool_used']}) → {log_entry['next_node']}")
        
        except Exception as e:
            print(f"✗ Failed to execute workflow: {e}")
            return
        
        # Test 3: Retrieve run state
        print("\n[TEST 3] Retrieve Workflow State by Run ID")
        print("-" * 70)
        try:
            resp = await client.get(f"{BASE_URL}/graph/state/{run_id}")
            resp.raise_for_status()
            retrieved = resp.json()
            print(f"✓ Run state retrieved successfully")
            print(f"  Run ID: {retrieved['run_id']}")
            print(f"  Final Quality Score: {retrieved['final_state']['quality_score']}")
            print(f"  Execution Steps: {len(retrieved['execution_log'])}")
        except Exception as e:
            print(f"✗ Failed to retrieve run state: {e}")
            return
        
        # Test 4: Create a custom graph
        print("\n[TEST 4] Create Custom Workflow Graph")
        print("-" * 70)
        custom_graph = {
            "id": f"test-graph-{int(asyncio.get_event_loop().time())}",
            "initial_node": "extract",
            "nodes": [
                {"name": "extract", "tool_name": "extract_functions"},
                {"name": "complexity", "tool_name": "check_complexity"},
                {"name": "detect", "tool_name": "detect_basic_issues"},
                {"name": "suggest", "tool_name": "suggest_improvements"}
            ],
            "edges": [
                [
                    {"source": "extract", "target": "complexity", "condition": None},
                    {"source": "complexity", "target": "detect", "condition": None}
                ],
                [
                    {"source": "detect", "target": "suggest", "condition": "len(state['issues_found']) > 0"},
                    {"source": "detect", "target": "STOP", "condition": "len(state['issues_found']) == 0"}
                ],
                [
                    {"source": "suggest", "target": "STOP", "condition": None}
                ]
            ]
        }
        
        try:
            resp = await client.post(
                f"{BASE_URL}/graph/create",
                json=custom_graph
            )
            resp.raise_for_status()
            created = resp.json()
            custom_graph_id = created["graph_id"]
            print(f"✓ Custom graph created successfully")
            print(f"  Graph ID: {custom_graph_id}")
            print(f"  Message: {created['message']}")
        except Exception as e:
            print(f"✗ Failed to create custom graph: {e}")
            return
        
        # Test 5: Run custom graph
        print("\n[TEST 5] Execute Custom Workflow")
        print("-" * 70)
        simple_code = "def hello():\n    x = 5\n    if x > 0:\n        print(x)\n"
        
        try:
            resp = await client.post(
                f"{BASE_URL}/graph/run/{custom_graph_id}",
                json={"code_snippet": simple_code},
                timeout=30.0
            )
            resp.raise_for_status()
            custom_result = resp.json()
            print(f"✓ Custom workflow executed successfully")
            print(f"  Run ID: {custom_result['run_id']}")
            print(f"  Final Quality Score: {custom_result['final_state']['quality_score']}")
            print(f"  Execution Steps: {len(custom_result['execution_log'])}")
        except Exception as e:
            print(f"✗ Failed to execute custom workflow: {e}")
            return
        
        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print("✓ All tests passed!")
        print("\nKey Results:")
        print(f"  - Sample workflow executed with quality score: {result['final_state']['quality_score']}")
        print(f"  - Custom graph created and executed successfully")
        print(f"  - Run state retrieval working correctly")
        print(f"  - Total steps across workflows: {len(result['execution_log']) + len(custom_result['execution_log'])}")
        print("="*70 + "\n")


if __name__ == "__main__":
    print("\n⚠️  Make sure the FastAPI server is running!")
    print("   Run: uvicorn app.main:app --reload")
    print("   In another terminal, run this script.\n")
    
    try:
        asyncio.run(test_workflow())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
