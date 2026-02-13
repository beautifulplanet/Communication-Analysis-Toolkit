import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { useApi } from './hooks/useApi';
import type { CaseInfo } from './types';
import Overview from './pages/Overview';
import Timeline from './pages/Timeline';
import Patterns from './pages/Patterns';
import Evidence from './pages/Evidence';
import './App.css';

function App() {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [caseId, setCaseId] = useState<string>('');
  const { data: casesData } = useApi<{ cases: CaseInfo[] }>('/cases');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Auto-select first case
  useEffect(() => {
    if (casesData?.cases?.length && !caseId) {
      const firstWithData = casesData.cases.find((c) => c.has_data);
      if (firstWithData) setCaseId(firstWithData.case_id);
      else setCaseId(casesData.cases[0].case_id);
    }
  }, [casesData, caseId]);

  const toggleTheme = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'));

  return (
    <BrowserRouter>
      <div className="app-layout">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="sidebar__brand">
            <div className="sidebar__logo">CA</div>
            <div>
              <div className="sidebar__title">Comm Analysis</div>
              <div className="sidebar__subtitle">Dashboard</div>
            </div>
          </div>

          {/* Case selector */}
          {casesData && casesData.cases.length > 1 && (
            <div className="case-selector">
              {casesData.cases.filter((c) => c.has_data).map((c) => (
                <button
                  key={c.case_id}
                  className={`case-selector__btn ${caseId === c.case_id ? 'case-selector__btn--active' : ''}`}
                  onClick={() => setCaseId(c.case_id)}
                >
                  {c.case_name || c.case_id}
                </button>
              ))}
            </div>
          )}

          <nav className="sidebar__nav">
            <NavLink
              to="/"
              end
              className={({ isActive }) => `sidebar__link ${isActive ? 'sidebar__link--active' : ''}`}
            >
              <span className="sidebar__link-icon">📊</span>
              Overview
            </NavLink>
            <NavLink
              to="/timeline"
              className={({ isActive }) => `sidebar__link ${isActive ? 'sidebar__link--active' : ''}`}
            >
              <span className="sidebar__link-icon">📅</span>
              Timeline
            </NavLink>
            <NavLink
              to="/patterns"
              className={({ isActive }) => `sidebar__link ${isActive ? 'sidebar__link--active' : ''}`}
            >
              <span className="sidebar__link-icon">🔍</span>
              Patterns
            </NavLink>
            <NavLink
              to="/evidence"
              className={({ isActive }) => `sidebar__link ${isActive ? 'sidebar__link--active' : ''}`}
            >
              <span className="sidebar__link-icon">📋</span>
              Evidence
            </NavLink>
          </nav>

          <div className="sidebar__footer">
            <button className="theme-toggle" onClick={toggleTheme}>
              {theme === 'dark' ? '☀️' : '🌙'} {theme === 'dark' ? 'Light mode' : 'Dark mode'}
            </button>
          </div>
        </aside>

        {/* Main */}
        <main className="main-content">
          {!caseId ? (
            <div className="empty-state">
              <div className="empty-state__icon">📂</div>
              <div className="empty-state__title">No cases found</div>
              <p>Run the analysis engine first to generate DATA.json</p>
            </div>
          ) : (
            <Routes>
              <Route path="/" element={<Overview caseId={caseId} />} />
              <Route path="/timeline" element={<Timeline caseId={caseId} />} />
              <Route path="/patterns" element={<Patterns caseId={caseId} />} />
              <Route path="/evidence" element={<Evidence caseId={caseId} />} />
            </Routes>
          )}
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
