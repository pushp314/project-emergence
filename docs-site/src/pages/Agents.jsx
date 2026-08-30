import React from 'react';
import CodeBlock from '../components/CodeBlock';

export default function Agents() {
    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">Agents</h1>
                <p className="page-subtitle">
                    Autonomous AI agents with tool access and distinct personalities
                </p>
            </div>

            <section className="doc-section">
                <h2>Atlas — The Explorer</h2>
                <p>
                    Atlas is the <strong>explorer agent</strong>. Its role is to investigate, research,
                    generate hypotheses, and propose directions. Atlas approaches problems with curiosity —
                    it wants to understand how things work, what possibilities exist, and where the most
                    interesting questions lie.
                </p>

                <h3>Capabilities</h3>
                <ul>
                    <li>Broad exploration and hypothesis generation</li>
                    <li>Web research via the <code>web</code> tool</li>
                    <li>Code and filesystem inspection via <code>terminal</code> and <code>filesystem</code></li>
                    <li>Proposes experiments and directions</li>
                    <li>Builds on what Argus says and responds to challenges</li>
                </ul>

                <h3>System Prompt Design</h3>
                <p>
                    Atlas's system prompt establishes it as a curious, tool-using explorer. The key design
                    principles are:
                </p>
                <ul>
                    <li>Explicit tool definitions with usage format</li>
                    <li>Rules that encourage engagement and specificity</li>
                    <li>A collaborative framing with Argus — they are partners, not opponents</li>
                    <li>Minimum response length to prevent terse, unhelpful replies</li>
                </ul>

                <CodeBlock title="Atlas system prompt" language="text">
{`You are Atlas, an autonomous AI explorer with access to tools.

TOOLS AVAILABLE:
- terminal: Run shell commands. Format: [TOOL:terminal:{"command": "your command"}]
- filesystem: Read/write files. Format: [TOOL:filesystem:{"operation": "read", "path": "file.py"}]
- web: Fetch web pages. Format: [TOOL:web:{"url": "https://example.com"}]

RULES:
- Use tools when you need to explore code, check files, run code, or research online
- You can use multiple tools in one response
- Always explain what you're doing before and after using a tool
- Respond in 2-4 sentences minimum
- Be curious, specific, and engaged
- Build on what Argus says

You and Argus are collaborators discovering insights together.`}
                </CodeBlock>

                <h3>Tool Usage Format</h3>
                <p>
                    Agents emit tool calls inline in their response text using a structured bracket format.
                    The conversation engine parses these and executes them via the event bus.
                </p>

                <CodeBlock title="Tool call format" language="text">
{`[TOOL:<tool_name>:<json_arguments>]`}
                </CodeBlock>

                <h3>Tool Call Examples</h3>

                <CodeBlock title="Terminal — run a shell command" language="text">
{`[TOOL:terminal:{"command": "ls -la src/"}]`}
                </CodeBlock>

                <CodeBlock title="Filesystem — read a file" language="text">
{`[TOOL:filesystem:{"operation": "read", "path": "src/main.py"}]`}
                </CodeBlock>

                <CodeBlock title="Web — fetch a page" language="text">
{`[TOOL:web:{"url": "https://docs.python.org/3/library/asyncio.html"}]`}
                </CodeBlock>

                <h3>Response Format</h3>
                <p>
                    After tool execution, results are injected back into the conversation as
                    <code>[tool_name result: ...]</code> or <code>[tool_name error: ...]</code> markers.
                    The agent then generates a follow-up response incorporating the results.
                </p>

                <CodeBlock title="Full agent response with tool usage" language="text">
{`Let me check what files are in the source directory to understand the project structure.

[TOOL:terminal:{"command": "find src/ -name '*.py' | head -20"}]

[terminal result: src/main.py
src/agents/base.py
src/agents/explorer.py
src/agents/challenger.py
src/orchestration/conversation.py]

I can see the project has a clean modular structure. The agents are separated into base,
explorer, and challenger modules. Let me look at the base agent to understand the core interface.`}
                </CodeBlock>
            </section>

            <section className="doc-section">
                <h2>Argus — The Challenger</h2>
                <p>
                    Argus is the <strong>challenger agent</strong>. Its role is to critically evaluate
                    what Atlas proposes — questioning assumptions, verifying claims, identifying gaps,
                    and suggesting alternatives. Argus is not adversarial for its own sake; it sharpens
                    the conversation by demanding rigor.
                </p>

                <h3>Capabilities</h3>
                <ul>
                    <li>Critical evaluation and assumption testing</li>
                    <li>Claim verification via tools (terminal, filesystem, web)</li>
                    <li>Deep reasoning and analysis</li>
                    <li>Identifies logical gaps and weak methodology</li>
                    <li>Offers alternative perspectives</li>
                </ul>

                <h3>How Argus Challenges</h3>
                <p>
                    Argus responds directly to what Atlas said — referencing specific points, asking
                    follow-up questions, and pointing out where reasoning is weak. It uses tools
                    to <em>verify</em> claims rather than accepting them at face value.
                </p>

                <CodeBlock title="Argus system prompt" language="text">
{`You are Argus, an autonomous AI challenger with access to tools.

TOOLS AVAILABLE:
- terminal: Run shell commands. Format: [TOOL:terminal:{"command": "your command"}]
- filesystem: Read/write files. Format: [TOOL:filesystem:{"operation": "read", "path": "file.py"}]
- web: Fetch web pages. Format: [TOOL:web:{"url": "https://example.com"}]

RULES:
- Use tools to verify claims, check code, or research facts
- Respond specifically to what Atlas said — reference their points directly
- Ask follow-up questions, point out gaps, offer alternatives
- Aim for 2-4 sentences minimum
- Be sharp, specific, and intellectually honest

You and Atlas are collaborators discovering insights together.`}
                </CodeBlock>

                <h3>Verification with Tools</h3>
                <p>
                    When Atlas makes a claim, Argus can use tools to independently verify it. For
                    example, if Atlas says "the file has 200 lines," Argus can read the file and
                    check.
                </p>

                <CodeBlock title="Argus verifying a claim" language="text">
{`That's an interesting observation about the memory layout, but let me verify — you mentioned
the context window is 8192 tokens. Let me check the actual configuration.

[TOOL:filesystem:{"operation": "read", "path": "app/memory/context_manager.py"}]

[filesystem result: @dataclass
class ContextBudget:
    max_context_tokens: int = 8192
    ...]

Confirmed — the default is indeed 8192. However, this gets reduced under resource pressure.
At YELLOW state it drops to 85% (6963), and at ORANGE to 70% (5734). This is a significant
constraint you didn't mention.`}
                </CodeBlock>
            </section>

            <section className="doc-section">
                <h2>Agent Interaction</h2>
                <p>
                    Atlas and Argus communicate through a shared conversation managed by the
                    Conversation Engine. Each agent sees the other's messages with an identity
                    prefix — <code>[atlas]</code> or <code>[argus]</code> — and responds to the
                    full context.
                </p>

                <h3>How It Works</h3>
                <ul>
                    <li>The <strong>Scheduler</strong> determines who speaks next (round-robin by default)</li>
                    <li>The current speaker's agent receives the recent conversation history as context</li>
                    <li>The agent generates a response, optionally including tool calls</li>
                    <li>The response is appended to the message history</li>
                    <li>The cycle repeats</li>
                </ul>

                <h3>Delegation</h3>
                <p>
                    Agents can delegate tasks to each other. A delegation request specifies the
                    receiver, capability needed, objective, and context. The receiving agent
                    evaluates the request and responds with acceptance and results.
                </p>

                <CodeBlock title="Delegation request event" language="json">
{`{
  "type": "agent.delegation",
  "speaker": "atlas",
  "payload": {
    "receiver": "argus",
    "capability": "security_audit",
    "objective": "Review the network scanning code for vulnerabilities",
    "context": "We're building a network scanner. Need security review.",
    "reason": "Security expertise needed",
    "expected_output": "List of vulnerabilities with severity ratings",
    "priority": "high"
  }
}`}
                </CodeBlock>

                <h3>Emergent Behaviors</h3>
                <p>
                    Because agents are autonomous, their relationships emerge from interaction.
                    The system observes and records behaviors like specialization, cooperation,
                    competition, trust, disagreement, and strategy evolution — without prescribing them.
                </p>
            </section>

            <section className="doc-section">
                <h2>Tool Format Reference</h2>
                <p>
                    All tool calls use the same bracket format. Here is a complete reference
                    of each tool type and its arguments.
                </p>

                <h3>Terminal</h3>
                <p>Executes shell commands on the host system.</p>
                <CodeBlock title="Terminal tool" language="text">
{`[TOOL:terminal:{"command": "<shell command>"}]`}
                </CodeBlock>

                <h3>Filesystem</h3>
                <p>Reads or writes files. Supports read, write, list, and search operations.</p>
                <CodeBlock title="Filesystem — read" language="text">
{`[TOOL:filesystem:{"operation": "read", "path": "path/to/file.py"}]`}
                </CodeBlock>
                <CodeBlock title="Filesystem — write" language="text">
{`[TOOL:filesystem:{"operation": "write", "path": "output.txt", "content": "file content here"}]`}
                </CodeBlock>

                <h3>Web</h3>
                <p>Fetches content from URLs for research and verification.</p>
                <CodeBlock title="Web tool" language="text">
{`[TOOL:web:{"url": "https://example.com/page"}]`}
                </CodeBlock>
            </section>
        </div>
    );
}
