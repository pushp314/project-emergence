import React from 'react';
import CodeBlock from '../components/CodeBlock';
import './QuickStart.css';

export default function QuickStart() {
    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">Quick Start</h1>
                <p className="page-subtitle">
                    Get AI Sandbox running locally in under 5 minutes
                </p>
            </div>

            <section className="content-section">
                <div className="steps-list">
                    <div className="step-card">
                        <div className="step-number">1</div>
                        <div className="step-content">
                            <h3 className="step-title">Clone &amp; Setup</h3>
                            <CodeBlock title="Terminal">
                                {`git clone https://github.com/your-org/ai-sandbox.git
cd ai-sandbox
python -m venv .venv
source .venv/bin/activate`}
                            </CodeBlock>
                        </div>
                    </div>

                    <div className="step-card">
                        <div className="step-number">2</div>
                        <div className="step-content">
                            <h3 className="step-title">Install Dependencies</h3>
                            <CodeBlock title="Terminal">
                                {`pip install -r requirements.txt`}
                            </CodeBlock>
                        </div>
                    </div>

                    <div className="step-card">
                        <div className="step-number">3</div>
                        <div className="step-content">
                            <h3 className="step-title">Pull Ollama Model</h3>
                            <CodeBlock title="Terminal">
                                {`ollama pull qwen2.5-coder:7b`}
                            </CodeBlock>
                        </div>
                    </div>

                    <div className="step-card">
                        <div className="step-number">4</div>
                        <div className="step-content">
                            <h3 className="step-title">Run</h3>
                            <CodeBlock title="Terminal">
                                {`python -m app start`}
                            </CodeBlock>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
}
