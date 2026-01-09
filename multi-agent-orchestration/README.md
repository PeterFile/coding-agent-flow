# Multi-Agent Orchestration System

Coordinates kiro-cli, Gemini, and Codex agents for parallel task execution with structured review workflows.

## Structure

```
multi-agent-orchestration/
├── skill/                  # Skill definition and scripts
│   ├── SKILL.md
│   ├── scripts/            # Python orchestration scripts
│   └── references/         # Schema and prompts
├── docs/                   # Documentation
│   ├── workflow-simulation.md
│   └── review.md
└── specs/                  # Kiro spec documents
```

## Quick Start

```bash
# Initialize
python multi-agent-orchestration/skill/scripts/init_orchestration.py /path/to/spec --session my-feature

# Dispatch tasks
python multi-agent-orchestration/skill/scripts/dispatch_batch.py AGENT_STATE.json

# Dispatch reviews
python multi-agent-orchestration/skill/scripts/dispatch_reviews.py AGENT_STATE.json

# Sync status
python multi-agent-orchestration/skill/scripts/sync_pulse.py AGENT_STATE.json PROJECT_PULSE.md
```

## Prerequisites

- Python 3.x + pytest/hypothesis
- Go 1.21+ (for codeagent-wrapper)
- tmux (Linux/macOS)
- AI backend: kiro-cli, gemini, or codex

## Related

- Go state management code remains in `codeagent-wrapper/` (state.go, state_validation.go, report.go)
- See `docs/workflow-simulation.md` for complete workflow walkthrough
