import React from 'react';
import CodeBlock from '../components/CodeBlock';
import './Browser.css';

export default function Browser() {
    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">Browser Access</h1>
                <p className="page-subtitle">
                    Let agents browse the web and extract structured content
                </p>
            </div>

            <section className="content-section">
                <h2 className="section-title">BrowserSession API</h2>
                <p className="section-subtitle">
                    Programmatic web browsing for agents. The BrowserSession class
                    provides async methods for fetching pages, extracting content,
                    and searching the web.
                </p>

                <h3 className="subsection-title">Initialization</h3>
                <CodeBlock title="JavaScript import" language="javascript">
{`import { BrowserSession, ContentExtractor } from 'app/browser';`}
</CodeBlock>

                <CodeBlock title="Create session" language="javascript">
{`const session = new BrowserSession();
await session.open();`}
</CodeBlock>

                <h3 className="subsection-title">Fetching Pages</h3>
                <CodeBlock title="Fetch a page" language="javascript">
{`// Get a webpage
const page = await session.get('https://example.com');

// page structure
/*
{
  html: '<!doctype html>...',
  status: 200,
  headers: { ... }
}
*/`}
</CodeBlock>

                <CodeBlock title="Search the web" language="javascript">
{`// Search using DuckDuckGo HTML
const results = await session.search('Python asyncio tutorial');

/* results structure:
[
  {
    title: 'asyncio — What's New in Python 3.14',
    url: 'https://docs.python.org/3/library/asyncio.html',
    snippet: '...introduction to asyncio...'
  }
]*/`}
</CodeBlock>

                <h3 className="subsection-title">Content Extraction</h3>
                <CodeBlock title="Extract structured content" language="javascript">
{`// Extract text, links, headings, code, tables from HTML
const extractor = new ContentExtractor();
const content = extractor.extract(page.html);

/* content structure:
{
  title: 'Page Title',
  text: 'Cleaned readable text...',
  headings: [
    { level: 1, text: 'Main Title' },
    { level: 2, text: 'Section 1' }
  ],
  links: [
    { text: 'Link text', url: 'https://...' }
  ],
  code_blocks: [
    'function foo() { ... }'
  ],
  tables: [
    [ { col1: 'val1' }, { col1: 'val2' } ]
  ],
  meta: {
    description: '...',
    author: '...'
  }
}*/
`}
</CodeBlock>

                <h3 className="subsection-title">Close Session</h3>
                <CodeBlock title="Cleanup" language="javascript">
{`await session.close();`}
</CodeBlock>

                <h3 className="subsection-title">Example: Research a Topic</h3>
                <CodeBlock title="Full research workflow" language="javascript">
{`// Research a topic using the browser session
async function researchTopic(topic) {
  const session = new BrowserSession();
  
  // Search for the topic
  const results = await session.search(topic);
  
  // Fetch the top result
  if (results.length > 0) {
    const page = await session.get(results[0].url);
    
    // Extract structured content
    const extractor = new ContentExtractor();
    const content = extractor.extract(page.html);
    
    console.log('Title:', content.title);
    console.log('Main text:', content.text.substring(0, 500));
    console.log('Key headings:');
    content.headings.forEach(h => console.log(`  h${h.level}: ${h.text}`));
    console.log('Important links:');
    content.links.slice(0, 5).forEach(l => console.log(`  - ${l.text}: ${l.url}`));
    
    await session.close();
  }
}

// Run the research
researchTopic('Python asyncio best practices 2026');`}
</CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">Agent Tool Usage</h2>
                <p className="section-subtitle">
                    Agents can browse the web by emitting tool calls in their responses.
                    The conversation engine parses these and routes them through the
                    browser session.
                </p>

                <CodeBlock title="Agent web fetch" language="text">
{`[TOOL:web:{"url": "https://docs.python.org/3/library/asyncio.html"}]`}
</CodeBlock>

                <CodeBlock title="Agent web search" language="text">
{`[TOOL:web:{"query": "Python asyncio best practices 2026"}]`}
</CodeBlock>

                <h3 className="subsection-title">Extraction Results in Conversation</h3>
                <CodeBlock title="Full conversation with browser results" language="text">
{`🧭 ATLAS  Turn 3
│ I need to understand async/await best practices for our project.
│
│ [TOOL:web:{"query": "Python asyncio best practices"}]

[web result: Python Asyncio: Best Practices for 2026
  The async/await syntax was introduced in Python 3.5. Since then,
  the ecosystem has evolved significantly. Key patterns include:]

│ • Use asyncio.run() as the entry point for standalone programs
│ • prefer create_task() over ensure_future() for new tasks
│ • Group related coroutines with asyncio.gather()
│ • Handle errors with try/except around await expressions
│ • Use timeouts with asyncio.wait_for() for long-running operations
│ • Consider web scraping rate limits when fetching multiple pages

│ The top result from DuckDuckGo covers the key patterns we need.
│ Let me also check the official documentation for the most authoritative source.]

│ [TOOL:web:{"url": "https://docs.python.org/3/library/asyncio.html"}]}

[web result: https://docs.python.org/3/library/asyncio.html
  ...official documentation on asyncio primitives...
  Key sections: asyncio.run(), Task objects, Condition, Event, Lock,
  Semaphore, Queue, Future]

🧭 ATLAS  Turn 3 (continued)
│ The official Python documentation confirms these patterns. The
 │ create_task() approach is preferred for concurrent operations
 │ within running event loops, while asyncio.run() is for standalone
 │ programs. Both are important to understand.`}
</CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">ContentExtractor Details</h2>
                <h3 className="subsection-title">What Gets Extracted</h3>
                <ul className="extracted-features">
                    <li><strong>Title</strong> — Page <code><title></code> tag content</li>
                    <li><strong>Readable text</strong> — All text with scripts, styles, and navigation removed</li>
                    <li><strong>Headings</strong> — h1 through h6 with hierarchy preserved</li>
                    <li><strong>Links</strong> — All <code><a></code> tags with visible text and href</li>
                    <li><strong>Code blocks</strong> — <code><code></code> and <code><pre></code> elements</li>
                    <li><strong>Tables</strong> — HTML tables converted to array of objects</li>
                    <li><strong>Meta description</strong> — <code><meta name="description"</code></code></li>
                </ul>

                <h3 className="subsection-title">Extraction Priority</h3>
                <p className="section-text">
                    The extractor prioritizes <em>main content</em> over boilerplate:
                </p>
                <ol className="extracted-steps">
                    <li>Remove <code><script></code> and <code><style></code> tags</li>
                    <li>Remove <code><nav></code>, <code><footer></code>, <code><header></code> if not main content</li>
                    <li>Extract primary <code><article></code> or <code><main></code> content</li>
                    <li>Extract headings to understand structure</li>
                    <li>Extract all links for navigation context</li>
                    <li>Extract code blocks and tables as structured data</li>
                    <li>Return cleaned readable text</li>
                </ol>
            </section>

            <section className="content-section">
                <h2 className="section-title">Limitations & Best Practices</h2>
                <ul className="limitations-list">
                    <li><strong>Rate limiting</strong> — Avoid rapid successive fetches; the system imposes delays</li>
                    <li><strong>Paywalls & robots.txt</strong> — Respect website terms; the tool may block restricted sites</li>
                    <li><strong>JavaScript-heavy pages</strong> — Dynamic content rendered by JS may not be fully accessible</li>
                    <li><strong>Timeouts</strong> — Web fetches have a default 30-second timeout</li>
                    <li><strong>Size limits</strong> — Responses are truncated at 500KB</li>
                </ul>
                <p className="section-text">
                    <strong>Best practice:</strong> Always check the extraction results for completeness,
                    and combine web tool use with filesystem/code inspection for comprehensive research.
                </p>
            </section>
        </div>
    );
}