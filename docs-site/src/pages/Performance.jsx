import React from 'react';
import CodeBlock from '../components/CodeBlock';
import './Performance.css';

export default function Performance() {
    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">Performance</h1>
                <p className="page-subtitle">
                    Benchmarks and optimization
                </p>
            </div>

            <section className="content-section">
                <h2 className="section-title">Benchmark Results</h2>
                <p className="section-subtitle">
                    AI Sandbox is designed for minimal overhead so agents can spend their time
                    thinking, not waiting. All core components are benchmarked on every build.
                </p>
                <div className="benchmark-table-wrapper">
                    <table className="benchmark-table">
                        <thead>
                            <tr>
                                <th>Component</th>
                                <th>Latency</th>
                                <th>Description</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><code>EventBus</code></td>
                                <td className="latency-value">48µs</td>
                                <td>Publish-subscribe event routing between components</td>
                            </tr>
                            <tr>
                                <td><code>SQLite Store</code></td>
                                <td className="latency-value">1.5µs</td>
                                <td>Single write operation to the persistence layer</td>
                            </tr>
                            <tr>
                                <td><code>ContextManager</code></td>
                                <td className="latency-value">466µs</td>
                                <td>Full context assembly for an agent turn</td>
                            </tr>
                            <tr>
                                <td><code>Scheduler</code></td>
                                <td className="latency-value">0.1µs</td>
                                <td>Next-agent selection and scheduling decision</td>
                            </tr>
                            <tr>
                                <td><code>Memory/agent</code></td>
                                <td className="latency-value">0.44KB</td>
                                <td>Average memory footprint per agent instance</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Running Benchmarks</h2>
                <p className="section-subtitle">
                    Run the full benchmark suite to verify performance targets on your machine.
                </p>
                <CodeBlock title="Terminal">
                    {`# Run all benchmarks
python -m pytest tests/benchmarks/ -v

# Run a specific benchmark
python -m pytest tests/benchmarks/test_event_bus.py -v

# Run with timing output
python -m pytest tests/benchmarks/ -v --tb=short -s`}
                </CodeBlock>
                <CodeBlock title="Python — Custom Benchmark">
                    {`import time
from app.core.events import EventBus

bus = EventBus()

# Warm up
for _ in range(100):
    bus.publish("test.event", {"data": "warmup"})

# Benchmark
start = time.perf_counter_ns()
for _ in range(10000):
    bus.publish("test.event", {"data": "benchmark"})
elapsed_ns = time.perf_counter_ns() - start

print(f"Average: {elapsed_ns / 10000 / 1000:.1f}µs")`}
                </CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">Resource Limits</h2>
                <p className="section-subtitle">
                    The system enforces resource limits to prevent runaway processes and ensure
                    stable operation on development machines.
                </p>
                <div className="resource-grid">
                    <div className="resource-card">
                        <div className="resource-limit">512MB</div>
                        <div className="resource-name">Max Memory</div>
                        <p className="resource-desc">
                            Total memory cap for all agents and system components combined.
                        </p>
                    </div>
                    <div className="resource-card">
                        <div className="resource-limit">30s</div>
                        <div className="resource-name">Agent Timeout</div>
                        <p className="resource-desc">
                            Maximum time a single agent turn can take before being interrupted.
                        </p>
                    </div>
                    <div className="resource-card">
                        <div className="resource-limit">50MB</div>
                        <div className="resource-name">DB Size Limit</div>
                        <p className="resource-desc">
                            Maximum SQLite database size before rotation or cleanup triggers.
                        </p>
                    </div>
                    <div className="resource-card">
                        <div className="resource-limit">100</div>
                        <div className="resource-name">Max Turns</div>
                        <p className="resource-desc">
                            Conversation turn limit per session before requiring a restart.
                        </p>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Optimization Tips</h2>
                <p className="section-subtitle">
                    Tips for getting the best performance out of your setup.
                </p>
                <div className="tips-list">
                    <div className="tip-card">
                        <h3 className="tip-title">Use a Smaller Model</h3>
                        <p className="tip-desc">
                            Smaller models (7B) generate responses faster, reducing per-turn latency
                            significantly. The system overhead is constant regardless of model size.
                        </p>
                    </div>
                    <div className="tip-card">
                        <h3 className="tip-title">Limit Tool Calls</h3>
                        <p className="tip-desc">
                            Each tool call adds I/O overhead. Configure tool permissions to only
                            expose what agents need for the current experiment.
                        </p>
                    </div>
                    <div className="tip-card">
                        <h3 className="tip-title">Tune Context Window</h3>
                        <p className="tip-desc">
                            Smaller context windows mean faster context assembly. Adjust
                            <code>max_context_tokens</code> in your config to match your needs.
                        </p>
                    </div>
                    <div className="tip-card">
                        <h3 className="tip-title">Use SSD Storage</h3>
                        <p className="tip-desc">
                            SQLite performance is disk-bound. An SSD ensures the 1.5µs write target
                            is met consistently.
                        </p>
                    </div>
                </div>
            </section>
        </div>
    );
}
