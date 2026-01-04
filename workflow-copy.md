是的，`codeagent-wrapper` 是整个系统的执行核心。让我用一个具体场景来模拟完整的多 Agent 工作流触发过程。

---

## 场景：实现用户登录功能

用户在 Claude Code 中输入：
```
/dev "实现用户登录功能，支持邮箱密码登录和JWT token"
```

### 完整工作流触发链

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           /dev 命令触发                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 0: 后端选择 (AskUserQuestion)                                           │
│ ─────────────────────────────────                                           │
│ Claude Code: "请选择允许的后端："                                             │
│   ☑ codex (稳定，高质量)                                                     │
│   ☑ claude (快速，轻量)                                                      │
│   ☑ gemini (UI/UX专家)                                                      │
│                                                                             │
│ 用户选择: [codex, gemini]  →  allowed_backends = {codex, gemini}            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 1: 需求澄清 (AskUserQuestion)                                           │
│ ─────────────────────────────────                                           │
│ Claude Code 提问:                                                            │
│   Q1: "登录失败需要限制重试次数吗？"  →  用户: "是，5次后锁定15分钟"           │
│   Q2: "JWT过期时间？"  →  用户: "access 15分钟，refresh 7天"                  │
│   Q3: "需要记住登录状态吗？"  →  用户: "是"                                   │
│                                                                             │
│ → TodoWrite 创建任务跟踪列表                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 2: codeagent-wrapper 深度分析                                           │
│ ─────────────────────────────────                                           │
│ Claude Code 调用 Bash 工具:                                                  │
│                                                                             │
│   codeagent-wrapper --backend codex - <<'EOF'                               │
│   Analyze the codebase for implementing user login feature.                 │
│   Requirements:                                                             │
│   - Email/password authentication                                           │
│   - JWT tokens (access 15min, refresh 7days)                                │
│   - Login attempt limiting (5 tries, 15min lockout)                         │
│   - Remember me functionality                                               │
│   Deliverables: task breakdown, UI detection, architecture decisions        │
│   EOF                                                                       │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ Codex Agent 执行:                                                       │ │
│ │  1. Glob/Grep/Read 探索代码库                                           │ │
│ │  2. 发现: src/auth/ 目录, React前端, Express后端                        │ │
│ │  3. 输出分析结果:                                                       │ │
│ │     - needs_ui: true (发现 .tsx 组件文件)                               │ │
│ │     - 任务分解: 4个任务                                                 │ │
│ │       task-1: 后端认证API (type: default)                               │ │
│ │       task-2: JWT服务 (type: default)                                   │ │
│ │       task-3: 登录限制中间件 (type: default)                            │ │
│ │       task-4: 登录UI组件 (type: ui)                                     │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 3: 生成开发计划 (Task tool → dev-plan-generator Agent)                  │
│ ─────────────────────────────────                                           │
│ Claude Code 调用 Task 工具启动 dev-plan-generator:                           │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ dev-plan-generator Agent 执行:                                          │ │
│ │  输入: 需求 + Step 2 分析结果                                           │ │
│ │  输出: .claude/specs/user-login/dev-plan.md                             │ │
│ │                                                                         │ │
│ │  # User Login - Development Plan                                        │ │
│ │  ## Task Breakdown                                                      │ │
│ │  ### Task 1: Backend Auth API                                           │ │
│ │  - ID: task-1, type: default                                            │ │
│ │  - File Scope: src/auth/**, src/routes/auth.ts                          │ │
│ │  - Dependencies: None                                                   │ │
│ │  - Test: jest --coverage --testPathPattern=auth                         │ │
│ │  ### Task 2: JWT Service                                                │ │
│ │  - ID: task-2, type: default                                            │ │
│ │  - Dependencies: task-1                                                 │ │
│ │  ### Task 3: Rate Limiting                                              │ │
│ │  - ID: task-3, type: default                                            │ │
│ │  - Dependencies: None                                                   │ │
│ │  ### Task 4: Login UI                                                   │ │
│ │  - ID: task-4, type: ui                                                 │ │
│ │  - Dependencies: task-1, task-2                                         │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Claude Code: "开发计划已生成，确认执行？"                                     │
│ 用户: "确认"                                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 4: 并行开发执行 (codeagent-wrapper --parallel)                          │
│ ─────────────────────────────────                                           │
│ Claude Code 调用 Bash 工具:                                                  │
│                                                                             │
│   codeagent-wrapper --parallel <<'EOF'                                      │
│   ---TASK---                                                                │
│   id: task-1                                                                │
│   backend: codex          ← type:default → codex                            │
│   workdir: .                                                                │
│   ---CONTENT---                                                             │
│   Implement backend auth API...                                             │
│                                                                             │
│   ---TASK---                                                                │
│   id: task-2                                                                │
│   backend: codex          ← type:default → codex                            │
│   dependencies: task-1                                                      │
│   ---CONTENT---                                                             │
│   Implement JWT service...                                                  │
│                                                                             │
│   ---TASK---                                                                │
│   id: task-3                                                                │
│   backend: codex          ← type:default → codex                            │
│   ---CONTENT---                                                             │
│   Implement rate limiting...                                                │
│                                                                             │
│   ---TASK---                                                                │
│   id: task-4                                                                │
│   backend: gemini         ← type:ui → gemini (在allowed_backends中)         │
│   dependencies: task-1, task-2                                              │
│   ---CONTENT---                                                             │
│   Implement login UI components...                                          │
│   EOF                                                                       │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ codeagent-wrapper 内部执行:                                             │ │
│ │                                                                         │ │
│ │  1. topologicalSort() 拓扑排序:                                         │ │
│ │     Layer 1: [task-1, task-3]  ← 无依赖，可并行                         │ │
│ │     Layer 2: [task-2]          ← 依赖 task-1                            │ │
│ │     Layer 3: [task-4]          ← 依赖 task-1, task-2                    │ │
│ │                                                                         │ │
│ │  2. executeConcurrent() 并行执行:                                       │ │
│ │                                                                         │ │
│ │     ┌──────────────┐    ┌──────────────┐                                │ │
│ │     │   task-1     │    │   task-3     │  ← Layer 1 并行               │ │
│ │     │ codex agent  │    │ codex agent  │                                │ │
│ │     │ 认证API实现   │    │ 限流中间件   │                                │ │
│ │     └──────┬───────┘    └──────────────┘                                │ │
│ │            │                                                            │ │
│ │            ▼                                                            │ │
│ │     ┌──────────────┐                                                    │ │
│ │     │   task-2     │  ← Layer 2                                        │ │
│ │     │ codex agent  │                                                    │ │
│ │     │ JWT服务实现   │                                                    │ │
│ │     └──────┬───────┘                                                    │ │
│ │            │                                                            │ │
│ │            ▼                                                            │ │
│ │     ┌──────────────┐                                                    │ │
│ │     │   task-4     │  ← Layer 3                                        │ │
│ │     │ gemini agent │  ← UI任务用gemini                                  │ │
│ │     │ 登录UI组件   │                                                    │ │
│ │     └──────────────┘                                                    │ │
│ │                                                                         │ │
│ │  3. 每个任务独立调用对应后端CLI:                                         │ │
│ │     - codex e --json "task content"                                     │ │
│ │     - gemini -o stream-json -y -p "task content"                        │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ 输出: 执行报告 (每个任务的覆盖率、修改文件、测试结果)                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 5: 覆盖率验证                                                           │
│ ─────────────────                                                           │
│ Claude Code 检查每个任务的覆盖率:                                            │
│   task-1: 92% ✓                                                             │
│   task-2: 95% ✓                                                             │
│   task-3: 88% ✗ → 请求补充测试 (最多2轮)                                    │
│   task-4: 91% ✓                                                             │
│                                                                             │
│ 如果 task-3 补测后仍 <90%，报告给用户                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 6: 完成总结                                                             │
│ ─────────────                                                               │
│ Claude Code 输出:                                                            │
│                                                                             │
│   ✅ 用户登录功能实现完成                                                    │
│   - 4个任务全部完成                                                          │
│   - 平均覆盖率: 91.5%                                                        │
│   - 修改文件: 12个                                                           │
│     - src/auth/authService.ts                                               │
│     - src/auth/jwtService.ts                                                │
│     - src/middleware/rateLimiter.ts                                         │
│     - src/components/LoginForm.tsx                                          │
│     - ...                                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 关键触发点总结

| 步骤 | 触发方式 | 执行者 |
|------|----------|--------|
| Step 0-1 | AskUserQuestion | Claude Code |
| Step 2 | `codeagent-wrapper --backend codex` | Codex Agent |
| Step 3 | Task tool → dev-plan-generator | dev-plan-generator Agent |
| Step 4 | `codeagent-wrapper --parallel` | 多个 Agent 并行 (Codex/Gemini) |
| Step 5-6 | 内部逻辑 | Claude Code |

**核心流程**：Claude Code 作为编排者，通过 `codeagent-wrapper` 调度多个 AI 后端执行实际的代码修改，实现了职责分离和并行加速。

## Step 5 & Step 6 输出实现原理

### 数据流

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  codeagent-wrapper --parallel 执行完成后                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. executeConcurrent() 返回 []TaskResult                                   │
│     每个 TaskResult 包含:                                                    │
│     - TaskID, ExitCode, Message (后端原始输出)                               │
│     - SessionID, Error, LogPath                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. 结构化字段提取 (main.go:255-275)                                         │
│                                                                             │
│     for i := range results {                                                │
│         lines := strings.Split(results[i].Message, "\n")                    │
│                                                                             │
│         // 覆盖率提取: "Coverage: 92%" → "92%"                               │
│         results[i].Coverage = extractCoverageFromLines(lines)               │
│         results[i].CoverageNum = extractCoverageNum(results[i].Coverage)    │
│                                                                             │
│         // 修改文件提取: "Modified: src/auth.ts" → ["src/auth.ts"]           │
│         results[i].FilesChanged = extractFilesChangedFromLines(lines)       │
│                                                                             │
│         // 测试结果提取: "12 passed, 2 failed" → passed=12, failed=2        │
│         results[i].TestsPassed, results[i].TestsFailed = ...                │
│                                                                             │
│         // 关键输出摘要                                                      │
│         results[i].KeyOutput = extractKeyOutputFromLines(lines, 150)        │
│     }                                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. generateFinalOutputWithMode() 生成报告 (executor.go:522-680)            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 关键提取函数 (utils.go)

| 函数 | 作用 | 匹配模式示例 |
|------|------|-------------|
| `extractCoverageFromLines()` | 提取覆盖率 | `"Coverage: 92%"`, `"TOTAL 92%"`, `"92% coverage"` |
| `extractCoverageNum()` | 转数值 | `"92%"` → `92.0` |
| `extractFilesChangedFromLines()` | 提取修改文件 | `"Modified: src/auth.ts"`, `"Created: test.go"` |
| `extractTestResultsFromLines()` | 提取测试结果 | `"12 passed, 2 failed"`, `"Tests: 2 failed, 12 passed"` |
| `extractKeyOutputFromLines()` | 提取关键摘要 | `"Summary: ..."`, `"Implemented: ..."` |
| `extractCoverageGap()` | 提取覆盖缺口 | `"uncovered lines"`, `"branch not taken"` |
| `extractErrorDetail()` | 提取错误详情 | `"Error:"`, `"FAIL"`, `"exception"` |

### 报告生成逻辑 (executor.go)

```go
func generateFinalOutputWithMode(results []TaskResult, summaryOnly bool) string {
    // 1. 统计成功/失败/低覆盖率任务数
    success, failed, belowTarget := 0, 0, 0
    for _, res := range results {
        if res.ExitCode == 0 && res.Error == "" {
            success++
            if res.CoverageNum < 90.0 {  // 默认目标 90%
                belowTarget++
            }
        } else {
            failed++
        }
    }

    // 2. 输出报告头
    // "=== Execution Report ==="
    // "4 tasks | 3 passed | 1 failed | 1 below 90%"

    // 3. 每个任务的详细结果
    for _, res := range results {
        if isSuccess && !isBelowTarget {
            // "### task-1 ✓ 92%"
            // "Did: Implemented auth service..."
            // "Files: src/auth.ts, tests/auth.test.ts"
            // "Tests: 12 passed"
        } else if isSuccess && isBelowTarget {
            // "### task-3 ⚠️ 88% (below 90%)"
            // "Gap: uncovered lines in error handler"
        } else {
            // "### task-2 ✗ FAILED"
            // "Exit code: 1"
            // "Error: ..."
        }
    }

    // 4. 总结部分
    // "## Summary"
    // "- 3/4 completed successfully"
    // "- Coverage: task-3"  (需要补测的任务)
}
```

### 实际输出示例

```
=== Execution Report ===
4 tasks | 3 passed | 1 failed | 1 below 90%

## Task Results

### task-1 ✓ 92%
Did: Implemented backend auth API with email/password validation
Files: src/auth/authService.ts, src/routes/auth.ts, tests/auth/auth.test.ts
Tests: 15 passed
Log: /tmp/codeagent-wrapper-task-1.log

### task-2 ✓ 95%
Did: Implemented JWT service with access/refresh tokens
Files: src/auth/jwtService.ts, tests/auth/jwt.test.ts
Tests: 8 passed

### task-3 ⚠️ 88% (below 90%)
Did: Implemented rate limiting middleware
Files: src/middleware/rateLimiter.ts
Tests: 6 passed
Gap: uncovered lines in error handler (lines 45-52)

### task-4 ✓ 91%
Did: Created login UI components with form validation
Files: src/components/LoginForm.tsx, src/components/LoginForm.css
Tests: 10 passed

## Summary
- 3/4 completed successfully
- Coverage: task-3
```

### Claude Code 如何使用这个输出

1. **Step 5 覆盖率验证**：Claude Code 解析报告，检查每个任务的 `CoverageNum`
   - `≥90%` → 通过
   - `<90%` → 触发补测流程 (最多2轮)

2. **Step 6 完成总结**：Claude Code 直接将报告呈现给用户，或进一步格式化

整个流程的关键是 `codeagent-wrapper` 从后端 (Codex/Claude/Gemini) 的原始输出中**智能提取结构化数据**，然后生成统一格式的报告供 Claude Code 解析和展示。

好问题！让我分析 skills 在这个工作流中的作用。

现在让我查看 skills 是如何被加载和使用的：

---

## Skills 在工作流中的作用

### 1. Skills 是什么？

Skills 是 **Claude Code 的知识增强模块**，为 AI 提供特定领域的专业知识和使用指南。它们不是可执行代码，而是**结构化的提示词文档**。

```
~/.claude/
├── skills/
│   ├── codeagent/
│   │   └── SKILL.md          # codeagent-wrapper 使用指南
│   ├── product-requirements/
│   │   └── SKILL.md          # PRD 生成技能
│   └── prototype-prompt-generator/
│       └── SKILL.md          # 原型设计技能
└── skill-rules.json          # 技能触发规则
```

### 2. Skills 的触发机制

通过 `skill-rules.json` 定义触发条件：

```json
{
  "skills": {
    "codeagent": {
      "type": "execution",
      "enforcement": "suggest",
      "priority": "high",
      "promptTriggers": {
        "keywords": ["codeagent", "multi-backend", "parallel task", "gemini"],
        "intentPatterns": ["\\bcodeagent\\b", "backend\\s+(codex|claude|gemini)"]
      }
    }
  }
}
```

**触发流程**：
```
用户输入: "使用 codex 后端重构这个模块"
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Claude Code 检测关键词/意图模式                                              │
│  - 匹配 "codex" → codeagent skill                                           │
│  - 匹配 "重构" → codex skill                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  加载 skills/codeagent/SKILL.md 到上下文                                     │
│  Claude Code 现在"知道"如何使用 codeagent-wrapper                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3. Skills 在 /dev 工作流中的角色

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           /dev 工作流                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│  codeagent Skill  │   │ product-requirements│   │ prototype-prompt │
│                   │   │      Skill         │   │     Skill        │
│  提供:            │   │                    │   │                  │
│  - 如何调用       │   │  提供:             │   │  提供:           │
│    codeagent-     │   │  - PRD 生成流程    │   │  - UI 原型设计   │
│    wrapper        │   │  - 质量评分标准    │   │    提示词生成    │
│  - 后端选择指南   │   │  - 需求澄清问题    │   │  - 设计系统参考  │
│  - 并行执行格式   │   │                    │   │                  │
│  - 错误处理       │   │                    │   │                  │
└───────────────────┘   └───────────────────┘   └───────────────────┘
        │                           │                           │
        │                           │                           │
        ▼                           ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Claude Code 获得专业知识，知道如何正确执行工作流                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4. 具体作用示例

#### codeagent Skill 的作用

当 `/dev` 命令需要调用 `codeagent-wrapper` 时，Skill 告诉 Claude Code：

```markdown
## 如何调用 (来自 SKILL.md)

**HEREDOC syntax** (recommended):
```bash
codeagent-wrapper - [working_dir] <<'EOF'
<task content here>
EOF
```

**并行执行格式**:
```bash
codeagent-wrapper --parallel <<'EOF'
---TASK---
id: task1
backend: codex
workdir: /path/to/dir
---CONTENT---
task content
EOF
```
```

**没有 Skill**：Claude Code 可能不知道正确的调用格式
**有 Skill**：Claude Code 知道精确的语法、参数、最佳实践

### 5. Skills vs Commands vs Agents 对比

| 组件 | 类型 | 作用 | 触发方式 |
|------|------|------|----------|
| **Skills** | 知识文档 | 提供专业知识和使用指南 | 关键词/意图自动触发 |
| **Commands** | 工作流定义 | 定义完整的执行流程 | 用户显式调用 `/dev` |
| **Agents** | 子任务执行者 | 执行特定子任务 | 被 Command 通过 Task tool 调用 |

### 6. 工作流中的协作关系

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  用户: /dev "实现用户登录"                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Command: dev.md                                                            │
│  ─────────────────                                                          │
│  定义 7 步工作流                                                             │
│  Step 2: 调用 codeagent-wrapper 分析                                        │
│  Step 3: 调用 dev-plan-generator agent                                      │
│  Step 4: 调用 codeagent-wrapper --parallel                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │   Skill     │ │   Agent     │ │   Tool      │
            │ (codeagent) │ │(dev-plan-   │ │(codeagent-  │
            │             │ │ generator)  │ │ wrapper)    │
            │ 提供知识:   │ │             │ │             │
            │ 如何正确    │ │ 生成        │ │ 实际执行    │
            │ 调用工具    │ │ dev-plan.md │ │ 代码修改    │
            └─────────────┘ └─────────────┘ └─────────────┘
```

### 7. 总结

**Skills 的核心价值**：

1. **知识注入** - 让 Claude Code 知道如何正确使用工具
2. **最佳实践** - 提供后端选择指南、错误处理策略
3. **格式规范** - 确保调用格式正确 (HEREDOC、parallel config)
4. **自动触发** - 根据用户意图自动加载相关知识

**类比**：
- Commands = 菜谱 (定义做什么)
- Agents = 厨师 (执行特定任务)
- Skills = 烹饪知识 (知道如何正确操作)
- codeagent-wrapper = 厨具 (实际执行工具)