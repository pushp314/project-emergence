import React from 'react';
import './CodeBlock.css';

export default function CodeBlock({ title, language = 'bash', children }) {
    return (
        <div className="code-block">
            {title && <div className="code-block-header">{title}</div>}
            <pre><code>{children.trim()}</code></pre>
        </div>
    );
}
