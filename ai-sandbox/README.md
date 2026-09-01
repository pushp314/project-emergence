<div align="center">

# 🌌 Project Emergence (AI Sandbox)
### Production-Grade Autonomous Agentic OS

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Next.js](https://img.shields.io/badge/Next.js-16.3-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-00a393)](https://fastapi.tiangolo.com/)

*Project Emergence* is a deeply integrated, 24/7 autonomous operating environment. It transforms your machine into an intelligent hub where hierarchical AI agents delegate tasks, execute code, maintain persistent semantic memories, and collaborate endlessly.

[Features](#-key-features) • [Architecture](#-system-architecture) • [Quick Start](#-quick-start-guide) • [Deep Dive Usage](#-deep-dive-usage)

</div>

---

## 🚀 Key Features

<table>
<tr>
<td width="50%">

### 🧠 Agent-to-Agent (A2A) Orchestration
- **Hierarchical Swarm**: A "Manager CEO" delegates tasks autonomously to specialized sub-agents (Explorers, QA, Observers).
- **24/7 Daemon**: Agents run autonomously in the background, continually researching, monitoring, or executing long-running builds.

</td>
<td width="50%">

### 🛡️ Enterprise Security & Tooling
- **Approval Pipeline**: High-risk commands (`rm`, `sudo`) are intercepted; execution is frozen until Human Approval via UI.
- **Deep System Access**: Agents have access to terminal, filesystem, and active window management.

</td>
</tr>
<tr>
<td width="50%">

### 💾 Persistent Vector Brain (RAG)
- **Semantic Memory**: Conversations, learned rules, and OS context are embedded directly into a local ChromaDB store.
- **Memory Explorer UI**: Audit, search, and curate the exact facts your AI has memorized over time.

</td>
<td width="50%">

### 📊 Live Telemetry Dashboard
- **Hardware Integration**: Real-time WebSocket streaming of CPU, RAM, and Disk I/O.
- **Mission Analytics**: Track success rates, token usage, and database growth natively.

</td>
</tr>
</table>

---

## 🏗️ System Architecture

Github seamlessly renders this architecture flow:

```mermaid
graph TD
    subgraph Frontend [Command Center (Next.js)]
        UI[Enterprise Chat UI]
        Dashboard[Live Telemetry Dashboard]
        MemExp[Vector Brain Explorer]
    end

    subgraph Backend [Emergence Engine (FastAPI)]
        CE[Conversation Engine]
        A2A[A2A Protocol Router]
        TE[Tool Gateway]
        
        subgraph Agents
            M[Manager Agent]
            E[Explorer Agent]
            O[Observer Agent]
        end
    end

    subgraph Persistence Layer
        SQL[(SQLite Timeline)]
        VDB[(ChromaDB Vectors)]
    end

    UI <-->|REST / WebSockets| CE
    Dashboard <-->|Live System Stats| Backend
    MemExp <-->|CRUD Memories| VDB

    CE --> A2A
    A2A --> M
    M -->|Delegates| E
    M -->|Delegates| O
    
    E <--> TE
    O <--> TE

    TE -->|Terminal / Filesystem| OS[Local Operating System]
    
    CE --> SQL
    O -->|Summarizes into| VDB
```

---

## ⚡ Quick Start Guide

### 1. Requirements
- Python 3.10+
- Node.js 18+ (npm or pnpm)
- *(Optional but recommended)* [Ollama](https://ollama.ai) for 100% private, local inference.

### 2. Backend Initialization
```bash
git clone https://github.com/pushp314/project-emergence.git
cd project-emergence

# Create isolated environment
python3 -m venv venv
source venv/bin/activate

# Install Core Engine dependencies
pip install -r requirements.txt

# Export your LLM Provider Keys
export GEMINI_API_KEY="your_api_key_here"
export OPENROUTER_API_KEY="your_api_key_here"

# Boot the Emergence Engine
PYTHONPATH=. python3 -m app.main api --port 8001
```

### 3. Frontend Initialization
```bash
# In a new terminal tab
cd project-emergence/web-ui

# Install Next.js dependencies
npm install

# Launch the Command Center
npm run dev
```
Navigate to **`http://localhost:3000`** in your browser.

---

## 📖 Deep Dive Usage

<details>
<summary><b>1. Multi-Chat CRUD (Managing Sessions)</b></summary>
<br>
In the left sidebar under <b>History</b>, you can spawn infinite parallel sessions. 
Each session initializes a clean state machine in the backend. 
<ul>
<li>Click the <code>+</code> button to create a new session.</li>
<li>Hover over a session and click <code>×</code> to permanently delete it.</li>
<li>Switch between sessions instantly without dropping background daemon tasks.</li>
</ul>
</details>

<details>
<summary><b>2. The Vector Brain Explorer</b></summary>
<br>
The AI remembers everything you teach it across all sessions.
<ul>
<li>Navigate to the <b>Intelligence > Vector Brain</b> tab.</li>
<li>You will see a searchable semantic database of every rule, code snippet, or instruction the AI has committed to long-term memory.</li>
<li><b>Self-Correction:</b> If the AI learns something wrong, simply find the memory here and click <b>Delete</b>.</li>
</ul>
</details>

<details>
<summary><b>3. Live Telemetry & Diagnostics</b></summary>
<br>
Keep an eye on what your autonomous background tasks are doing to your machine.
<ul>
<li>Navigate to <b>Intelligence > Analytics</b>.</li>
<li>Watch live WebSocket feeds of your actual CPU and RAM utilization.</li>
<li>Monitor how fast your SQLite timeline and Vector Store are growing.</li>
</ul>
</details>

<details>
<summary><b>4. Customizing Agents & Models (config.yaml)</b></summary>
<br>
You can route different tasks to different models dynamically. Open <code>config.yaml</code> to configure fallbacks.

```yaml
model:
  routes:
    default:
      provider: gemini
      name: "gemini-3.1-flash-lite-preview"
    local_ollama:
      provider: ollama
      name: "qwen2.5-coder:7b"
      host: "http://127.0.0.1:11434"
```
If Gemini goes down, the system will automatically seamlessly failover to your local Ollama instance without crashing the mission.
</details>

---

## 🛡️ Security Posture

> [!WARNING]  
> **Unrestricted Tooling:** By default, Project Emergence has access to read and write to your local filesystem and execute arbitrary bash commands. 

To mitigate risks:
1. Ensure `autonomy.enabled` is set to `False` in your `config.yaml` if you want a purely interactive chat experience.
2. The UI features a hardcoded **Approval Interceptor** for commands containing `sudo`, `rm -rf`, or heavy file deletions. Do not disable this in the backend router unless you fully trust the active agent model.

---

<div align="center">
<i>Engineered for the edge of autonomous computing.</i>
</div>
