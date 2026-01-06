---
name: multi-agent-orchestrator
description: |
  Orchestrate multi-agent workflows with kiro-cli and Gemini workers.
  
  **Trigger Conditions:**
  - WHEN starting execution from a Kiro spec directory
  - WHEN dispatching tasks to worker agents
  - WHEN handling task completion and review
  - WHEN synchronizing state to PULSE document
  
  **Use Cases:**
  - Multi-agent code implementation with kiro-cli and Gemini
  - Tmux-based task visualization and monitoring
  - Structured review workflows with Codex reviewers
  - Dual-document state management (AGENT_STATE.json + PROJECT_PULSE.md)
license: MIT
---

# Multi-Agent Orchestrator

## Overview

Coordinates kiro-cli (code) and Gemini (UI) agents within a tmux environment, with Codex as the central orchestrator.

**Architecture:**
- **Spec Phase**: User creates requirements.md, design.md, tasks.md in Kiro IDE
- **Execution Phase**: Codex orchestrates workers via codeagent-wrapper

## Commands

- `$orchestrator start <spec_path>` - Initialize orchestration from spec directory
- `$orchestrator dispatch` - Dispatch ready tasks to workers
- `$orchestrator status` - Show current orchestration state
- `$orchestrator review` - Spawn reviews for completed tasks
- `$orchestrator sync` - Sync state to PULSE document

## Workflow

1. **Initialize**: Parse tasks.md, create AGENT_STATE.json and PROJECT_PULSE.md
2. **Dispatch**: Collect ready tasks, invoke codeagent-wrapper --parallel
3. **Execute**: Workers run in tmux panes, results written to state file
4. **Review**: Spawn Codex reviewers for completed tasks
5. **Consolidate**: Merge review findings into final reports
6. **Sync**: Update PROJECT_PULSE.md with current state

## Agent Assignment

| Task Type | Agent | Backend |
|-----------|-------|---------|
| Code | kiro-cli | `--backend kiro-cli` |
| UI | Gemini | `--backend gemini` |
| Review | Codex | `--backend codex` |

## Task State Machine

```
not_started → in_progress → pending_review → under_review → final_review → completed
     ↓              ↓
  blocked ←────────┘
```

## Resources

**Always run scripts with `--help` first** to see usage before reading source code.

### scripts/

- `init_orchestration.py` - Initialize orchestration from spec directory
  ```bash
  python scripts/init_orchestration.py <spec_path> [--session <name>]
  ```

- `dispatch_batch.py` - Dispatch ready tasks to workers
  ```bash
  python scripts/dispatch_batch.py <state_file> [--dry-run]
  ```

- `dispatch_reviews.py` - Dispatch review tasks for completed work
  ```bash
  python scripts/dispatch_reviews.py <state_file> [--dry-run]
  ```

- `spec_parser.py` - Parse tasks.md to extract task definitions
  ```bash
  python scripts/spec_parser.py <spec_directory>
  ```

### references/

- `agent-state-schema.json` - JSON Schema for AGENT_STATE.json validation
- `task-state-machine.md` - Task state transition documentation

## Integration with codeagent-wrapper

The orchestrator invokes codeagent-wrapper with tmux support:

```bash
codeagent-wrapper --parallel \
  --tmux-session orchestration \
  --state-file /path/to/AGENT_STATE.json \
  <<'EOF'
---TASK---
id: task-001
backend: kiro-cli
workdir: .
---CONTENT---
Implement user authentication...
EOF
```

## Criticality Levels

| Level | Review Count |
|-------|--------------|
| standard | 1 reviewer |
| complex | 2+ reviewers |
| security-sensitive | 2+ reviewers with security focus |

