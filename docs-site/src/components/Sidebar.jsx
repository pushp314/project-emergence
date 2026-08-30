import React from 'react';
import { NavLink } from 'react-router-dom';
import './Sidebar.css';

const sections = [
    {
        title: 'Getting Started',
        items: [
            { path: '/', label: 'Overview' },
            { path: '/quickstart', label: 'Quick Start' },
            { path: '/installation', label: 'Installation' },
        ],
    },
    {
        title: 'Core Concepts',
        items: [
            { path: '/architecture', label: 'Architecture' },
            { path: '/agents', label: 'Agents' },
            { path: '/conversation', label: 'Conversation Engine' },
            { path: '/tools', label: 'Tools & Capabilities' },
        ],
    },
    {
        title: 'Configuration',
        items: [
            { path: '/config', label: 'Configuration' },
            { path: '/models', label: 'Models' },
            { path: '/permissions', label: 'Permissions' },
        ],
    },
    {
        title: 'CLI Reference',
        items: [
            { path: '/cli', label: 'Commands' },
            { path: '/db', label: 'Database Commands' },
        ],
    },
    {
        title: 'Advanced',
        items: [
            { path: '/browser', label: 'Browser Access' },
            { path: '/control', label: 'Master Control' },
            { path: '/memory', label: 'Memory System' },
            { path: '/performance', label: 'Performance' },
            { path: '/api', label: 'API Reference' },
        ],
    },
    {
        title: 'Resources',
        items: [
            { path: '/troubleshooting', label: 'Troubleshooting' },
            { path: '/deployment', label: 'Deployment' },
            { path: '/research', label: 'Research Notes' },
        ],
    },
];

export default function Sidebar({ isOpen, onClose }) {
    return (
        <>
            {isOpen && <div className="sidebar-overlay" onClick={onClose} />}
            <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
                <div className="sidebar-header">
                    <div className="sidebar-logo">
                        <span className="logo-mark">◈</span>
                        <span className="logo-text">AI Sandbox</span>
                    </div>
                    <span className="sidebar-version">v1.0</span>
                </div>
                <nav className="sidebar-nav">
                    {sections.map((section) => (
                        <div key={section.title} className="nav-section">
                            <div className="nav-section-title">{section.title}</div>
                            {section.items.map((item) => (
                                <NavLink
                                    key={item.path}
                                    to={item.path}
                                    className={({ isActive }) =>
                                        `nav-link ${isActive ? 'active' : ''}`
                                    }
                                    onClick={onClose}
                                    end={item.path === '/'}
                                >
                                    {item.label}
                                </NavLink>
                            ))}
                        </div>
                    ))}
                </nav>
                <div className="sidebar-footer">
                    <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="sidebar-link">
                        GitHub →
                    </a>
                </div>
            </aside>
        </>
    );
}
