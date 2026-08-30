import React from 'react';
import CodeBlock from '../components/CodeBlock';
import './Permissions.css';

export default function Permissions() {
    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">Permissions</h1>
                <p className="page-subtitle">
                    Six-tier permission system for agent tool access
                </p>
            </div>

            <section className="content-section">
                <h2 className="section-title">Permission Levels</h2>
                <p className="section-subtitle">
                    Every tool call an agent makes must pass through the permission system.
                    Six levels define what each agent can do. The system automatically
                    grants auto-approved permissions and requires explicit approval for
                    the remaining levels.
                </p>

                <div className="permission-grid">
                    <div className="perm-card perm-read">
                        <div className="perm-header">
                            <span className="perm-level">read</span>
                        </div>
                        <div className="perm-body">
                            <h4 className="perm-title">Read-Only Access</h4>
                            <p className="perm-desc">
                                Agents can inspect files, data, and information but cannot
                                create, modify, or delete anything. This is the safest
                                permission level and is granted by default.
                            </p>
                            <ul className="perm-tools">
                                <li>read_file</li>
                                <li>list_directory</li>
                                <li>search_files</li>
                                <li>web_fetch</li>
                                <li>web_search</li>
                            </ul>
                        </div>
                    </div>

                    <div className="perm-card perm-write">
                        <div className="perm-header">
                            <span className="perm-level">write</span>
                        </div>
                        <div className="perm-body">
                            <h4 className="perm-title">File Modification</h4>
                            <p className="perm-desc">
                                Agents can create new files and modify existing ones within
                                the sandbox path. Operations are scoped to the project directory
                                and cannot write outside the permitted root.
                            </p>
                            <ul className="perm-tools">
                                <li>write_file</li>
                                <li>edit_file</li>
                                <li>delete_file</li>
                            </ul>
                        </div>
                    </div>

                    <div className="perm-card perm-execute">
                        <div className="perm-header">
                            <span className="perm-level">execute</span>
                        </div>
                        <div className="perm-body">
                            <h4 className="perm-title">Command Execution</h4>
                            <p className="perm-desc">
                                Agents can run shell commands via the terminal tool. Each
                                command is checked against the allowed_commands whitelist
                                in config.yaml. Commands not in the list are automatically
                                blocked.
                            </p>
                            <ul className="perm-notes">
                                <li>Auto-approved for config.yaml whitelist commands</li>
                                <li>All other commands require explicit approval</li>
                                <li>Timeout: configurable per-agent</li>
                            </ul>
                        </div>
                    </div>

                    <div className="perm-card perm-network">
                        <div className="perm-header">
                            <span className="perm-level">network</span>
                        </div>
                        <div className="perm-body">
                            <h4 className="perm-title">Network Access</h4>
                            <p className="perm-desc">
                                Agents can fetch web pages and perform search queries.
                                This includes both reading content from the internet and
                                performing search queries. Network operations are logged
                                with full URLs and timestamps for auditability.
                            </p>
                            <ul className="perm-tools">
                                <li>web_fetch</li>
                                <li>web_search</li>
                                <li>Any URL accessed is logged</li>
                            </ul>
                        </div>
                    </div>

                    <div className="perm-card perm-install">
                        <div className="perm-header">
                            <span className="perm-level">install</span>
                        </div>
                        <div className="perm-body">
                            <h4 className="perm-title">Package Installation</h4>
                            <p className="perm-desc">
                                Agents can install packages via pip, npm, or other package
                                managers. This is a high-risk operation and is typically
                                restricted. When enabled, it allows agents to expand their
                                capabilities during a conversation.
                            </p>
                            <ul className="perm-notes">
                                <li>Very high risk — grants access to system packages</li>
                                <li>Only available when explicitly enabled in config</li>
                                <li>Strongly discouraged for research involving unknown topics</li>
                            </ul>
                        </div>
                    </div>

                    <div className="perm-card perm-system">
                        <div className="perm-header">
                            <span className="perm-level">system</span>
                        </div>
                        <div className="perm-body">
                            <h4 className="perm-title">System Configuration</h4>
                            <p className="perm-desc">
                                Agents can modify system-level settings, environment
                                variables, and configuration files. This is the most
                                permissive level and should only be granted in trusted
                                research environments.
                            </p>
                            <ul className="perm-tools">
                                <li>Environment variable modification</li>
                                <li>Configuration file updates</li>
                                <li>System command execution</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Auto-Approval vs Require Approval</h2>
                <div className="approval-grid">
                    <div className="approval-card approved">
                        <h4 className="approval-title">Auto-Approved</h4>
                        <p className="approval-desc">
                            These permission levels are granted automatically without
                            user intervention. Default set includes: <code>read</code>,
                            and optionally <code>write</code> depending on config.
                        </p>
                        <ul>
                            <li><code>read</code> — Always auto-approved</li>
                            <li><code>write</code> — Configurable: auto or require approval</li>
                        </ul>
                    </div>
                    <div className="approval-card pending">
                        <h4 className="approval-title">Require Approval</h4>
                        <p className="approval-desc">
                            These levels always prompt the human operator (via CLI) before
                            the agent can proceed. The system pauses and waits for an
                            explicit <code>/approve</code> command or the agent can use
                            <code>/inject</code> to request approval.
                        </p>
                        <ul>
                            <li><code>execute</code> — Always requires approval</li>
                            <li><code>network</code> — Always requires approval</li>
                            <li><code>install</code> — Always requires approval</li>
                            <li><code>system</code> — Always requires approval</li>
                        </ul>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Configuration</h2>
                <CodeBlock title="config.yaml permissions" language="yaml">
{`permissions:
  auto_approve:
    - read
    - write          # Set to empty [] to require approval for write
  require_approval:
    - execute
    - network
    - install
    - system`}
</CodeBlock>

                <h3 className="subsection-title">Runtime Overrides</h3>
                <p className="section-text">
                    Permission levels can be overridden at runtime via CLI:
                </p>
                <CodeBlock title="CLI commands" language="bash">
{`# Grant temporary approval
YOU > /approve execute

# Deny a pending request
YOU > /deny network

# Check current permissions
YOU > /status`}
</CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">Safety Guidelines for Researchers</h2>
                <div className="safety-grid">
                    <div className="safety-card">
                        <h4 className="safety-title">Start with read-only</h4>
                        <p className="safety-desc">
                            Begin every experiment with agents at <code>read</code> level only.
                            Enable additional permissions gradually as you understand the
                            agents' behavior patterns.
                        </p>
                    </div>
                    <div className="safety-card">
                        <h4 className="safety-title">Log everything</h4>
                        <p className="safety-desc">
                            Every permission change, tool call, and approval is logged to
                            SQLite. Review the evidence database before and after each
                            experiment.
                        </p>
                    </div>
                    <div className="safety-card">
                        <h4 className="safety-title">Use isolated sandboxes</h4>
                        <p className="safety-desc">
                            Set <code>filesystem.sandbox_path</code> to a dedicated
                            directory for each experiment. Prevents cross-contamination
                            between runs.
                        </p>
                    </div>
                    <div className="safety-card">
                        <h4 className="safety-title">Emergency stop discipline</h4>
                        <p className="safety-desc">
                            Memorize the <code>/stop</code> command. In case of runaway
                            agents or unsafe tool execution, this immediately halts all
                            agent activity.
                        </p>
                    </div>
                </div>
            </section>
        </div>
    );
}