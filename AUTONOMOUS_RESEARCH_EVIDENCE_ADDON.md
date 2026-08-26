# AUTONOMOUS AI SANDBOX — RESEARCH, BROWSER & EVIDENCE ADDON

## STATUS

MANDATORY ARCHITECTURE ADDON

This document extends the main Autonomous AI Sandbox architecture.

The implementation agent MUST read and follow both:

1. The main architecture specification
2. This addon specification

Do NOT treat this document as optional.

The existing architecture must remain intact unless a change is explicitly required by this addon.

---

# 1. PURPOSE

The system is not only an AI conversation system.

It is an autonomous local AI experimentation environment.

Agents must be capable of:

- talking continuously
- researching independently
- using the browser
- using available tools
- creating files and experiments
- analyzing results
- requesting human permissions
- discovering new directions
- documenting their activities
- producing verifiable evidence

The human should be able to observe the entire process without needing to save hours of audio.

Therefore:

THE SYSTEM MUST RECORD WHAT HAPPENS AS STRUCTURED DIGITAL EVIDENCE.

Audio is only an interface.

The event/evidence system is the permanent record.

---

# 2. EXPERIMENT SESSION

Every execution of the system MUST create an Experiment Session.

Example:

Session #001

The session must have:

- unique session ID
- start timestamp
- end timestamp
- participating agents
- model configuration
- system configuration
- available tools
- permission configuration
- resource configuration
- conversation history
- decisions
- tool calls
- browser research
- experiments
- artifacts
- results
- discoveries
- errors
- interruptions
- final report

Example:

sessions/
└── session_001/
    ├── session.json
    ├── conversation.jsonl
    ├── events.jsonl
    ├── decisions.jsonl
    ├── permissions.jsonl
    ├── research.jsonl
    ├── experiments/
    ├── artifacts/
    ├── evidence/
    └── final_report.md

Sessions MUST be independently recoverable.

---

# 3. EVENT BUS AS THE SOURCE OF TRUTH

The Event Bus is the central event stream.

Every meaningful system action MUST generate an event.

Examples:

agent.message
agent.thinking_started
agent.response_completed

human.message
human.interruption

tool.request
tool.started
tool.completed
tool.failed

browser.search
browser.page_opened
browser.content_extracted

permission.requested
permission.approved
permission.denied

memory.updated

experiment.started
experiment.completed
experiment.failed

evidence.created

observer.intervention

resource.warning

system.pause
system.resume
system.stop

The Event Bus MUST NOT depend on the agents for logging.

The infrastructure observes the agents independently.

---

# 4. EVIDENCE PLANE

Create a dedicated Evidence Plane.

The Evidence Plane consumes events from the Event Bus.

Architecture:

Everything that happens
        ↓
     Event Bus
        ↓
 ┌──────┴────────┐
 ↓               ↓
Memory       Evidence Logger
                 ↓
        Research Record
                 ↓
             Artifacts

Agents MUST NOT be responsible for proving their own actions.

The system itself must record them.

---

# 5. ACTION RECORD

Every meaningful agent action should produce a structured record.

Example:

{
  "session_id": "...",
  "event_id": "...",
  "timestamp": "...",
  "agent": "agent_a",
  "action_type": "tool_request",

  "intent": "Investigate distributed inference",

  "reason": "The current discussion suggests that distributed inference may reduce local hardware limitations.",

  "tool": "browser_search",

  "input": {
    "query": "distributed inference small GPU LLM"
  },

  "permission": "not_required",

  "result": "...",

  "evidence": [],

  "next_decision": "Compare available approaches."
}

The exact schema may evolve during implementation, but the semantic information MUST be preserved.

---

# 6. BROWSER / RESEARCH SYSTEM

Browser access is a first-class tool.

Agents may independently decide that they need external information.

Example:

Agent A:

"I need to research current approaches to distributed inference."

The agent can request:

browser_search

The browser system may then:

1. search
2. open relevant pages
3. extract content
4. return relevant information
5. provide source references
6. store research evidence
7. return the result to the requesting agent

The browser MUST NOT simply return information without recording the research action.

---

# 7. BROWSER EVIDENCE

For every meaningful research action, record:

- session ID
- agent
- timestamp
- search query
- URL
- page title
- source
- extracted information
- relevant claims
- reason for research
- conclusion derived by agent
- verification status
- other agent's response/challenge if applicable

Example:

Research:

Question:
"What are current approaches to distributed LLM inference?"

Search:
"distributed inference LLM memory bandwidth"

Sources:
- Source A
- Source B
- Source C

Agent A conclusion:
"..."

Agent B challenge:
"..."

Verification:
"..."

---

# 8. SOURCE TRACEABILITY

External information MUST NEVER silently become system knowledge.

Every externally obtained claim should maintain provenance.

Use the following conceptual chain:

SOURCE
  ↓
EXTRACTED INFORMATION
  ↓
CLAIM
  ↓
AGENT INTERPRETATION
  ↓
VERIFICATION
  ↓
MEMORY

The system should be able to answer:

"Where did this information come from?"

and provide:

- source
- URL
- timestamp
- extracting agent
- original claim
- verification status

---

# 9. MEMORY + EVIDENCE

Memory and evidence are different systems.

Evidence:

"What actually happened?"

Memory:

"What should the agents remember?"

Do NOT merge them into one database concept.

Example:

Evidence:

Agent A searched:
"Mac M4 unified memory inference"

Memory:

"Agent A discovered that memory bandwidth may be a bottleneck for local inference."

The evidence must remain available even if the memory is later summarized.

---

# 10. RESEARCH LOOP

Agents should be able to independently enter a research loop.

Example:

Agent identifies question
        ↓
Search web
        ↓
Read sources
        ↓
Extract information
        ↓
Discuss with other agent
        ↓
Identify disagreement
        ↓
Search again
        ↓
Update hypothesis
        ↓
Experiment if useful
        ↓
Record result
        ↓
Continue conversation

This loop must NOT require a human to manually assign each research task.

The human remains available for permission requests and intervention.

---

# 11. EXPERIMENT SYSTEM

Agents may decide to conduct experiments.

An experiment MUST have:

- experiment ID
- session ID
- objective
- hypothesis
- proposed procedure
- required tools
- required permissions
- start time
- end time
- inputs
- outputs
- artifacts
- result
- conclusion

Example:

Experiment #004

Objective:
Test whether approach A reduces inference latency.

Hypothesis:
Approach A should reduce latency by approximately X.

Procedure:
...

Result:
...

Evidence:
...

Conclusion:
...

Next step:
...

---

# 12. ARTIFACT MANAGEMENT

Agents may create artifacts.

Examples:

- code
- scripts
- datasets
- reports
- screenshots
- command output
- experiment results
- research notes
- generated documents

Artifacts MUST be associated with:

- session
- agent
- timestamp
- action/experiment that created them

Example:

artifacts/
└── session_001/
    ├── experiment_001/
    │   ├── code.py
    │   ├── output.txt
    │   └── result.json
    │
    └── research_003/
        ├── sources.json
        └── notes.md

---

# 13. DECISION LOG

Important agent decisions MUST be recorded.

Record:

- what decision was made
- which agent made it
- why it was made
- evidence considered
- alternatives considered if available
- resulting action

Example:

Decision:

Agent B decided to challenge Agent A's hypothesis.

Reason:

Agent A's conclusion relied on a source that had not been independently verified.

Action:

Search for independent sources.

---

# 14. HUMAN PERMISSION SYSTEM

Agents may request capabilities they currently do not have.

The agent MUST clearly explain:

1. What it wants to do
2. Why it wants to do it
3. What tool/capability is required
4. What exactly will happen
5. Potential consequences/risk
6. Whether the permission is one-time or persistent

Example:

PERMISSION REQUEST

Agent: A

Requested action:
Install package X.

Reason:
Required to run experiment Y.

Command:
...

Impact:
Installs software on the local system.

Permission:
ALLOW ONCE / DENY

The permission decision MUST be recorded as evidence.

---

# 15. BROWSER + HUMAN PERMISSIONS

Not every browser operation needs approval.

Low-risk actions may be automatic:

- search
- read public webpages
- gather information

Higher-impact actions may request approval.

Examples:

- downloading software
- uploading files
- submitting forms
- external account actions
- purchases
- sending messages
- changing browser/system configuration

The exact permission policy should remain configurable.

---

# 16. AUTONOMY PRINCIPLE

Do not hard-code a fixed list of research topics.

Agents should be able to decide:

"What should we investigate next?"

based on:

- conversation
- discoveries
- available tools
- unresolved questions
- previous experiments
- external information

The system should provide capabilities rather than predetermined tasks.

---

# 17. OBSERVER AGENT

Agent C should monitor:

- conversation quality
- research activity
- repetition
- contradictions
- important discoveries
- unresolved questions
- experiments
- evidence quality

Agent C should remain silent most of the time.

It may intervene when intervention provides meaningful value.

It must NOT constantly consume inference resources.

Prefer event-triggered or periodic observation.

---

# 18. RESOURCE-AWARE RESEARCH

The system runs on:

Apple Silicon M4
16 GB unified memory

Resource efficiency is a PRIMARY requirement.

Research should not cause unnecessary inference load.

Avoid:

- running three large models simultaneously
- constantly running the observer
- unnecessarily large context windows
- repeatedly summarizing identical information
- loading/unloading models for every request
- unnecessary duplicate browser searches

Prefer:

- sequential inference
- streaming
- context compression
- cached research
- deduplicated searches
- event-triggered observer
- smaller model for summarization
- smaller model for lightweight classification
- strongest model only for difficult reasoning

---

# 19. RESEARCH CACHE

If an agent requests information that has already been researched recently, check the research cache first.

Example:

Agent A:
"Research distributed inference."

System checks:

Research Cache
       ↓
Matching research found
       ↓
Return existing evidence
       ↓
Avoid unnecessary browser/model work

If information is stale or insufficient, perform a new search.

---

# 20. DUPLICATE RESEARCH DETECTION

The system should detect when both agents are researching the same question.

Instead of:

Agent A → search X
Agent B → search X

prefer:

Agent A → search X
       ↓
Research cache
       ↓
Agent B receives existing evidence

This reduces:

- browser requests
- model inference
- network usage
- unnecessary work

---

# 21. FINAL SESSION REPORT

When a session ends, automatically generate:

final_report.md

Structure:

# Autonomous AI Session Report

## Session Information

## Agents

## Models

## Environment

## Initial State

## Conversation Summary

## Research Performed

## Sources

## Important Decisions

## Experiments

## Results

## Discoveries

## Failed Attempts

## Human Interventions

## Permissions

## Artifacts

## Unresolved Questions

## Final State

## Timeline

## Resource Usage

## Conclusions

The report MUST distinguish between:

FACT
OBSERVATION
AGENT CLAIM
EXTERNAL SOURCE
HYPOTHESIS
EXPERIMENTAL RESULT
CONCLUSION

Do not present speculation as fact.

---

# 22. COMPLETE TIMELINE

The system must be able to reconstruct the entire session chronologically.

Example:

09:00:00 — Session started
09:00:04 — Agent A spoke
09:00:18 — Agent B responded
09:00:43 — Agent A requested web research
09:00:44 — Browser search executed
09:01:02 — Source A opened
09:01:15 — Evidence recorded
09:01:31 — Agent B challenged claim
09:02:00 — New research requested
09:03:12 — Experiment created
09:04:02 — Permission requested
09:04:15 — Human approved
09:05:30 — Experiment completed
09:06:00 — Result recorded

This timeline is one of the most important outputs of the system.

---

# 23. AUDIO IS NOT THE PRIMARY RECORD

Do NOT design the system around storing audio.

Audio exists primarily for human interaction.

The permanent record should be:

EVENTS
+
TEXT TRANSCRIPT
+
DECISIONS
+
TOOL CALLS
+
RESEARCH
+
EVIDENCE
+
ARTIFACTS
+
EXPERIMENTS
+
RESULTS

Optional audio recording may be supported later, but it is NOT required for the core experiment.

---

# 24. AUDITABILITY REQUIREMENT

At any point, the human should be able to ask:

"What have you done?"

and the system should answer using the recorded session state.

It should be possible to trace:

Decision
 ↓
Reason
 ↓
Action
 ↓
Tool
 ↓
Result
 ↓
Evidence
 ↓
Conclusion

This traceability is mandatory.

---

# 25. IMPLEMENTATION REQUIREMENT

Before implementing this addon:

1. Read the existing architecture.
2. Identify where the Event Bus exists.
3. Integrate Evidence Logging with the Event Bus.
4. Add Experiment Sessions.
5. Add browser/research tools.
6. Add research provenance.
7. Add research caching.
8. Add experiment tracking.
9. Add artifact tracking.
10. Add decision logging.
11. Add final report generation.
12. Add timeline reconstruction.
13. Integrate resource-aware research behavior.
14. Test recovery and failure cases.

Do NOT create a completely separate application for these features.

Integrate them into the existing architecture.

---

# 26. ACCEPTANCE CRITERIA

The addon is complete only when:

- [ ] Every session has a unique ID.
- [ ] Every meaningful event is logged.
- [ ] Agent actions are independently recorded.
- [ ] Browser searches are recorded.
- [ ] URLs are recorded.
- [ ] External claims maintain source provenance.
- [ ] Decisions are recorded.
- [ ] Tool calls are recorded.
- [ ] Permission requests are recorded.
- [ ] Experiments are recorded.
- [ ] Artifacts are linked to their origin.
- [ ] Memory can be reconstructed from evidence.
- [ ] Duplicate research can be detected.
- [ ] Research can be cached.
- [ ] Human interventions are recorded.
- [ ] A complete timeline can be generated.
- [ ] A final research report can be generated.
- [ ] The system can recover an interrupted session.
- [ ] Evidence remains available after memory summarization.
- [ ] The system remains efficient on an M4 with 16 GB RAM.

---

# FINAL INSTRUCTION TO THE IMPLEMENTATION AGENT

This addon is MANDATORY.

Do not merely create placeholder logging.

Implement a real, persistent, queryable evidence system.

The objective is to make every autonomous session reproducible and auditable.

The human should be able to leave the agents running, return later, and understand:

WHAT THEY DISCUSSED
WHAT THEY RESEARCHED
WHY THEY RESEARCHED IT
WHAT THEY DID
WHAT THEY REQUESTED
WHAT THE HUMAN APPROVED
WHAT THEY EXPERIMENTED WITH
WHAT THEY DISCOVERED
WHAT EVIDENCE SUPPORTS IT
WHAT FAILED
WHAT THEY CONCLUDED
AND WHAT THEY DECIDED TO DO NEXT.

The system must optimize all of this for an Apple M4 with 16 GB unified memory.

Do not sacrifice system stability or responsiveness for unnecessary model parallelism.

Build incrementally, test each component, and preserve the existing architecture.