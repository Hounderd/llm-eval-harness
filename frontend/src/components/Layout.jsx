import { NavLink, Outlet } from 'react-router-dom'
import './Layout.css'

export default function Layout() {
    return (
        <div className="layout">
            <aside className="sidebar">
                <div className="sidebar-logo">
                    <span className="logo-icon">⚡</span>
                    <span className="logo-text">EvalHarness</span>
                </div>
                <nav className="sidebar-nav">
                    <NavLink to="/" end className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
                        <svg width="17" height="17" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></svg>
                        Dashboard
                    </NavLink>
                    <NavLink to="/run" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
                        <svg width="17" height="17" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><polygon points="5 3 19 12 5 21 5 3" /></svg>
                        Run Suite
                    </NavLink>
                </nav>
                <div className="sidebar-footer">
                    <span className="sidebar-footer-text">LLM Eval Harness</span>
                </div>
            </aside>
            <main className="main-content">
                <Outlet />
            </main>
        </div>
    )
}
