import React from 'react';
import CodeBlock from '../components/CodeBlock';
import './Models.css';

export default function Models() {
    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">Models</h1>
                <p className="page-subtitle">
                    Configure your local LLM for AI Sandbox
                </p>
            </div>

            <section className="content-section">
                <h2 className="section-title">Ollama Setup</h2>
                <p className="section-subtitle">
                    AI Sandbox uses Ollama for local model inference. All model interactions
                    are managed through a simple HTTP API at <code>localhost:11434</code>.
                </p>
                <h3 className="subsection-title">Installation</h3>
                <CodeBlock title="Shell" language="bash">
{`# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull recommended model
ollama pull qwen2.5-coder:7b

# List available models
ollama list

# Verify it's running
curl http://localhost:11434/api/tags`}
</CodeBlock>
                <p className="section-text">
                    After installation, start the Ollama serve process:
                </p>
                <CodeBlock title="Shell" language="bash">
{`ollama serve`}
</CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">Recommended Models</h2>
                <div className="model-grid">
                    <div className="model-card">
                        <h3 className="model-name">qwen2.5-coder:7b</h3>
                        <p className="model-size">4.4 GB</p>
                        <p className="model-description">
                            Code-specialized model optimized for reasoning and tool use.
                            Best balance of speed and capability for the M4 Mac constraint.
                        </p>
                        <ul className="model-specs">
                            <li>Context: 16,384 tokens</li>
                            <li>VRAM: ~5 GB</li>
                            <li>Good for: General exploration, tool use, code reading</li>
                        </ul>
                    </div>
                    <div className="model-card">
                        <h3 className="model-name">qwen2.5-coder:14b</h3>
                        <p className="model-size">8.9 GB</p>
                        <p className="model-description">
                            Larger, more capable model for complex reasoning and deep
                            analysis when hardware permits.
                        </p>
                        <ul className="model-specs">
                            <li>Context: 32,768 tokens</li>
                            <li>VRAM: ~12 GB</li>
                            <li>Good for: Detailed code analysis, complex reasoning</li>
                        </ul>
                    </div>
                    <div className="model-card">
                        <h3 className="model-name">llama3.1:8b</h3>
                        <p className="model-size">4.7 GB</p>
                        <p className="model-description">
                            General-purpose model with strong instruction following.
                            Good all-around choice for agent conversations.
                        </p>
                    </div>
                    <div className="model-card">
                        <h3 className="model-name">llama3.1:70b</h3>
                        <p className="model-size">40.1 GB</p>
                        <p className="model-description">
                            Flagship model only for high-end hardware (32GB+ RAM).
                            Best reasoning and analysis capability.
                        </p>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Model Configuration</h2>
                <p className="section-subtitle">
                    All model settings are in <code>config.yaml</code> under the <code>model</code>
                    section. Here are all available options with defaults:
                </p>
                <CodeBlock title="model config section" language="yaml">
{`model:
  host: "http://localhost:11434"
  default: "qwen2.5-coder:7b"
  context_window: 32768
  max_output_tokens: 512
  temperature: 0.7
  timeout: 300`}
</CodeBlock>

                <h3 className="subsection-title">Temperature & Creativity</h3>
                <p className="section-text">
                    <strong>Temperature 0.1–0.3:</strong> Deterministic, focused, good for
                    code and logical reasoning. Agents will be conservative and consistent.
                </p>
                <p className="section-text">
                    <strong>Temperature 0.5–0.7:</strong> Balanced — good default for most
                    exploratory and analytical tasks.
                </p>
                <p className="section-text">
                    <strong>Temperature 0.8–1.2:</strong> Creative, diverse outputs. May
                    produce more novel tool-use patterns but less coherent long-term strategies.
                </p>

                <h3 className="subsection-title">Timeout & Resource Limits</h3>
                <p className="section-text">
                    <code>timeout</code> sets the maximum seconds for any single model request.
                    On M4 Mac with 16GB, typical inference times are:
                </p>
                <ul className="resource-list">
                    <li>qwen2.5-coder:7b — 1–3 seconds per response</li>
                    <li>qwen2.5-coder:14b — 3–8 seconds per response</li>
                    <li>llama3.1:8b — 2–5 seconds per response</li>
                </ul>

                <h3 className="subsection-title">Model Override via Environment</h3>
                <CodeBlock title="Shell" language="bash">
{`# Override default model
export SANDBOX_MODEL="llama3.1:8b"

# Override host for remote Ollama
export OLLAMA_HOST="http://remote-host:11434"}`}
</CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">Model Switching During Runtime</h2>
                <p className="section-subtitle">
                    You can switch models mid-conversation by changing the config and
                    restarting agents, or via the CLI:
                </p>
                <CodeBlock title="CLI" language="bash">
{`# Change model via environment
SANDBOX_MODEL=qwen2.5-coder:14b python -m app start`}
</CodeBlock>
                <p className="section-text">
                    Note: Changing models mid-conversation will reset the conversation
                    context since different models have different tokenizers and context
                    handling characteristics.
                </p>
            </section>

            <section className="content-section">
                <h2 className="section-title">GPU / MPS Considerations</h2>
                <p className="section-text">
                    On M4 Mac, AI Sandbox uses Apple's Metal Performance Shaders (MPS)
                    through Ollama's built-in acceleration. For best performance:
                </p>
                <ul className="resource-list">
                    <li>Ensure Ollama is using the correct device: <code>ollama --gpu true</code></li>
                    <li>Monitor with: <code>top -l 1 | grep -i ollama</code></li>
                    <li>Memory pressure: Keep below 14GB to leave room for other processes</li>
                    <li>If MPS isn't detected, Ollama will fall back to CPU</li>
                </ul>
                <CodeBlock title="Check MPS status" language="bash">
{`# Check if Ollama uses MPS
python3 -c "
import requests
r = requests.get('http://localhost:11434/api/tags')
print(r.json())
"`}
</CodeBlock>
            </section>
        </div>
    );
}