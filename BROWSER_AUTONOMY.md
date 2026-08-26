# BROWSER_AUTONOMY.md

## 1. Purpose

This document defines the Autonomous Browser Control capability for the agent-society experiment.

The browser is not merely a search API. It is an external research environment in which autonomous agents may independently search, navigate, inspect pages, compare evidence, follow leads, conduct multi-step research, download permitted research material, revise hypotheses, and continue investigating without requiring a human to specify every browser action.

This capability integrates with:
- Tool Gateway
- Permission Engine
- Evidence Plane
- Memory Plane
- Context Manager
- Resource Manager
- SQLite
- Master Control Plane

This document is an architecture/specification addon. It does not authorize implementation changes by itself.

## 2. Core Principle

> The browser is an environment, not merely an information API.

The agent should be able to decide:
1. What it needs to know.
2. Where it might find it.
3. Which source to inspect.
4. What to click/open/search next.
5. What evidence is required.
6. Whether another source is needed.
7. Whether evidence changes its hypothesis.
8. What to investigate next.

The human should not need to prescribe every browser operation.

## 3. Architecture

```text
                    AGENT A / AGENT B
                           |
                           v
                     TOOL GATEWAY
                           |
                    BROWSER MANAGER
                           |
              +------------+------------+
              |            |            |
              v            v            v
        Navigation      Actions     Observation
              |            |            |
              |       +----+----+       |
              |       |    |    |       |
              |       v    v    v       |
              |     Click Type Scroll   |
              |            |            |
              |            v            |
              |       Forms / Pages     |
              |                         |
              +-----------+-------------+
                          |
                          v
                   BROWSER SESSION
                          |
                 +--------+--------+
                 |                 |
                 v                 v
              DOM/Text        Screenshot
              /A11y Tree      /Visual State
                 |                 |
                 +--------+--------+
                          |
                          v
                     AGENT CONTEXT
                          |
                   +------+------+
                   |             |
                   v             v
                MEMORY       EVIDENCE
```

## 4. Browser Manager

Agents must not directly control the underlying browser process.

Use:

```text
Agent
  |
  v
Browser Tool Request
  |
  v
Tool Gateway
  |
  v
Permission Engine
  |
  v
Browser Manager
  |
  v
Browser
```

The Browser Manager provides:
- permission enforcement
- action recording
- resource control
- browser-session isolation
- state management
- error recovery
- consistent tool interfaces

## 5. Browser Capabilities

### Navigation
- Open URL
- Navigate to URL
- Back
- Forward
- Reload
- Open new tab
- Switch tab
- Close tab
- List tabs
- Read current URL
- Read page title

### Interaction
- Click
- Double-click
- Type
- Clear field
- Select option
- Hover
- Scroll
- Press keyboard key
- Submit forms where permitted
- Wait for page/content state

### Observation
- Extract page text
- Read DOM
- Read accessibility tree
- Inspect metadata
- Identify interactive elements
- Identify links
- Identify forms
- Identify headings
- Identify tables
- Read visible state
- Capture screenshots when required

### Research
- Search
- Open search results
- Follow links
- Search within pages
- Compare multiple sources
- Track source URLs
- Extract evidence
- Revisit sources
- Follow research chains

### Files
Where permitted:
- Download public research material
- Read downloaded research material
- Upload files only when the permission system allows it

## 6. Agent Autonomy

The browser must not force agents into a fixed workflow.

Agents may independently decide:
- whether browsing is necessary
- which source to use
- how many sources to inspect
- whether to follow links
- whether to search again
- whether evidence is sufficient
- whether to challenge a conclusion
- whether to ask the other agent for verification
- whether to continue researching
- whether to abandon a research path

Example:

```text
Agent
  -> verify claim
  -> search
  -> inspect source A
  -> follow reference to source B
  -> inspect source B
  -> investigate dataset C
  -> revise hypothesis
```

## 7. Browser State

Recommended state:

```text
BrowserSession
|- session_id
|- agent_id
|- browser_instance
|- active_tab
|- tabs
|- current_url
|- page_title
|- navigation_history
|- pending_actions
|- downloads
|- permissions
`- timestamps
```

Do not continuously inject complete browser history into model context.

## 8. Observation Strategy

Prefer the least expensive useful representation:

1. Accessibility tree
2. DOM structure
3. Extracted visible text
4. Page metadata
5. Structured elements
6. Screenshot

Use screenshots when visual information is genuinely required, such as charts, diagrams, canvas applications, or interfaces where DOM information is insufficient.

This is especially important on an M4 16 GB machine.

## 9. Browser Action Loop

```text
OBSERVE
   |
UNDERSTAND STATE
   |
DECIDE NEXT ACTION
   |
REQUEST TOOL
   |
PERMISSION CHECK
   |
EXECUTE
   |
OBSERVE RESULT
   |
UPDATE CONTEXT
   |
DECIDE AGAIN
```

Continue until:
- objective is satisfied
- agent stops
- objective changes
- Master interrupts
- permission is denied
- resource limit is reached
- unrecoverable error occurs
- session is stopped

## 10. Permission Architecture

Full browser control does not mean unrestricted real-world authority.

Every browser action passes through the Tool Gateway.

```text
Agent
  |
Browser Action
  |
Permission Engine
  +-- ALLOW
  +-- DENY
  `-- MASTER APPROVAL
```

The agent may decide that it wants an action. The Permission Engine decides whether it is technically permitted.

> Decision freedom != system authority.

## 11. Permission Classes

### Class A - Low-risk autonomous browsing
Normally allowed:
- Search
- Open public pages
- Read public information
- Navigate links
- Scroll
- Search within pages
- Compare public sources
- Read public documentation
- Read public research papers
- Inspect public GitHub repositories

### Class B - Controlled operations
May require policy checks:
- Downloads
- Uploads
- Non-public resources
- Persistent browser storage
- Large downloads
- Resource-intensive pages

### Class C - External-impacting actions
Normally require Master approval:
- Send messages
- Submit forms
- Create accounts
- Purchases
- Publish content
- Modify external accounts
- Consequential external changes
- Upload sensitive information

### Class D - Forbidden
Must be blocked:
- Credential theft
- Password extraction
- API-key extraction
- Circumventing authentication
- Bypassing permission controls
- Disabling security mechanisms
- Modifying Master Control security
- Modifying Permission Engine to gain authority

## 12. Dedicated Browser Environment

Use a dedicated experimental browser profile/session.

Do not automatically expose the user's normal personal browser profile.

The experimental browser should have separate:
- cookies
- local storage
- session state
- downloads
- history
- cache
- authentication state

## 13. Browser Credentials

Do not automatically expose:
- passwords
- API keys
- authentication tokens
- private cookies
- password-manager data
- personal account credentials

The existence of a browser session must not allow credential extraction.

## 14. Research Evidence

Every meaningful research action should be observable by the Evidence Plane.

Record:

```text
agent_id
session_id
timestamp
action
query
URL
page_title
source
action_result
extracted_claim
evidence
confidence
verification_status
```

Agents must not be able to claim evidence without an associated source record.

## 15. External Information and Memory

> External information must never silently become trusted memory.

Recommended flow:

```text
Browser
  |
Evidence
  |
Evaluation
  |
Verification when appropriate
  |
Memory
```

Unverified information must remain distinguishable from verified knowledge.

## 16. Source Tracking

Preserve:
- URL
- title
- domain
- timestamp
- agent
- query/path leading to source

Where practical:
- author
- publication date
- document identifier
- source type
- relevant section
- evidence reference
- verification status

## 17. Multi-Agent Research

Atlas and Argus may browse independently.

They may:
- research different aspects
- use different sources
- challenge findings
- verify claims
- discover contradictions
- combine findings
- abandon hypotheses

Example:

```text
Atlas: "I found evidence supporting X."
Argus: "I will independently verify it."
Argus -> Browser -> different sources
Argus: "Source B contradicts X."
Atlas: "Then the hypothesis needs revision."
```

Preserve this interaction in Evidence and Memory.

## 18. Browser Context Management

Do not place the complete browser history into every model request.

Retrieve only relevant information:
- current page
- current action
- relevant extracted text
- recent browser actions
- research objective
- relevant previous sources
- important evidence
- open questions

Older activity should be summarized and stored.

## 19. Browser Loop Prevention

Detect repetitive patterns such as:

```text
Search A
Open B
Back
Search A
Open B
Back
...
```

or repeated failed actions.

Record repetition. The system may:
- inform the agent
- request a new strategy
- pause the action loop
- apply a configurable action budget

Do not silently alter the agent's reasoning.

## 20. Resource Management

Monitor:
- browser memory
- number of tabs
- page memory
- downloads
- CPU
- RAM
- model inference
- context size
- screenshot frequency
- browser processes

Configurable controls may include:
- maximum tabs
- maximum concurrent browser sessions
- screenshot frequency
- download size
- browser memory
- tool calls per time window

These are resource controls, not cognitive restrictions.

## 21. M4 16 GB Optimization

Prioritize:
- DOM/accessibility/text over screenshots
- minimal browser processes
- controlled tab count
- closing unused tabs
- bounded downloads
- bounded context
- asynchronous tool execution
- caching useful page information
- avoiding duplicate retrieval
- monitoring memory pressure

If memory pressure rises:

```text
Resource Manager
      |
Detect pressure
      |
Reduce browser workload
      |
Notify agents
      |
Continue when resources recover
```

## 22. Browser Errors

Distinguish:

```text
NAVIGATION_ERROR
TIMEOUT
PAGE_LOAD_ERROR
ELEMENT_NOT_FOUND
ACTION_FAILED
NETWORK_ERROR
DOWNLOAD_ERROR
PERMISSION_DENIED
RESOURCE_LIMIT
BROWSER_CRASH
```

Provide structured errors rather than arbitrary raw exceptions.

Allow agents to attempt reasonable recovery while recording failures.

## 23. Master Observation

Master Control should expose:
- browser sessions
- active tabs
- current URLs
- page titles
- recent actions
- pending permissions
- downloads
- research evidence
- browser errors
- resource consumption

The default remains:

> Observe first. Intervene when necessary.

## 24. Master Intervention

The Master may interrupt browser activity:

```text
stop atlas
interrupt atlas
close-browser atlas
deny <request>
stop-all
```

Emergency stop must not depend on agent cooperation.

## 25. Evidence Events

Suggested event types:

```text
BROWSER_SESSION_CREATED
BROWSER_SESSION_CLOSED
PAGE_OPENED
PAGE_NAVIGATED
PAGE_RELOADED
PAGE_READ
TAB_OPENED
TAB_SWITCHED
TAB_CLOSED
SEARCH_PERFORMED
LINK_FOLLOWED
CLICK_PERFORMED
TEXT_ENTERED
SCROLL_PERFORMED
SCREENSHOT_CAPTURED
DOWNLOAD_REQUESTED
DOWNLOAD_COMPLETED
DOWNLOAD_BLOCKED
PERMISSION_REQUESTED
PERMISSION_GRANTED
PERMISSION_DENIED
BROWSER_ERROR
BROWSER_RECOVERY
RESEARCH_CLAIM_CREATED
RESEARCH_CLAIM_VERIFIED
RESEARCH_CLAIM_DISPUTED
```

## 26. SQLite Integration

Suggested tables:

```text
browser_sessions
browser_tabs
browser_actions
browser_sources
browser_claims
browser_downloads
browser_permissions
browser_errors
```

Reference:
- session_id
- agent_id
- event_id

This must make browser activity reconstructable.

## 27. Research Reproducibility

A report should be able to answer:

> How did the agent reach this conclusion?

Reconstruct:

```text
Objective
   |
Initial hypothesis
   |
Search
   |
Source A
   |
Source B
   |
Contradiction
   |
Additional search
   |
Experiment
   |
Result
   |
Revised hypothesis
   |
Conclusion
```

## 28. Novelty

Browsing does not guarantee novel research.

Agents may:
- rediscover existing work
- misunderstand sources
- produce false conclusions
- enter loops
- find useful information
- combine known techniques
- generate potentially novel hypotheses

Claims of novelty require evidence and prior-art/literature verification.

## 29. Browser as Experimental Environment

The desired autonomous loop is:

```text
QUESTION
   |
HYPOTHESIS
   |
SEARCH
   |
READ
   |
FOLLOW LEADS
   |
COMPARE
   |
CHALLENGE
   |
EXPERIMENT
   |
RESULT
   |
REVISE
   |
SEARCH AGAIN
   |
NEW QUESTION
```

Agents may continue this loop autonomously.

## 30. Security Boundary

> Full browser control does not equal unrestricted system authority.

Browser control must not bypass:
- Master authority
- Permission Engine
- Tool Gateway
- protected filesystem boundaries
- security policies
- emergency stop
- evidence requirements

## 31. Implementation Rule

When implementing:
1. Inspect the existing architecture first.
2. Reuse Tool Gateway.
3. Reuse Permission Engine.
4. Reuse Evidence Plane.
5. Reuse Context Manager.
6. Reuse Resource Manager.
7. Reuse SQLite.
8. Do not duplicate these systems.
9. Do not weaken Master protections.
10. Document implementation decisions.
11. Add tests for every new browser capability.
12. Update implementation documentation after completion.

## 32. Acceptance Criteria

The browser subsystem is complete when:
- Agents independently decide when to browse.
- Agents navigate browser sessions.
- Agents search and read public information.
- Agents interact with supported page actions.
- Agents use DOM/accessibility information.
- Screenshots are available when visual understanding is required.
- Browser actions pass through Tool Gateway.
- Permissions are enforced.
- Research activity is recorded.
- Sources are associated with evidence.
- Browser history is not blindly injected into context.
- Browser loops can be detected.
- Resource usage is monitored.
- Master intervention works.
- Emergency stop works.
- Browser activity can be reconstructed from SQLite/evidence.
- Browser credentials are not silently exposed.
- Master Control remains immutable.
- Browser control does not grant additional system authority.

## 33. Final Design Principle

```text
                    AGENT
                      |
              "What should I do?"
                      |
                      v
                BROWSER MANAGER
                      |
              "What can I do?"
                      |
                      v
               PERMISSION ENGINE
                      |
              "Is this allowed?"
                 /                       ALLOW       APPROVAL
                |             |
                v             v
             BROWSER        MASTER
                |
                v
             OBSERVE
                |
        +-------+-------+
        |               |
        v               v
     MEMORY          EVIDENCE
        |               |
        +-------+-------+
                |
                v
              AGENT
                |
                v
          Next decision
```

The browser becomes an autonomous environment through which agents can investigate, learn, verify, experiment, and adapt while the system independently maintains permissions, evidence, resource control, and Master authority.
