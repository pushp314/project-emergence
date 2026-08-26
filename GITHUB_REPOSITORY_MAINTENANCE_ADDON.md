# GITHUB_REPOSITORY_MAINTENANCE_ADDON.md

## PURPOSE

This addon makes GitHub repository maintenance a first-class responsibility of the A2A Autonomous AI Sandbox.

The coding agents are not only responsible for writing code.

They are also responsible for maintaining a clean, understandable, traceable Git/GitHub history of the project.

The repository should become the permanent external record of the system's development.

---

# 1. CORE PRINCIPLE

The project must maintain two synchronized forms of truth:

```text
LIVE SYSTEM
    ↓
Git Repository
    ↓
GitHub Repository
    ↓
Permanent Development History
```

Every meaningful implementation cycle should leave behind:

- working code
- tests
- documentation
- project state
- Git history
- useful commit message
- issue/decision context where appropriate

The agents MUST NOT treat GitHub as merely a place to upload code.

GitHub is part of the engineering workflow.

---

# 2. REPOSITORY OWNERSHIP

The agents may maintain the repository according to the permissions granted to them.

They may:

- inspect repository history
- create branches
- create commits
- update documentation
- create issues where appropriate
- update issues
- create pull requests where appropriate
- review their own proposed changes using tests and diffs
- push approved branches
- maintain project documentation
- maintain changelogs
- record experiments

They MUST NOT assume they have permission for destructive GitHub operations.

---

# 3. PROTECTED OPERATIONS

The following require explicit human approval unless the user has deliberately configured otherwise:

- deleting the repository
- deleting important branches
- force pushing
- rewriting public Git history
- deleting releases
- changing repository ownership
- changing repository visibility
- changing GitHub security settings
- changing collaborators/permissions
- deleting important issues
- deleting project history
- exposing secrets
- publishing private data

Default principle:

```text
CREATE / DOCUMENT / TEST
        ↓
SAFE

DELETE / REWRITE / EXPOSE
        ↓
REQUIRE APPROVAL
```

---

# 4. BRANCHING STRATEGY

Do not make every experiment directly on the main branch.

Recommended:

```text
main
 │
 ├── feature/...
 ├── experiment/...
 ├── research/...
 ├── fix/...
 └── self-modification/...
```

Examples:

```text
feature/browser-research
fix/event-bus-generation
experiment/context-compression
research/model-routing
self-modification/agent-memory
```

Branch names should describe the purpose.

---

# 5. MAIN BRANCH

The `main` branch should represent the latest known stable state.

Do not intentionally leave:

- broken code
- failing tests
- experimental temporary code
- debugging artifacts
- secrets
- generated junk

in `main`.

Experiments belong on separate branches until they are validated.

---

# 6. COMMIT POLICY

Commits should represent meaningful engineering changes.

Good:

```text
feat: add event bus persistence
fix: handle Ollama generation timeout
test: add agent interruption tests
docs: update browser research architecture
perf: reduce repeated context serialization
```

Bad:

```text
update
fix stuff
changes
asdf
final
final2
working now
```

A commit should explain WHAT changed.

The code/documentation should explain WHY.

---

# 7. ATOMIC COMMITS

Prefer small, logically coherent commits.

Example:

```text
feat: add browser research interface
test: add browser research integration tests
docs: document browser provenance
```

Do not combine unrelated changes into one giant commit.

---

# 8. BEFORE COMMITTING

The agent MUST inspect:

```bash
git status
git diff
```

Then verify:

- intended files changed
- no secrets are present
- no credentials are present
- no accidental large files are present
- no temporary debug files are included
- tests relevant to the change pass
- documentation is updated

Only then commit.

---

# 9. SECRET PROTECTION

NEVER commit:

- API keys
- passwords
- access tokens
- SSH private keys
- browser session data
- cookies
- authentication tokens
- private personal data
- `.env` files containing secrets
- credential databases

Before pushing, inspect the diff.

Use:

```text
.env
.env.*
*.key
*.pem
credentials.*
secrets.*
```

or equivalent repository-specific ignore rules where appropriate.

If a secret is accidentally exposed:

1. Stop.
2. Do not continue pushing.
3. Inform the human.
4. Rotate/revoke the secret.
5. Remove it from the repository history using an appropriate controlled process.

---

# 10. GITIGNORE

Maintain an appropriate `.gitignore`.

At minimum, consider excluding:

- virtual environments
- Python caches
- OS metadata
- IDE metadata
- local databases where appropriate
- logs
- model files
- temporary artifacts
- credentials
- local session data
- generated runtime files

Do NOT blindly ignore files that are required for reproducibility.

---

# 11. SESSION → GIT CHECKPOINT

Every significant development session should produce a Git checkpoint.

Example:

```text
Agent session
    ↓
Implementation
    ↓
Tests
    ↓
Documentation
    ↓
PROJECT_STATE update
    ↓
Git commit
    ↓
Optional push
```

The commit should make it possible to identify what the agent accomplished.

---

# 12. EXPERIMENTS

Experiments should normally use separate branches.

Example:

```text
experiment/model-routing
experiment/context-compression
experiment/multi-agent-scheduling
experiment/memory-retrieval
```

Each experiment should document:

- hypothesis
- baseline
- change
- benchmark
- result
- conclusion

If the experiment fails, preserve the branch/history when useful.

A failed experiment is still useful research.

---

# 13. SELF-MODIFICATION + GIT

Self-modification MUST integrate with Git.

Recommended flow:

```text
Agent detects problem
        ↓
Research
        ↓
Modification proposal
        ↓
Create isolated branch/worktree
        ↓
Modify code
        ↓
Run tests
        ↓
Benchmark
        ↓
Document result
        ↓
Human approval
        ↓
Merge
```

Example branch:

```text
self-modification/SM-004-context-cache
```

The modification ID should appear in the documentation and preferably the commit/PR metadata.

---

# 14. ROLLBACK

Git is part of the rollback mechanism.

Before risky self-modification:

- create a checkpoint
- ensure the current state is committed
- record the commit hash
- record the experiment ID
- record the modification ID

Example:

```text
Modification: SM-004
Baseline commit: a91f42c
Experiment branch: self-modification/SM-004-context-cache
```

If the modification fails:

```text
rollback
    ↓
restore known-good commit
    ↓
document failure
    ↓
preserve evidence
```

Never delete the evidence of a failed modification.

---

# 15. PULL REQUESTS

For meaningful changes, use a Pull Request workflow when practical.

A PR should contain:

```text
## What changed

## Why

## Architecture impact

## Tests

## Performance impact

## Risks

## Evidence

## Rollback plan
```

For self-modification:

```text
## Modification ID
SM-004

## Hypothesis

## Baseline

## Change

## Benchmark

## Result

## Decision
```

The PR should allow the human to understand the change without reading the entire conversation.

---

# 16. ISSUES

GitHub Issues may be used as persistent task records.

Create an issue when a problem is:

- significant
- long-running
- blocked
- architectural
- worth tracking across sessions
- discovered during an experiment

Do not create hundreds of trivial issues.

Prefer labels such as:

```text
bug
feature
research
experiment
performance
architecture
security
documentation
self-modification
blocked
```

---

# 17. RESEARCH ISSUES

When an agent discovers an important unresolved research question, it may create or update a research issue.

Example:

```text
Research: Can dynamic context compression improve local inference latency?
```

The issue should contain:

- question
- current evidence
- sources
- hypotheses
- experiments
- results
- conclusion

---

# 18. PERFORMANCE TRACKING

Performance improvements should be connected to Git history.

Example:

```text
Baseline:
commit a91f42c

RAM:
11.8 GB

Latency:
8.4 sec

Tokens/sec:
12.1
```

After change:

```text
commit b72d19e

RAM:
10.2 GB

Latency:
6.7 sec

Tokens/sec:
15.3
```

Document measurable improvements rather than claiming improvement from subjective observation alone.

---

# 19. AUTOMATED CHECKS

Before pushing important changes, run available checks such as:

```text
tests
lint
type checking
format checking
security checks
dependency checks
```

Use the repository's actual tooling.

Do not invent commands that do not exist.

If a check cannot be run, document why.

---

# 20. GITHUB ACTIONS

GitHub Actions may eventually be used for:

- tests
- linting
- type checks
- build validation
- documentation validation
- security checks

Do not add complex CI infrastructure unnecessarily.

Start with the minimum useful automation.

---

# 21. RELEASES

When the system reaches meaningful milestones, maintain releases.

Example:

```text
v0.1.0
Foundation

v0.2.0
Multi-agent runtime

v0.3.0
Research + evidence

v0.4.0
Tools + permissions

v0.5.0
Self-modification experiments
```

Versioning strategy may evolve.

Do not create releases for every tiny change.

---

# 22. CHANGELOG SYNCHRONIZATION

GitHub releases and repository documentation should remain consistent with:

```text
CHANGELOG.md
PROJECT_STATE.md
IMPLEMENTATION_LOG.md
```

Do not maintain separate contradictory histories.

---

# 23. AGENT HANDOFF THROUGH GITHUB

GitHub should help another agent understand the project.

A future agent should be able to inspect:

```text
README
RULES
ARCHITECTURE
PROJECT_STATE
CHANGELOG
DECISIONS
KNOWN_ISSUES
Git history
Issues
Pull Requests
Experiments
```

and reconstruct the development trajectory.

This reduces dependence on previous AI conversations.

---

# 24. COMMIT MESSAGE + AGENT IDENTITY

Where useful, include the agent/session/modification identifier in commit metadata.

Example:

```text
feat: implement browser evidence pipeline

Session: 018
Modification: none
```

Do not include sensitive information.

The exact metadata format may be adapted to the repository.

---

# 25. README MAINTENANCE

The README should always explain the current usable state.

It should include, where appropriate:

- project purpose
- architecture overview
- installation
- configuration
- running the CLI
- supported models
- supported tools
- development instructions
- testing
- current limitations
- safety/permission model

Do not claim features that are not actually implemented.

---

# 26. DOCUMENTATION SHOULD FOLLOW IMPLEMENTATION

When a feature changes architecture or user behavior:

```text
Code change
+
Tests
+
Documentation
```

must be treated as one implementation unit.

Do not postpone important documentation indefinitely.

---

# 27. AGENT MUST VERIFY REMOTE STATE

Before pushing:

```text
git fetch
git status
```

Determine whether the remote changed.

Do not blindly overwrite remote work.

If conflicts exist:

1. Inspect them.
2. Preserve other work.
3. Resolve carefully.
4. Test again.
5. Document important resolution decisions.

---

# 28. NEVER FORCE PUSH BY DEFAULT

Do not use:

```bash
git push --force
```

unless explicitly authorized and the consequences are understood.

Prefer safe alternatives.

---

# 29. REMOTE REPOSITORY AS BACKUP

The GitHub repository can serve as a backup of:

- source code
- documentation
- architecture
- experiments
- decisions
- development history

But do not push private runtime data merely because it is useful locally.

Keep local/private data separate from public repository content.

---

# 30. AGENT AUTONOMY

The goal is not for the agent to ask the human for approval for every normal Git operation.

Normal low-risk maintenance may be automated:

```text
inspect
branch
edit
test
commit
document
```

Human approval should focus on meaningful risk:

```text
destructive Git operations
public exposure
security changes
major architectural changes
merging risky self-modifications
external actions
```

---

# 31. REPOSITORY HEALTH

The agent should periodically check:

- uncommitted changes
- stale branches
- failing tests
- outdated documentation
- accidental generated files
- oversized files
- secrets
- broken CI
- dependency problems
- unresolved critical issues

Do not perform destructive cleanup automatically.

Report questionable items first.

---

# 32. FINAL GITHUB WORKFLOW

The preferred development cycle is:

```text
                    ┌───────────────┐
                    │   USER/GOAL   │
                    └───────┬───────┘
                            ↓
                       Agent plans
                            ↓
                       Git branch
                            ↓
                      Implementation
                            ↓
                           Tests
                            ↓
                       Benchmark
                            ↓
                       Documentation
                            ↓
                    PROJECT_STATE update
                            ↓
                         Git commit
                            ↓
                       GitHub push
                            ↓
                    Issue / PR if useful
                            ↓
                    Human review when needed
                            ↓
                         Merge
                            ↓
                      Stable main
```

---

# 33. ACCEPTANCE CRITERIA

This addon is implemented when:

- [ ] Git repository is initialized/configured correctly.
- [ ] `.gitignore` protects local/generated/private data.
- [ ] Main branch represents stable code.
- [ ] Feature work uses appropriate branches.
- [ ] Meaningful changes receive meaningful commits.
- [ ] Documentation changes are tracked.
- [ ] Self-modifications use isolated Git branches/worktrees.
- [ ] Self-modifications record baseline commits.
- [ ] Experiments can be traced to Git history.
- [ ] Rollback can identify a known-good commit.
- [ ] Secrets are prevented from entering the repository.
- [ ] Important work can be represented through Issues/PRs.
- [ ] GitHub can serve as a development handoff record.
- [ ] Another coding agent can reconstruct project history from the repository.
- [ ] Agents do not perform destructive remote Git operations without authorization.

---

# FINAL IMPLEMENTATION INSTRUCTION

Read:

1. `RULES.md`
2. `ARCHITECTURE.md`
3. `AUTONOMOUS_RESEARCH_EVIDENCE_ADDON.md`
4. `SELF_MODIFICATION_ADDON.md`
5. `CLI_FIRST_INTERFACE_ADDON.md`
6. `GITHUB_REPOSITORY_MAINTENANCE_ADDON.md`

Integrate Git/GitHub maintenance into the existing architecture.

Do not redesign the entire system just to add GitHub support.

Git should become a persistent engineering layer around the project:

```text
Code
+
Tests
+
Evidence
+
Experiments
+
Documentation
+
Git History
+
GitHub
```

The objective is that the project can continue evolving for months across different AI coding agents without losing context, history, reasoning, experiments, or implementation state.
