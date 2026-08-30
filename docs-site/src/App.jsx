import React, { useState, useEffect } from 'react';
import { HashRouter, Routes, Route, useLocation } from 'react-router-dom';
import './App.css';
import Sidebar from './components/Sidebar';
import Overview from './pages/Overview';
import QuickStart from './pages/QuickStart';
import Installation from './pages/Installation';
import Architecture from './pages/Architecture';
import Agents from './pages/Agents';
import Conversation from './pages/Conversation';
import Tools from './pages/Tools';
import Config from './pages/Config';
import Models from './pages/Models';
import Permissions from './pages/Permissions';
import CLI from './pages/CLI';
import DB from './pages/DB';
import Browser from './pages/Browser';
import Control from './pages/Control';
import Memory from './pages/Memory';
import Performance from './pages/Performance';
import API from './pages/API';
import Troubleshooting from './pages/Troubleshooting';
import Deployment from './pages/Deployment';
import Research from './pages/Research';

function ScrollToTop() {
    const { pathname } = useLocation();
    useEffect(() => {
        window.scrollTo(0, 0);
    }, [pathname]);
    return null;
}

function AppLayout() {
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const location = useLocation();

    useEffect(() => {
        setSidebarOpen(false);
    }, [location.pathname]);

    return (
        <div className="app-layout">
            <button
                className="mobile-menu-btn"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                aria-label="Toggle menu"
            >
                {sidebarOpen ? '✕' : '☰'}
            </button>
            <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
            <main className="main-content">
                <Routes>
                    <Route path="/" element={<Overview />} />
                    <Route path="/quickstart" element={<QuickStart />} />
                    <Route path="/installation" element={<Installation />} />
                    <Route path="/architecture" element={<Architecture />} />
                    <Route path="/agents" element={<Agents />} />
                    <Route path="/conversation" element={<Conversation />} />
                    <Route path="/tools" element={<Tools />} />
                    <Route path="/config" element={<Config />} />
                    <Route path="/models" element={<Models />} />
                    <Route path="/permissions" element={<Permissions />} />
                    <Route path="/cli" element={<CLI />} />
                    <Route path="/db" element={<DB />} />
                    <Route path="/browser" element={<Browser />} />
                    <Route path="/control" element={<Control />} />
                    <Route path="/memory" element={<Memory />} />
                    <Route path="/performance" element={<Performance />} />
                    <Route path="/api" element={<API />} />
                    <Route path="/troubleshooting" element={<Troubleshooting />} />
                    <Route path="/deployment" element={<Deployment />} />
                    <Route path="/research" element={<Research />} />
                </Routes>
            </main>
        </div>
    );
}

export default function App() {
    return (
        <HashRouter>
            <ScrollToTop />
            <AppLayout />
        </HashRouter>
    );
}
