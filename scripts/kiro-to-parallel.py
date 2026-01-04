#!/usr/bin/env python3
"""
Convert Kiro Spec tasks.md to codeagent-wrapper --parallel format.

Usage:
    python kiro-to-parallel.py .kiro/specs/user-auth/tasks.md > parallel-config.txt
    cat parallel-config.txt | codeagent-wrapper --parallel
    
    # Or directly:
    python kiro-to-parallel.py .kiro/specs/user-auth/tasks.md | codeagent-wrapper --parallel
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Optional

# Task type detection patterns
UI_PATTERNS = ['.css', '.scss', '.tsx', '.jsx', '.vue', 'tailwind', 'style', 'component', 'ui', 'frontend']
QUICKFIX_PATTERNS = ['config', 'fix', 'typo', 'rename', 'small', 'minor', 'update version']

def detect_task_type(task: Dict) -> str:
    """Detect task type based on files and description."""
    text = f"{task.get('description', '')} {' '.join(task.get('files', []))}".lower()
    
    for pattern in UI_PATTERNS:
        if pattern in text:
            return 'ui'
    
    for pattern in QUICKFIX_PATTERNS:
        if pattern in text:
            return 'quick-fix'
    
    return 'default'

def get_backend(task_type: str, allowed_backends: List[str]) -> str:
    """Route backend based on task type."""
    preferred = {
        'default': 'codex',
        'ui': 'gemini',
        'quick-fix': 'claude'
    }
    
    backend = preferred.get(task_type, 'codex')
    
    if backend in allowed_backends:
        return backend
    
    # Fallback priority: codex -> claude -> gemini
    for fallback in ['codex', 'claude', 'gemini']:
        if fallback in allowed_backends:
            return fallback
    
    return 'codex'

def parse_kiro_tasks(content: str) -> List[Dict]:
    """Parse Kiro tasks.md format."""
    tasks = []
    current_task = None
    
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Task header: "### Task 1: Description" or "## Task 1: Description"
        task_match = re.match(r'^#{2,3}\s*Task\s*(\d+):\s*(.+)$', line, re.IGNORECASE)
        if task_match:
            if current_task:
                tasks.append(current_task)
            current_task = {
                'id': f"task-{task_match.group(1)}",
                'description': task_match.group(2).strip(),
                'files': [],
                'dependencies': [],
                'test_command': ''
            }
            continue
        
        if not current_task:
            continue
        
        # Files: "- Files: src/auth.ts, src/utils.ts"
        files_match = re.match(r'^-?\s*Files?:\s*(.+)$', line, re.IGNORECASE)
        if files_match:
            files = [f.strip() for f in files_match.group(1).split(',')]
            current_task['files'] = files
            continue
        
        # Dependencies: "- Dependencies: Task 1, Task 2" or "- Dependencies: task-1"
        deps_match = re.match(r'^-?\s*Dependenc(?:y|ies):\s*(.+)$', line, re.IGNORECASE)
        if deps_match:
            deps_str = deps_match.group(1).strip().lower()
            if deps_str in ['none', 'n/a', '-', '']:
                continue
            # Parse "Task 1, Task 2" or "task-1, task-2"
            deps = []
            for dep in deps_str.split(','):
                dep = dep.strip()
                if dep.startswith('task '):
                    deps.append(f"task-{dep.replace('task ', '')}")
                elif dep.startswith('task-'):
                    deps.append(dep)
                elif dep.isdigit():
                    deps.append(f"task-{dep}")
            current_task['dependencies'] = deps
            continue
        
        # Test command: "- Test: npm test -- --coverage"
        test_match = re.match(r'^-?\s*Test(?:\s*Command)?:\s*(.+)$', line, re.IGNORECASE)
        if test_match:
            current_task['test_command'] = test_match.group(1).strip()
            continue
        
        # Scope: "- Scope: src/auth/**"
        scope_match = re.match(r'^-?\s*Scope:\s*(.+)$', line, re.IGNORECASE)
        if scope_match:
            if not current_task['files']:
                current_task['files'] = [scope_match.group(1).strip()]
            continue
    
    if current_task:
        tasks.append(current_task)
    
    return tasks

def generate_parallel_config(tasks: List[Dict], spec_dir: str, allowed_backends: List[str] = None) -> str:
    """Generate codeagent-wrapper --parallel config."""
    if allowed_backends is None:
        allowed_backends = ['codex', 'claude', 'gemini']
    
    output = []
    
    for task in tasks:
        task_type = detect_task_type(task)
        backend = get_backend(task_type, allowed_backends)
        
        deps = ', '.join(task['dependencies']) if task['dependencies'] else ''
        files = ', '.join(task['files']) if task['files'] else 'TBD'
        test_cmd = task['test_command'] or 'npm test -- --coverage'
        
        output.append('---TASK---')
        output.append(f"id: {task['id']}")
        output.append(f"backend: {backend}")
        output.append('workdir: .')
        if deps:
            output.append(f"dependencies: {deps}")
        output.append('---CONTENT---')
        output.append(f"Task: {task['description']}")
        output.append(f"Reference: @{spec_dir}/design.md")
        output.append(f"Scope: {files}")
        output.append(f"Test: {test_cmd}")
        output.append('Deliverables: code + unit tests + coverage ≥90% + coverage summary')
        output.append('')
    
    return '\n'.join(output)

def main():
    if len(sys.argv) < 2:
        print("Usage: python kiro-to-parallel.py <tasks.md> [--backends codex,gemini]", file=sys.stderr)
        sys.exit(1)
    
    tasks_file = Path(sys.argv[1])
    
    if not tasks_file.exists():
        print(f"Error: {tasks_file} not found", file=sys.stderr)
        sys.exit(1)
    
    # Parse backends from args
    allowed_backends = ['codex', 'claude', 'gemini']
    for i, arg in enumerate(sys.argv):
        if arg == '--backends' and i + 1 < len(sys.argv):
            allowed_backends = [b.strip() for b in sys.argv[i + 1].split(',')]
    
    # Determine spec directory
    spec_dir = str(tasks_file.parent)
    
    # Parse and convert
    content = tasks_file.read_text(encoding='utf-8')
    tasks = parse_kiro_tasks(content)
    
    if not tasks:
        print("Error: No tasks found in file", file=sys.stderr)
        sys.exit(1)
    
    print(f"# Parsed {len(tasks)} tasks from {tasks_file}", file=sys.stderr)
    for task in tasks:
        task_type = detect_task_type(task)
        backend = get_backend(task_type, allowed_backends)
        print(f"#   {task['id']}: {task['description'][:50]}... -> {backend}", file=sys.stderr)
    
    # Generate config
    config = generate_parallel_config(tasks, spec_dir, allowed_backends)
    print(config)

if __name__ == '__main__':
    main()
