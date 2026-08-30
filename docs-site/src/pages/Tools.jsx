import React from 'react';
import CodeBlock from '../components/CodeBlock';
import './Tools.css';

export default function Tools() {
    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">Tools &amp; Capabilities</h1>
                <p className="page-subtitle">
                    How agents interact with the real world
                </p>
            </div>

            <section className="content-section">
                <h2 className="section-title">Terminal Tool</h2>
                <p className="section-text">
                    Agents can execute shell commands to interact with the system.
                    A whitelist of allowed commands ensures safety while providing
                    useful capabilities.
                </p>
                <h3 className="section-subtitle">Allowed Commands</h3>
                <div className="tools-list">
                    <div className="tool-item">
                        <span className="tool-name">ls, pwd, echo</span>
                        <span className="tool-desc">Basic file listing and navigation</span>
                    </div>
                    <div className="tool-item">
                        <span className="tool-name">cat, head, tail, wc</span>
                        <span className="tool-desc">File reading and word count</span>
                    </div>
                    <div className="tool-item">
                        <span className="tool-name">grep, find, sort, uniq</span>
                        <span className="tool-desc">Search and text processing</span>
                    </div>
                    <div className="tool-item">
                        <span className="tool-name">python, python3, pip</span>
                        <span className="tool-desc">Python execution and packages</span>
                    </div>
                    <div className="tool-item">
                        <span className="tool-name">git</span>
                        <span className="tool-desc">Version control operations</span>
                    </div>
                    <div className="tool-item">
                        <span className="tool-name">curl, wget</span>
                        <span className="tool-desc">HTTP requests and downloads</span>
                    </div>
                    <div className="tool-item">
                        <span className="tool-name">mkdir, touch, cp, mv</span>
                        <span className="tool-desc">File and directory manipulation</span>
                    </div>
                </div>
                <CodeBlock title="Example Usage">
                    {`# Agent executing a terminal command
$ ls -la src/
$ python -c "print('Hello from the sandbox')"
$ git log --oneline -5`}
                </CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">Filesystem Tool</h2>
                <p className="section-text">
                    Agents can read, write, and manage files within the sandbox.
                    All operations are scoped to the project directory.
                </p>
                <h3 className="section-subtitle">Operations</h3>
                <div className="tools-list">
                    <div className="tool-item">
                        <span className="tool-name">read_file</span>
                        <span className="tool-desc">Read file contents with optional line range</span>
                    </div>
                    <div className="tool-item">
                        <span className="tool-name">write_file</span>
                        <span className="tool-desc">Create or overwrite file contents</span>
                    </div>
                    <div className="tool-item">
                        <span className="tool-name">edit_file</span>
                        <span className="tool-desc">Apply targeted edits to existing files</span>
                    </div>
                    <div className="tool-item">
                        <span className="tool-name">list_directory</span>
                        <span className="tool-desc">List directory contents recursively</span>
                    </div>
                    <div className="tool-item">
                        <span className="tool-name">search_files</span>
                        <span className="tool-desc">Grep-style content search across files</span>
                    </div>
                    <div className="tool-item">
                        <span className="tool-name">delete_file</span>
                        <span className="tool-desc">Remove files (requires write permission)</span>
                    </div>
                </div>
                <CodeBlock title="Example: Read & Edit">
                    {`# Read a file
read_file(path="src/main.py", offset=1, limit=50)

# Edit a specific section
edit_file(
    path="src/main.py",
    old_string="def old_name():",
    new_string="def new_name():"
)

# Search across project
search_files(pattern="TODO", path="src/")
`}
                </CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">Web Tool</h2>
                <p className="section-text">
                    Agents can fetch web pages and perform search queries to
                    gather external information during conversations.
                </p>
                <div className="tools-list">
                    <div className="tool-item">
                        <span className="tool-name">fetch</span>
                        <span className="tool-desc">Retrieve and parse web page content</span>
                    </div>
                    <div className="tool-item">
                        <span className="tool-name">search</span>
                        <span className="tool-desc">Web search with configurable result count</span>
                    </div>
                </div>
                <CodeBlock title="Example: Web Access">
                    {`# Fetch a specific URL
web_fetch(url="https://docs.python.org/3/library/json.html")

# Search the web
web_search(query="Python async best practices 2026")
`}
                </CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">Tool Gateway</h2>
                <p className="section-text">
                    All tool calls pass through a global tool gateway that
                    enforces permissions, logs activity, and applies rate limits.
                    The gateway sits between the LLM output parser and actual
                    tool execution.
                </p>
                <div className="callout-card">
                    <div className="callout-icon">⚡</div>
                    <div className="callout-content">
                        <h4 className="callout-title">Event-Driven Pipeline</h4>
                        <p className="callout-text">
                            Tool calls are dispatched as events through the
                            async event bus, enabling non-blocking execution and
                            real-time progress streaming to the UI.
                        </p>
                    </div>
                </div>
                <CodeBlock title="Gateway Flow">
                    {`LLM Output
  → Parser extracts tool_call
  → Gateway checks permissions
  → Rate limiter validates
  → Tool executes
  → Result packaged as ToolResult
  → Fed back to conversation engine`}
                </CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">Permission Levels</h2>
                <p className="section-text">
                    Each tool requires a specific permission level. Agents must
                    have the appropriate permission granted to use a tool.
                </p>
                <div className="permission-table-wrapper">
                    <table className="permission-table">
                        <thead>
                            <tr>
                                <th>Level</th>
                                <th>Description</th>
                                <th>Tools</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><span className="perm-badge perm-read">read</span></td>
                                <td>Read-only access to files and data</td>
                                <td>read_file, list_directory, search_files</td>
                            </tr>
                            <tr>
                                <td><span className="perm-badge perm-write">write</span></td>
                                <td>Create and modify files</td>
                                <td>write_file, edit_file, delete_file</td>
                            </tr>
                            <tr>
                                <td><span className="perm-badge perm-execute">execute</span></td>
                                <td>Run shell commands</td>
                                <td>terminal, python execution</td>
                            </tr>
                            <tr>
                                <td><span className="perm-badge perm-network">network</span></td>
                                <td>Access external network resources</td>
                                <td>web_fetch, web_search, curl, wget</td>
                            </tr>
                            <tr>
                                <td><span className="perm-badge perm-install">install</span></td>
                                <td>Install packages and dependencies</td>
                                <td>pip install, npm install</td>
                            </tr>
                            <tr>
                                <td><span className="perm-badge perm-system">system</span></td>
                                <td>System-level configuration changes</td>
                                <td>Environment variables, system settings</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>
        </div>
    );
}
