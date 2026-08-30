import React from 'react';
import CodeBlock from '../components/CodeBlock';

export default function Installation() {
    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">Installation</h1>
                <p className="page-subtitle">Set up AI Sandbox in minutes</p>
            </div>

            <section className="content-section">
                <h2 className="section-title">Prerequisites</h2>
                <p>Before installing AI Sandbox, ensure your system meets these requirements:</p>
                <div className="info-card">
                    <div className="info-card-title">Python 3.14+</div>
                    <p>AI Sandbox uses modern Python features including improved async generators and task groups. Python 3.14 or newer is required.</p>
                </div>
                <div className="info-card">
                    <div className="info-card-title">Ollama</div>
                    <p>A running Ollama instance with a compatible model pulled (e.g., <code>ollama pull llama3.2</code>). Ollama provides the local LLM backend.</p>
                </div>
                <div className="info-card">
                    <div className="info-card-title">16GB RAM Recommended</div>
                    <p>Running two concurrent agent loops with a local model requires sufficient memory. 16GB is recommended for comfortable operation; 8GB is the minimum with smaller models.</p>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Dependencies</h2>
                <p>All dependencies are listed in <code>requirements.txt</code> and grouped by purpose:</p>
                <CodeBlock title="requirements.txt" language="txt">
{`# Core
aiohttp
bs4
pyyaml
click
rich

# Audio (optional)
pyttsx3
edge-tts

# Database
sqlite3  # built-in with Python`}
                </CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">Install Commands</h2>
                <p>Clone the repository and install dependencies step by step:</p>

                <h3 style={{ marginTop: '24px', marginBottom: '12px', color: 'var(--text-secondary)' }}>1. Clone the repository</h3>
                <CodeBlock title="Clone" language="bash">
{`git clone https://github.com/your-org/ai-sandbox.git
cd ai-sandbox`}
                </CodeBlock>

                <h3 style={{ marginTop: '24px', marginBottom: '12px', color: 'var(--text-secondary)' }}>2. Create and activate a virtual environment</h3>
                <CodeBlock title="Virtual Environment" language="bash">
{`python -m venv .venv
source .venv/bin/activate`}
                </CodeBlock>

                <h3 style={{ marginTop: '24px', marginBottom: '12px', color: 'var(--text-secondary)' }}>3. Install dependencies</h3>
                <CodeBlock title="Install Dependencies" language="bash">
{`pip install -r requirements.txt`}
                </CodeBlock>

                <h3 style={{ marginTop: '24px', marginBottom: '12px', color: 'var(--text-secondary)' }}>4. Ensure Ollama is running</h3>
                <CodeBlock title="Ollama Setup" language="bash">
{`# Start Ollama (if not already running)
ollama serve

# Pull a compatible model
ollama pull llama3.2`}
                </CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">Verify Installation</h2>
                <p>Run the test suite to confirm everything is configured correctly:</p>
                <CodeBlock title="Verify" language="bash">
{`pytest tests/ -v`}
                </CodeBlock>
                <p>All 58 tests should pass. If any fail, check the <a href="#/troubleshooting">Troubleshooting</a> page for common solutions.</p>
            </section>
        </div>
    );
}
