import React from 'react';
import CodeBlock from '../components/CodeBlock';
import './Deployment.css';

export default function Deployment() {
    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">Deployment</h1>
                <p className="page-subtitle">
                    Production deployment options
                </p>
            </div>

            <section className="content-section">
                <h2 className="section-title">Local Development</h2>
                <p className="section-subtitle">
                    The fastest way to get running. AI Sandbox is designed to run entirely on
                    your local machine with no external dependencies.
                </p>
                <CodeBlock title="Terminal">
                    {`# Clone and set up
git clone https://github.com/your-org/ai-sandbox.git
cd ai-sandbox
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Pull the model
ollama pull qwen2.5-coder:7b

# Run in development mode
python -m app start --dev`}
                </CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">Background Service</h2>
                <p className="section-subtitle">
                    Run AI Sandbox as a background process that persists across terminal sessions.
                </p>
                <h3 className="subsection-title">Using nohup</h3>
                <CodeBlock title="Terminal">
                    {`# Start in background
nohup python -m app start > sandbox.log 2>&1 &

# Check if running
ps aux | grep "app start"

# View logs
tail -f sandbox.log

# Stop the process
kill $(pgrep -f "app start")`}
                </CodeBlock>

                <h3 className="subsection-title">Using systemd (Linux)</h3>
                <CodeBlock title="/etc/systemd/system/ai-sandbox.service">
                    {`[Unit]
Description=AI Sandbox Multi-Agent System
After=network.target

[Service]
Type=simple
User=sandbox
WorkingDirectory=/opt/ai-sandbox
ExecStart=/opt/ai-sandbox/.venv/bin/python -m app start
Restart=on-failure
RestartSec=5
Environment=OLLAMA_HOST=localhost:11434

[Install]
WantedBy=multi-user.target`}
                </CodeBlock>
                <CodeBlock title="Terminal">
                    {`# Enable and start
sudo systemctl enable ai-sandbox
sudo systemctl start ai-sandbox

# Check status
sudo systemctl status ai-sandbox

# View logs
sudo journalctl -u ai-sandbox -f`}
                </CodeBlock>

                <h3 className="subsection-title">Using launchd (macOS)</h3>
                <CodeBlock title="~/Library/LaunchAgents/com.aisandbox.plist">
                    {`<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aisandbox</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/ai-sandbox/.venv/bin/python</string>
        <string>-m</string>
        <string>app</string>
        <string>start</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/opt/ai-sandbox</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>`}
                </CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">Environment Variables</h2>
                <p className="section-subtitle">
                    Configure AI Sandbox through environment variables for different deployment
                    contexts.
                </p>
                <div className="env-table-wrapper">
                    <table className="env-table">
                        <thead>
                            <tr>
                                <th>Variable</th>
                                <th>Default</th>
                                <th>Description</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><code>OLLAMA_HOST</code></td>
                                <td>localhost:11434</td>
                                <td>Ollama server address</td>
                            </tr>
                            <tr>
                                <td><code>SANDBOX_DB_PATH</code></td>
                                <td>sandbox.db</td>
                                <td>SQLite database file path</td>
                            </tr>
                            <tr>
                                <td><code>SANDBOX_LOG_LEVEL</code></td>
                                <td>INFO</td>
                                <td>Logging verbosity (DEBUG, INFO, WARNING, ERROR)</td>
                            </tr>
                            <tr>
                                <td><code>SANDBOX_MAX_MEMORY</code></td>
                                <td>512</td>
                                <td>Max memory in MB for all agents</td>
                            </tr>
                            <tr>
                                <td><code>SANDBOX_TIMEOUT</code></td>
                                <td>30</td>
                                <td>Per-turn timeout in seconds</td>
                            </tr>
                            <tr>
                                <td><code>SANDBOX_PORT</code></td>
                                <td>8080</td>
                                <td>HTTP port for the web interface</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Docker</h2>
                <p className="section-subtitle">
                    Optional containerized deployment for consistent environments.
                </p>
                <CodeBlock title="Dockerfile">
                    {`FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["python", "-m", "app", "start"]`}
                </CodeBlock>
                <CodeBlock title="Terminal">
                    {`# Build
docker build -t ai-sandbox .

# Run (connect to host Ollama)
docker run -p 8080:8080 \\
  -e OLLAMA_HOST=host.docker.internal:11434 \\
  -v $(pwd)/data:/app/data \\
  ai-sandbox`}
                </CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">Resource Requirements</h2>
                <div className="resource-grid">
                    <div className="resource-card">
                        <div className="resource-limit">4GB</div>
                        <div className="resource-name">Min RAM</div>
                        <p className="resource-desc">
                            Required for system + 7B model inference.
                        </p>
                    </div>
                    <div className="resource-card">
                        <div className="resource-limit">8GB+</div>
                        <div className="resource-name">Recommended RAM</div>
                        <p className="resource-desc">
                            Comfortable headroom for multiple agents and tools.
                        </p>
                    </div>
                    <div className="resource-card">
                        <div className="resource-limit">2 CPU</div>
                        <div className="resource-name">Min Cores</div>
                        <p className="resource-desc">
                            Minimum for Ollama inference + sandbox process.
                        </p>
                    </div>
                    <div className="resource-card">
                        <div className="resource-limit">1GB</div>
                        <div className="resource-name">Disk Space</div>
                        <p className="resource-desc">
                            For the model, database, and logs combined.
                        </p>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Security Considerations</h2>
                <p className="section-subtitle">
                    AI Sandbox grants agents real system access. Review these controls before
                    any production or shared deployment.
                </p>
                <div className="security-list">
                    <div className="security-card">
                        <h3 className="security-title">Tool Sandboxing</h3>
                        <p className="security-desc">
                            Configure blocked_commands and allowed_patterns to limit what agents
                            can execute. Never expose unrestricted terminal access on shared
                            machines.
                        </p>
                    </div>
                    <div className="security-card">
                        <h3 className="security-title">Network Isolation</h3>
                        <p className="security-desc">
                            Agents can fetch web content by default. Disable web_fetch in
                            tool_permissions if network access should be restricted.
                        </p>
                    </div>
                    <div className="security-card">
                        <h3 className="security-title">Filesystem Boundaries</h3>
                        <p className="security-desc">
                            Agents can read and write files. Use the sandbox_root config to
                            restrict file access to a specific directory.
                        </p>
                    </div>
                    <div className="security-card">
                        <h3 className="security-title">Emergency Stop</h3>
                        <p className="security-desc">
                            The emergency stop button (Ctrl+C or SIGINT) immediately halts all
                            agent activity. Available at every point in the conversation loop.
                        </p>
                    </div>
                </div>
            </section>
        </div>
    );
}
