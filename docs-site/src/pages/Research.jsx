import React from 'react';
import CodeBlock from '../components/CodeBlock';
import './Research.css';

export default function Research() {
    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">Research Notes</h1>
                <p className="page-subtitle">
                    Multi-agent emergence and tool use
                </p>
            </div>

            <section className="content-section">
                <h2 className="section-title">Research Motivation</h2>
                <p className="section-subtitle">
                    Current AI research predominantly evaluates models on static benchmarks
                    with single-agent, turn-based interactions. Yet real intelligence —
                    biological and artificial — emerges from dynamic, multi-agent environments
                    where participants communicate, collaborate, use tools, and challenge each
                    other's reasoning.
                </p>
                <p className="section-subtitle">
                    AI Sandbox was built to fill this gap. It provides a controlled, observable
                    environment where researchers can study how agents with different roles and
                    personalities develop emergent strategies when given access to real tools,
                    persistent memory, and the ability to influence each other through dialogue.
                </p>
            </section>

            <section className="content-section">
                <h2 className="section-title">Key Research Questions</h2>
                <div className="research-questions">
                    <div className="question-card">
                        <div className="question-number">1</div>
                        <div className="question-content">
                            <h3 className="question-title">
                                Emergent Strategies with Tool Access
                            </h3>
                            <p className="question-desc">
                                How do agents develop emergent strategies when given tool access?
                                Do agents learn to combine tools in unexpected ways? Do they
                                develop tool-use heuristics that weren't explicitly programmed?
                            </p>
                        </div>
                    </div>
                    <div className="question-card">
                        <div className="question-number">2</div>
                        <div className="question-content">
                            <h3 className="question-title">
                                Communication Patterns Between Roles
                            </h3>
                            <p className="question-desc">
                                What communication patterns emerge between agents with different
                                roles? Do explorers and challengers develop complementary
                                conversational strategies? How does role assignment affect
                                information flow?
                            </p>
                        </div>
                    </div>
                    <div className="question-card">
                        <div className="question-number">3</div>
                        <div className="question-content">
                            <h3 className="question-title">
                                Tool Use and Reasoning
                            </h3>
                            <p className="question-desc">
                                How does tool use affect agent reasoning and collaboration? Do
                                agents with tool access produce different argument structures than
                                those without? Does access to evidence change confidence
                                calibration?
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">System Design Decisions</h2>
                <p className="section-subtitle">
                    Key architectural choices and their rationale for research purposes.
                </p>
                <div className="design-decisions">
                    <div className="decision-card">
                        <h3 className="decision-title">Local-First Architecture</h3>
                        <p className="decision-desc">
                            All inference runs locally via Ollama. This eliminates API costs,
                            enables reproducible experiments, removes network variability, and
                            allows unlimited conversation length within hardware constraints.
                        </p>
                    </div>
                    <div className="decision-card">
                        <h3 className="decision-title">Role-Based Agents</h3>
                        <p className="decision-desc">
                            Agents are assigned distinct roles (explorer, challenger) with
                            different system prompts and tool access. This creates observable
                            dynamics rather than symmetric, featureless interactions.
                        </p>
                    </div>
                    <div className="decision-card">
                        <h3 className="decision-title">Full Tool Transparency</h3>
                        <p className="decision-desc">
                            Every tool call is logged with full input/output. This provides
                            complete observability into how agents use tools, what they choose
                            to investigate, and how tool results shape their reasoning.
                        </p>
                    </div>
                    <div className="decision-card">
                        <h3 className="decision-title">Event-Driven Architecture</h3>
                        <p className="decision-desc">
                            All components communicate through a typed event bus. This decouples
                            components, enables clean instrumentation, and makes it trivial to
                            add new observers without modifying core logic.
                        </p>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Experimental Setup</h2>
                <p className="section-subtitle">
                    Guidelines for setting up reproducible experiments.
                </p>
                <CodeBlock title="config.json — Research Setup">
                    {`{
  "model": "qwen2.5-coder:7b",
  "temperature": 0.7,
  "agents": {
    "atlas": {
      "role": "explorer",
      "tools": ["terminal", "read_file", "web_fetch"],
      "temperature": 0.7
    },
    "argus": {
      "role": "challenger",
      "tools": ["read_file", "web_fetch"],
      "temperature": 0.7
    }
  },
  "max_turns": 100,
  "memory": {
    "short_term_window": 30,
    "long_term_enabled": true,
    "summary_interval": 15
  },
  "logging": {
    "record_tool_calls": true,
    "record_reasoning": true,
    "export_format": "jsonl"
  }
}`}
                </CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">Suggested Experiments</h2>
                <div className="experiments-list">
                    <div className="experiment-card">
                        <h3 className="experiment-title">Temperature Effects</h3>
                        <p className="experiment-desc">
                            Vary temperature from 0.1 to 1.0 across runs. Measure how creativity,
                            coherence, and tool-use patterns change. Higher temperatures may
                            produce more novel tool combinations but less coherent long-term
                            strategies.
                        </p>
                        <CodeBlock title="Shell">
                            {`# Run at different temperatures
for temp in 0.1 0.3 0.5 0.7 0.9; do
    python -m app start --temperature $temp --output results/temp_$temp.jsonl
done`}
                        </CodeBlock>
                    </div>

                    <div className="experiment-card">
                        <h3 className="experiment-title">Agent Role Variations</h3>
                        <p className="experiment-desc">
                            Test different agent role combinations. Compare two explorers vs.
                            explorer+challenger vs. three agents with distinct specializations.
                            Observe how role diversity affects conversation quality and depth.
                        </p>
                    </div>

                    <div className="experiment-card">
                        <h3 className="experiment-title">Tool Availability Impact</h3>
                        <p className="experiment-desc">
                            Run the same topic with different tool configurations. Measure how
                            the absence of specific tools (web, terminal, filesystem) changes
                            agent reasoning and conclusion quality.
                        </p>
                        <CodeBlock title="Shell">
                            {`# Tool availability matrix
# Run 1: All tools enabled
python -m app start --tools all --output results/all_tools.jsonl

# Run 2: Filesystem only
python -m app start --tools read_file --output results/fs_only.jsonl

# Run 3: No tools (baseline)
python -m app start --tools none --output results/no_tools.jsonl`}
                        </CodeBlock>
                    </div>

                    <div className="experiment-card">
                        <h3 className="experiment-title">Conversation Length Effects</h3>
                        <p className="experiment-desc">
                            Run conversations from 10 to 200 turns. Track how topic coverage,
                            depth of analysis, memory utilization, and emergent behaviors
                            evolve over time. Look for phase transitions where new strategies
                            appear.
                        </p>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Data Collection &amp; Analysis</h2>
                <p className="section-subtitle">
                    The system automatically exports structured data for analysis.
                </p>
                <CodeBlock title="Python — Analysis">
                    {`import json
import pandas as pd

# Load conversation export
with open("results/experiment_1.jsonl") as f:
    events = [json.loads(line) for line in f]

# Analyze tool usage patterns
tool_calls = [e for e in events if e["type"] == "tool_call"]
tool_freq = pd.Series([tc["tool"] for tc in tool_calls]).value_counts()

# Measure conversation dynamics
messages = [e for e in events if e["type"] == "message"]
turn_lengths = [len(m["content"].split()) for m in messages]

# Track agent interaction patterns
agent_msgs = pd.Series([m["agent"] for m in messages])
alternation_rate = (agent_msgs.diff() != 0).mean()`}
                </CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">Related Work</h2>
                <div className="references-list">
                    <div className="reference-item">
                        <span className="ref-authors">Park et al. (2023)</span>
                        <span className="ref-title">
                            "Generative Agents: Interactive Simulacra of Human Behavior"
                        </span>
                        <span className="ref-venue">UIST 2023</span>
                    </div>
                    <div className="reference-item">
                        <span className="ref-authors">Hong et al. (2023)</span>
                        <span className="ref-title">
                            "MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework"
                        </span>
                        <span className="ref-venue">arXiv 2308.00352</span>
                    </div>
                    <div className="reference-item">
                        <span className="ref-authors">Wu et al. (2023)</span>
                        <span className="ref-title">
                            "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation"
                        </span>
                        <span className="ref-venue">arXiv 2308.08155</span>
                    </div>
                    <div className="reference-item">
                        <span className="ref-authors">Shinn et al. (2023)</span>
                        <span className="ref-title">
                            "Reflexion: Language Agents with Verbal Reinforcement Learning"
                        </span>
                        <span className="ref-venue">NeurIPS 2023</span>
                    </div>
                    <div className="reference-item">
                        <span className="ref-authors">Yao et al. (2023)</span>
                        <span className="ref-title">
                            "ReAct: Synergizing Reasoning and Acting in Language Models"
                        </span>
                        <span className="ref-venue">ICLR 2023</span>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Citation</h2>
                <CodeBlock title="BibTeX">
                    {`@software{ai_sandbox_2024,
  title  = {AI Sandbox: Autonomous Multi-Agent AI Laboratory},
  author = {Your Name},
  year   = {2024},
  url    = {https://github.com/your-org/ai-sandbox},
  note   = {Multi-agent emergence and tool use research platform}
}`}
                </CodeBlock>
            </section>
        </div>
    );
}
