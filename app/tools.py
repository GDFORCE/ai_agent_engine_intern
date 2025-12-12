# --- app/tools.py ---

import re
from typing import Dict, Any, Callable
from .models import WorkflowState
import random


async def extract_functions(state: WorkflowState) -> Dict[str, Any]:
    """Extracts function definitions from the code snippet."""
    # Simple regex to find function definitions (Python style)
    func_pattern = r'def\s+([a-zA-Z_]\w*)\s*\('
    functions = re.findall(func_pattern, state.code_snippet)
    
    print(f"Tool: extract_functions found {len(functions)} functions.")
    return {"functions_extracted": functions}


async def check_complexity(state: WorkflowState) -> Dict[str, Any]:
    """Calculates a proxy for Cyclomatic Complexity by counting control flow statements."""
    control_flow_count = 0
    # Search for common control flow keywords
    keywords = ['if ', 'while ', 'for ', 'try:', 'except ', 'with ']
    for keyword in keywords:
        control_flow_count += state.code_snippet.count(keyword)
    
    # Base complexity on the number of control flow statements
    score = control_flow_count * 10 
    print(f"Tool: check_complexity calculated proxy complexity score: {score}.")
    return {"complexity_score": score}

async def detect_basic_issues(state: WorkflowState) -> Dict[str, Any]:
    """Detects basic code style and maintainability issues (linters-style)."""
    issues = []
    
    # Rule 1: Long Lines (Maintainability)
    for i, line in enumerate(state.code_snippet.split('\n')):
        if len(line) > 80:
            issues.append(f"Line {i+1} exceeds 80 characters.")

    # Rule 2: High Complexity Flag
    if state.complexity_score > 50:
        issues.append("High complexity score. Consider reducing control flow depth.")
    
    # Rule 3: Single-letter variables outside of loops (Readability)
    # Simple regex to catch standalone single letters not followed by another letter/number
    single_var_matches = re.findall(r'\b[a-zA-Z]\b', state.code_snippet)
    if len(single_var_matches) > 3:
        issues.append(f"Found {len(single_var_matches)} possible single-letter variables. Use descriptive names.")

    print(f"Tool: detect_basic_issues found {len(issues)} issues.")
    return {"issues_found": issues}

async def suggest_improvements(state: WorkflowState) -> Dict[str, Any]:
    """Generates specific suggestions and updates the quality score."""
    suggestions = []
    
    for issue in state.issues_found:
        if "exceeds 80 characters" in issue:
            suggestions.append("Break the long line into multiple lines or use parenthesis.")
        elif "High complexity score" in issue:
            suggestions.append("Refactor the large block of code into smaller, single-responsibility functions.")
        else:
            suggestions.append(f"Consider refactoring the detected issue: {issue}.")
            
    # CRUCIAL LOOP CONTROL: Update the quality score faster if fewer issues are left.
    improvement_factor = max(1, 10 - len(state.issues_found)) 
    new_score = state.quality_score + improvement_factor * 10
    
    print(f"Tool: suggest_improvements generated {len(suggestions)} suggestions and updated score.")
    return {
        "suggestions": suggestions,
        "quality_score": min(new_score, 100)  # Cap at 100
    }


# Tool Registry: Maps tool names to their async handler functions
TOOL_REGISTRY: Dict[str, Callable] = {
    "extract_functions": extract_functions,
    "check_complexity": check_complexity,
    "detect_basic_issues": detect_basic_issues,
    "suggest_improvements": suggest_improvements,
}