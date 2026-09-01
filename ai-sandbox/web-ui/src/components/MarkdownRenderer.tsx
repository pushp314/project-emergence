'use client';

import React, { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';

// Clean enterprise dark theme — based on VS Code "Quiet Light" dark adaptation
const enterpriseCodeTheme: { [key: string]: React.CSSProperties } = {
  'code[class*="language-"]': {
    color: '#d4d4d8',
    fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
    fontSize: '0.8125rem',
    lineHeight: '1.65',
  },
  'token.comment': { color: '#52525b', fontStyle: 'italic' },
  'token.string': { color: '#86efac' },
  'token.number': { color: '#93c5fd' },
  'token.keyword': { color: '#a78bfa' },
  'token.function': { color: '#67e8f9' },
  'token.operator': { color: '#d4d4d8' },
  'token.punctuation': { color: '#71717a' },
  'token.class-name': { color: '#fde68a' },
  'token.boolean': { color: '#93c5fd' },
  'token.builtin': { color: '#67e8f9' },
  'token.attr-name': { color: '#86efac' },
  'token.attr-value': { color: '#fda4af' },
};

function MermaidBlock({ code }: { code: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!ref.current) return;
    let cancelled = false;
    (async () => {
      try {
        const { default: mermaid } = await import('mermaid');
        mermaid.initialize({
          startOnLoad: false,
          theme: 'dark',
          themeVariables: {
            background: '#0a0a0c',
            primaryColor: '#1c1c20',
            primaryTextColor: '#d4d4d8',
            primaryBorderColor: '#3f3f46',
            lineColor: '#52525b',
            secondaryColor: '#18181b',
            tertiaryColor: '#111113',
            edgeLabelBackground: '#18181b',
            nodeTextColor: '#f2f2f3',
            fontFamily: 'Inter, sans-serif',
            fontSize: '13px',
          },
          flowchart: { curve: 'basis', htmlLabels: true },
          sequence: { actorMargin: 60, noteMargin: 8 },
        });
        const id = `mm-${Math.random().toString(36).slice(2)}`;
        const { svg } = await mermaid.render(id, code);
        if (!cancelled && ref.current) { ref.current.innerHTML = svg; setDone(true); }
      } catch (e: any) { if (!cancelled) setError(e.message); }
    })();
    return () => { cancelled = true; };
  }, [code]);

  if (error) return (
    <div style={{ background: 'var(--red-bg)', border: '1px solid var(--red-border)', borderRadius: 'var(--r-md)', padding: '10px 14px', margin: '0.65em 0' }}>
      <div style={{ fontSize: '0.75rem', color: 'var(--red-light)', fontWeight: 600, marginBottom: 6 }}>Diagram render error</div>
      <pre style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.75rem', color: 'var(--zinc-500)', whiteSpace: 'pre-wrap' }}>{code}</pre>
    </div>
  );

  return (
    <div className="mermaid-box anim-fade-in">
      {!done && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-muted)', fontSize: '0.75rem' }}>
          <span className="anim-spin" style={{ display: 'inline-block' }}>◌</span>
          Rendering diagram…
        </div>
      )}
      <div ref={ref} style={{ display: done ? 'block' : 'none' }} />
    </div>
  );
}

interface MarkdownRendererProps { content: string; className?: string; }

export function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  return (
    <div className={`md ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ className: cls, children, ...props }: any) {
            const match = /language-(\w+)/.exec(cls || '');
            const lang = match?.[1] || '';
            const codeStr = String(children).replace(/\n$/, '');
            const isInline = !cls;

            if (!isInline && lang === 'mermaid') return <MermaidBlock code={codeStr} />;

            if (!isInline && lang) {
              return (
                <div style={{ position: 'relative', margin: '0.65em 0' }}>
                  <div style={{
                    position: 'absolute', top: 8, right: 12, zIndex: 1,
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: '0.625rem', color: 'var(--zinc-600)',
                    textTransform: 'uppercase', letterSpacing: '0.07em',
                  }}>{lang}</div>
                  <SyntaxHighlighter
                    useInlineStyles
                    style={enterpriseCodeTheme}
                    language={lang}
                    PreTag="div"
                    customStyle={{
                      background: '#0a0a0c',
                      border: '1px solid var(--border-base)',
                      borderRadius: '8px',
                      padding: '13px 16px',
                      margin: 0,
                      fontSize: '0.8125rem',
                      lineHeight: '1.65',
                      overflowX: 'auto',
                    }}
                    codeTagProps={{ style: { fontFamily: "'JetBrains Mono', 'Fira Code', monospace" } }}
                    {...props}
                  >
                    {codeStr}
                  </SyntaxHighlighter>
                </div>
              );
            }

            return (
              <code style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: '0.8em',
                background: 'rgba(255,255,255,0.06)',
                border: '1px solid var(--border-subtle)',
                padding: '0 5px', borderRadius: '4px',
                color: 'var(--zinc-300)',
              }} {...props}>{children}</code>
            );
          },

          table: ({ children }) => (
            <div style={{ overflowX: 'auto', margin: '0.65em 0' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>{children}</table>
            </div>
          ),
          th: ({ children }) => (
            <th style={{
              background: 'rgba(255,255,255,0.03)', color: 'var(--text-secondary)',
              fontWeight: 600, padding: '7px 12px', textAlign: 'left',
              borderBottom: '1px solid var(--border-base)',
              fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.04em',
            }}>{children}</th>
          ),
          td: ({ children }) => (
            <td style={{ padding: '7px 12px', borderBottom: '1px solid var(--border-faint)', color: 'var(--text-primary)' }}>{children}</td>
          ),
          blockquote: ({ children }) => (
            <blockquote style={{
              borderLeft: '2px solid var(--zinc-700)', padding: '8px 14px',
              background: 'rgba(255,255,255,0.02)',
              borderRadius: '0 var(--r-sm) var(--r-sm) 0',
              color: 'var(--text-secondary)', margin: '0.65em 0',
            }}>{children}</blockquote>
          ),
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer"
              style={{ color: 'var(--blue-400)', textDecoration: 'none' }}
              onMouseEnter={e => (e.currentTarget.style.textDecoration = 'underline')}
              onMouseLeave={e => (e.currentTarget.style.textDecoration = 'none')}
            >{children}</a>
          ),
          hr: () => <hr style={{ border: 'none', borderTop: '1px solid var(--border-subtle)', margin: '1em 0' }} />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
