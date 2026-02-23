import React, { useState } from 'react';
import './App.css';

// ── Session ID — generated once per browser tab, persisted in sessionStorage ──
const _getSessionId = () => {
  try {
    let id = sessionStorage.getItem('cra_session_id');
    if (!id) { id = crypto.randomUUID(); sessionStorage.setItem('cra_session_id', id); }
    return id;
  } catch { return 'unknown'; }
};
const SESSION_ID = _getSessionId();

// ── Shared UI Components ─────────────────────────────────────────────────────

/** Reusable button with variant + size system */
function Btn({ variant = 'primary', size = 'md', style: extraStyle, children, ...props }) {
  const base = {
    border: 'none', borderRadius: 'var(--radius-sm)', cursor: 'pointer',
    fontFamily: 'var(--font-family)', fontWeight: 600,
    transition: 'opacity 0.15s, box-shadow 0.15s', display: 'inline-flex',
    alignItems: 'center', gap: '4px', whiteSpace: 'nowrap',
  };
  const variants = {
    primary:   { background: 'var(--color-accent)',   color: 'white' },
    secondary: { background: 'white', color: 'var(--color-accent)', border: '1px solid var(--color-accent)' },
    ghost:     { background: 'transparent', color: 'var(--color-neutral-500)' },
    danger:    { background: 'var(--color-danger)',   color: 'white' },
    success:   { background: 'var(--color-success)',  color: 'white' },
    navy:      { background: 'var(--color-primary)',  color: 'white' },
  };
  const sizes = {
    xs: { padding: '2px 8px',   fontSize: '11px' },
    sm: { padding: '4px 10px',  fontSize: '12px' },
    md: { padding: '6px 14px',  fontSize: '13px' },
    lg: { padding: '9px 20px',  fontSize: '14px' },
  };
  return (
    <button
      style={{ ...base, ...variants[variant] || variants.primary, ...sizes[size] || sizes.md, ...extraStyle }}
      onMouseEnter={e => { e.currentTarget.style.opacity = '0.88'; }}
      onMouseLeave={e => { e.currentTarget.style.opacity = '1'; }}
      {...props}
    >
      {children}
    </button>
  );
}

/** Toast notification container — rendered at App root level */
function ToastContainer({ toasts }) {
  const colours = { success: 'var(--color-success)', error: 'var(--color-danger)', info: 'var(--color-accent)' };
  return (
    <div style={{ position: 'fixed', top: 16, right: 16, zIndex: 9999,
      display: 'flex', flexDirection: 'column', gap: 8, pointerEvents: 'none' }}>
      {toasts.map(t => (
        <div key={t.id} style={{
          background: colours[t.type] || colours.info, color: 'white',
          padding: '10px 16px', borderRadius: 'var(--radius-md)',
          fontSize: 'var(--font-size-base)', fontWeight: 500,
          boxShadow: 'var(--shadow-lg)', minWidth: 220, maxWidth: 340,
          fontFamily: 'var(--font-family)',
        }}>
          {t.message}
        </div>
      ))}
    </div>
  );
}

// Live API Usage Banner
function UsageBanner() {
  const [usage, setUsage] = useState(null);
  const [expanded, setExpanded] = useState(false);

  React.useEffect(() => {
    const fetch_usage = () => {
      fetch('/api/usage').then(r => r.json()).then(setUsage).catch(() => {});
    };
    fetch_usage();
    const interval = setInterval(fetch_usage, 5000); // refresh every 5s
    return () => clearInterval(interval);
  }, []);

  if (!usage || usage.total_api_calls === 0) return null;

  return (
    <div style={{
      background: usage.estimated_cost_usd > 0.10 ? '#fff7ed' : '#f0fdf4',
      borderBottom: `2px solid ${usage.estimated_cost_usd > 0.10 ? '#f97316' : '#22c55e'}`,
      padding: '6px 24px', display: 'flex', alignItems: 'center', gap: '16px',
      fontSize: '13px', flexWrap: 'wrap'
    }}>
      <span>💰 <strong>API Usage This Session:</strong></span>
      <span>🔢 Tokens: <strong>{usage.total_tokens.toLocaleString()}</strong>
        <span style={{ color: '#64748b', marginLeft: '6px' }}>
          ({usage.total_input_tokens.toLocaleString()} in / {usage.total_output_tokens.toLocaleString()} out)
        </span>
      </span>
      <span>📞 API Calls: <strong>{usage.total_api_calls}</strong></span>
      <span>🤖 LLM Evaluations: <strong>{usage.llm_rule_evaluations}</strong></span>
      <span style={{ fontWeight: 700, color: usage.estimated_cost_usd > 0.10 ? '#ea580c' : '#16a34a' }}>
        Est. Cost: {usage.estimated_cost_display}
      </span>
      <button onClick={() => setExpanded(!expanded)} style={{
        marginLeft: 'auto', padding: '2px 10px', fontSize: '12px',
        background: 'transparent', border: '1px solid #94a3b8',
        borderRadius: '4px', cursor: 'pointer', color: '#475569'
      }}>
        {expanded ? 'Hide Details' : 'Details'}
      </button>
      {expanded && (
        <div style={{
          width: '100%', background: '#1e293b', color: '#e2e8f0',
          borderRadius: '6px', padding: '10px 14px', fontSize: '12px',
          fontFamily: 'monospace', marginTop: '4px'
        }}>
          Input tokens: {usage.total_input_tokens.toLocaleString()} × $3.00/M = ${((usage.total_input_tokens / 1e6) * 3).toFixed(6)}
          {'  |  '}
          Output tokens: {usage.total_output_tokens.toLocaleString()} × $15.00/M = ${((usage.total_output_tokens / 1e6) * 15).toFixed(6)}
          {'  |  '}
          <strong>Total: {usage.estimated_cost_display}</strong>
          {'  '}
          <button onClick={() => fetch('/api/usage/reset', { method: 'POST' }).then(() => setUsage(null))}
            style={{ marginLeft: '12px', padding: '1px 8px', fontSize: '11px', background: '#dc2626',
              color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer' }}>
            Reset Counter
          </button>
        </div>
      )}
    </div>
  );
}

// Main App Component
function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [chatContext, setChatContext] = useState({ site_id: '', visit_id: null });
  const [toasts, setToasts] = useState([]);

  const showToast = React.useCallback((message, type = 'success') => {
    const id = Date.now();
    setToasts(t => [...t, { id, message, type }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3500);
  }, []);

  return (
    <div className="App">
      <ToastContainer toasts={toasts} />
      <Header currentView={currentView} setCurrentView={setCurrentView} chatOpen={chatOpen} setChatOpen={setChatOpen} />
      <UsageBanner />
      <div style={{ display: 'flex', position: 'relative' }}>
        <main className="main-content" style={{ flex: 1, minWidth: 0 }}>
          {currentView === 'dashboard' && <Dashboard onNavigate={setCurrentView} />}
          {currentView === 'rules' && <RuleLibrary />}
          {currentView === 'subjects' && (
            <SubjectList onSelectSubject={(id) => {
              setSelectedSubject(id);
              setCurrentView('subject-detail');
            }} />
          )}
          {currentView === 'subject-detail' && selectedSubject && (
            <SubjectDashboard
              subjectId={selectedSubject}
              onBack={() => setCurrentView('subjects')}
            />
          )}
          {currentView === 'violations' && <ViolationsDashboard />}
          {currentView === 'execute' && <RuleExecutor onNavigate={setCurrentView} />}
          {currentView === 'results' && <ResultsViewer />}
          {currentView === 'site' && (
            <SiteMonitoring
              onNavigate={setCurrentView}
              onSelectSubject={(id) => { setSelectedSubject(id); setCurrentView('subject-detail'); }}
              onContextChange={setChatContext}
              showToast={showToast}
            />
          )}
        </main>
        {chatOpen && (
          <CopilotPanel
            context={chatContext}
            onClose={() => setChatOpen(false)}
          />
        )}
      </div>
    </div>
  );
}

// Header with Navigation
function Header({ currentView, setCurrentView, chatOpen, setChatOpen }) {
  const navItems = [
    { id: 'dashboard', label: '📊 Dashboard', icon: '📊' },
    { id: 'subjects', label: '👥 Subjects', icon: '👥' },
    { id: 'rules', label: '📋 Rules', icon: '📋' },
    { id: 'execute', label: '▶️ Execute', icon: '▶️' },
    { id: 'results', label: '📁 Results', icon: '📁' },
    { id: 'violations', label: '🚨 Violations', icon: '🚨' },
    { id: 'site', label: '📍 My Sites', icon: '📍' }
  ];

  return (
    <header className="header">
      <div className="header-title">
        <h1>🏥 Clinical Trial Monitor — AI Powered</h1>
        <p className="subtitle">Protocol NVX-1218.22</p>
      </div>
      
      <nav className="nav">
        {navItems.map(item => (
          <button
            key={item.id}
            className={`nav-button ${currentView === item.id ? 'active' : ''}`}
            onClick={() => setCurrentView(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </button>
        ))}
        <button
          onClick={() => setChatOpen(o => !o)}
          style={{
            marginLeft: '12px', background: chatOpen ? '#1d4ed8' : '#2563eb',
            color: 'white', border: 'none', borderRadius: '8px',
            padding: '6px 14px', cursor: 'pointer', fontWeight: 600,
            fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px',
            boxShadow: chatOpen ? 'inset 0 2px 4px rgba(0,0,0,0.2)' : 'none',
            whiteSpace: 'nowrap'
          }}
        >
          💬 Copilot
        </button>
      </nav>
    </header>
  );
}

// Dashboard - Overview
function Dashboard({ onNavigate }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  React.useEffect(() => {
    fetch('/api/statistics')
      .then(res => res.json())
      .then(data => {
        setStats(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="dashboard">
      <h2>System Overview</h2>
      
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{stats?.subjects || 0}</div>
          <div className="stat-label">Total Subjects</div>
        </div>

        <div className="stat-card">
          <div className="stat-value">{stats?.subjects_enrolled || 0}</div>
          <div className="stat-label">Enrolled</div>
        </div>

        <div className="stat-card">
          <div className="stat-value">{stats?.adverse_events || 0}</div>
          <div className="stat-label">Adverse Events</div>
        </div>

        <div className="stat-card">
          <div className="stat-value">{stats?.serious_adverse_events || 0}</div>
          <div className="stat-label">Serious AEs</div>
        </div>

        <div className="stat-card">
          <div className="stat-value">{stats?.open_queries || 0}</div>
          <div className="stat-label">Open Queries</div>
        </div>

        <div className="stat-card">
          <div className="stat-value">{stats?.protocol_deviations || 0}</div>
          <div className="stat-label">Deviations</div>
        </div>
      </div>

      <div className="quick-actions">
        <h3>Quick Actions</h3>
        <div className="actions-grid">
          <ActionCard
            title="Execute Rules"
            description="Run all active rules for subjects"
            icon="▶️"
            action="execute"
            onNavigate={onNavigate}
          />
          <ActionCard
            title="View Violations"
            description="Review flagged issues"
            icon="🚨"
            action="violations"
            onNavigate={onNavigate}
          />
          <ActionCard
            title="Manage Rules"
            description="Configure and edit rules"
            icon="📋"
            action="rules"
            onNavigate={onNavigate}
          />
        </div>
      </div>
    </div>
  );
}

function ActionCard({ title, description, icon, action, onNavigate }) {
  return (
    <div className="action-card" onClick={() => onNavigate && onNavigate(action)}
      style={{ cursor: 'pointer' }}>
      <div className="action-icon">{icon}</div>
      <h4>{title}</h4>
      <p>{description}</p>
    </div>
  );
}

// Rule Library - View/Manage Rules
function RuleLibrary() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');

  React.useEffect(() => {
    fetch('/api/rules')
      .then(res => res.json())
      .then(data => {
        setRules(data.rules || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // Category metadata for display
  const categoryMeta = {
    exclusion:      { label: 'Exclusion',   emoji: '🚫', color: '#dc2626' },
    inclusion:      { label: 'Inclusion',   emoji: '✅', color: '#16a34a' },
    safety_ae:      { label: 'AE Safety',   emoji: '⚠️', color: '#ea580c' },
    safety_lab:     { label: 'Lab Safety',  emoji: '🧪', color: '#0891b2' },
    protocol_visit: { label: 'Deviations',  emoji: '📅', color: '#7c3aed' },
    protocol_dose:  { label: 'Deviations',  emoji: '📅', color: '#7c3aed' },
    efficacy:       { label: 'Endpoints',   emoji: '📊', color: '#0369a1' },
  };

  // Unique categories present in loaded rules, mapped to display groups
  const categoryGroups = [
    { key: 'all',           label: 'All',         emoji: '📋' },
    { key: 'exclusion',     label: 'Exclusion',   emoji: '🚫' },
    { key: 'inclusion',     label: 'Inclusion',   emoji: '✅' },
    { key: 'safety',        label: 'AE Safety',   emoji: '⚠️' },
    { key: 'lab',           label: 'Lab Safety',  emoji: '🧪' },
    { key: 'deviation',     label: 'Deviations',  emoji: '📅' },
    { key: 'efficacy',      label: 'Endpoints',   emoji: '📊' },
  ];

  const matchesCategory = (rule, catKey) => {
    if (catKey === 'all') return true;
    if (catKey === 'exclusion') return rule.category === 'exclusion';
    if (catKey === 'inclusion') return rule.category === 'inclusion';
    if (catKey === 'safety') return rule.category === 'safety_ae';
    if (catKey === 'lab') return rule.category === 'safety_lab';
    if (catKey === 'deviation') return rule.category === 'protocol_visit' || rule.category === 'protocol_dose';
    if (catKey === 'efficacy') return rule.category === 'efficacy';
    return false;
  };

  const filteredRules = rules.filter(r => {
    const statusOk = statusFilter === 'all' || r.status === statusFilter;
    const catOk = matchesCategory(r, categoryFilter);
    return statusOk && catOk;
  });

  const countFor = (catKey) => rules.filter(r => matchesCategory(r, catKey)).length;

  if (loading) return <div className="loading">Loading rules...</div>;

  const btnBase = { padding: '5px 14px', borderRadius: '20px', border: '1.5px solid', cursor: 'pointer', fontWeight: 600, fontSize: '13px', transition: 'all 0.15s' };

  return (
    <div className="rule-library">
      <div className="library-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 style={{ margin: 0 }}>Rule Library</h2>
            <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: '14px' }}>
              {rules.filter(r => r.status === 'active').length} active rules across {Object.keys(categoryMeta).filter(c => rules.some(r => r.category === c)).length} categories
            </p>
          </div>
          {/* Status filter */}
          <div className="filters" style={{ alignSelf: 'flex-start' }}>
            {[['all', 'All'], ['active', 'Active'], ['inactive', 'Inactive']].map(([val, label]) => (
              <button key={val}
                className={statusFilter === val ? 'active' : ''}
                onClick={() => setStatusFilter(val)}>
                {label} ({val === 'all' ? rules.length : rules.filter(r => r.status === val).length})
              </button>
            ))}
          </div>
        </div>

        {/* Category filter row */}
        <div style={{ display: 'flex', gap: '8px', marginTop: '14px', flexWrap: 'wrap' }}>
          {categoryGroups.map(({ key, label, emoji }) => {
            const count = countFor(key);
            const active = categoryFilter === key;
            const colors = {
              all: '#374151', exclusion: '#dc2626', inclusion: '#16a34a',
              safety: '#ea580c', lab: '#0891b2', deviation: '#7c3aed', efficacy: '#0369a1'
            };
            const c = colors[key] || '#374151';
            return (
              <button key={key} onClick={() => setCategoryFilter(key)} style={{
                ...btnBase,
                background: active ? c : 'white',
                color: active ? 'white' : c,
                borderColor: c,
                opacity: count === 0 ? 0.4 : 1,
              }}>
                {emoji} {label} <span style={{ opacity: 0.8, fontWeight: 400 }}>({count})</span>
              </button>
            );
          })}
        </div>
      </div>

      {filteredRules.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
          No rules match the selected filters.
        </div>
      ) : (
        <div className="rules-list" style={{ marginTop: '16px' }}>
          {filteredRules.map(rule => (
            <RuleCard key={rule.rule_id} rule={rule} categoryMeta={categoryMeta} />
          ))}
        </div>
      )}
    </div>
  );
}

function RuleCard({ rule, categoryMeta = {} }) {
  const [expanded, setExpanded] = useState(false);
  const [template, setTemplate] = useState(null);
  const [templateVisible, setTemplateVisible] = useState(false);
  const [templateLoading, setTemplateLoading] = useState(false);
  const [templateError, setTemplateError] = useState(null);
  const [sampleInput, setSampleInput] = useState(null);
  const [sampleVisible, setSampleVisible] = useState(false);
  const [sampleLoading, setSampleLoading] = useState(false);
  const [sampleError, setSampleError] = useState(null);

  const severityColor = {
    critical: '#dc2626',
    major: '#f59e0b',
    minor: '#10b981',
    info: '#64748b',
  };

  const typeColor = {
    llm_with_tools: '#7c3aed',
    deterministic: '#0369a1'
  };

  const cat = categoryMeta[rule.category] || { label: rule.category, emoji: '📋', color: '#64748b' };

  const handleViewSampleInput = (e) => {
    e.stopPropagation();
    if (sampleVisible) { setSampleVisible(false); return; }
    if (sampleInput) { setSampleVisible(true); return; }
    setSampleLoading(true);
    setSampleError(null);
    fetch(`/api/templates/${rule.template_name}/sample-input?subject_id=101-001`)
      .then(res => {
        if (!res.ok) throw new Error(`Template sample not available (${res.status})`);
        return res.json();
      })
      .then(data => {
        if (data.detail) throw new Error(data.detail);
        setSampleInput(data);
        setSampleVisible(true);
        setSampleLoading(false);
      })
      .catch(err => {
        setSampleError(err.message || 'Sample input not available for this template.');
        setSampleVisible(true);
        setSampleLoading(false);
      });
  };

  const handleViewTemplate = (e) => {
    e.stopPropagation();
    if (templateVisible) {
      setTemplateVisible(false);
      setTemplateError(null);
      return;
    }
    if (template) {
      setTemplateVisible(true);
      return;
    }
    setTemplateLoading(true);
    setTemplateError(null);
    // Try the canonical key (uppercase), then the raw template_name
    const templateKey = rule.template_name;
    fetch(`/api/templates/${templateKey}`)
      .then(res => {
        if (!res.ok) throw new Error(`Template "${templateKey}" not found (${res.status})`);
        return res.json();
      })
      .then(data => {
        if (data.detail) throw new Error(data.detail);
        // API may return the template nested under the key name
        const tpl = data[templateKey] || data;
        setTemplate(tpl);
        setTemplateVisible(true);
        setTemplateLoading(false);
      })
      .catch(err => {
        setTemplateError(err.message || 'Template details not available.');
        setTemplateVisible(true);
        setTemplateLoading(false);
      });
  };

  return (
    <div className="rule-card">
      <div className="rule-header" onClick={() => setExpanded(!expanded)}>
        <div className="rule-info">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
            <span style={{
              display: 'inline-block', padding: '1px 8px', borderRadius: '10px', fontSize: '11px',
              fontWeight: 700, color: cat.color, background: cat.color + '18', border: `1px solid ${cat.color}44`,
              whiteSpace: 'nowrap'
            }}>
              {cat.emoji} {cat.label}
            </span>
            <h3 style={{ margin: 0 }}>{rule.rule_id}: {rule.name}</h3>
          </div>
          <p className="rule-description">{rule.description}</p>
        </div>

        <div className="rule-meta">
          <span
            className="severity-badge"
            style={{ backgroundColor: severityColor[rule.severity] || '#64748b' }}
          >
            {rule.severity}
          </span>
          <span className={`status-badge ${rule.status}`}>
            {rule.status}
          </span>
          <span className="complexity-badge">{rule.complexity}</span>
        </div>
      </div>

      {expanded && (
        <div className="rule-details">
          <div className="detail-row">
            <strong>Category:</strong> {cat.emoji} {cat.label} <span style={{ color: '#94a3b8', fontSize: '12px' }}>({rule.category})</span>
          </div>
          <div className="detail-row">
            <strong>Evaluation Type:</strong>{' '}
            <span style={{ color: typeColor[rule.evaluation_type] || '#374151', fontWeight: 600 }}>
              {rule.evaluation_type === 'llm_with_tools' ? '🤖 LLM + Tools' : '⚙️ Deterministic'}
            </span>
          </div>
          <div className="detail-row">
            <strong>Template:</strong> {rule.template_name}
            <button
              onClick={handleViewTemplate}
              style={{
                marginLeft: '10px',
                padding: '2px 10px',
                fontSize: '12px',
                background: templateVisible ? '#e5e7eb' : '#2563eb',
                color: templateVisible ? '#374151' : 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              {templateLoading ? '...' : templateVisible ? 'Hide Template' : 'View Template'}
            </button>
          </div>
          {rule.protocol_reference && (
            <div className="detail-row">
              <strong>Protocol Reference:</strong> {rule.protocol_reference}
            </div>
          )}

          <div className="detail-row">
            <strong>Sample Input:</strong>
            <button
              onClick={handleViewSampleInput}
              style={{
                marginLeft: '10px',
                padding: '2px 10px',
                fontSize: '12px',
                background: sampleVisible ? '#e5e7eb' : '#059669',
                color: sampleVisible ? '#374151' : 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              {sampleLoading ? '...' : sampleVisible ? 'Hide Input' : 'View Sample Input'}
            </button>
            <span style={{ marginLeft: '8px', fontSize: '12px', color: '#94a3b8' }}>
              (using subject 101-001)
            </span>
          </div>

          {sampleVisible && (
            <div style={{
              marginTop: '14px',
              background: sampleError ? '#fff7ed' : '#f0fdf4',
              border: `1px solid ${sampleError ? '#fed7aa' : '#bbf7d0'}`,
              borderRadius: '8px',
              padding: '16px'
            }}>
              {sampleError ? (
                <p style={{ margin: 0, color: '#9a3412', fontSize: '13px' }}>
                  ⚠️ {sampleError}
                </p>
              ) : sampleInput && (
                <>
                  <h4 style={{ margin: '0 0 6px', color: '#14532d' }}>
                    🔬 Sample Input — {sampleInput.template}
                  </h4>
                  <p style={{ color: '#166534', fontSize: '13px', marginBottom: '10px' }}>
                    {sampleInput.description}
                  </p>
                  <pre style={{
                    background: '#1e293b', color: '#e2e8f0', padding: '14px',
                    borderRadius: '6px', fontSize: '12px', overflowX: 'auto',
                    whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                    maxHeight: '400px', overflowY: 'auto'
                  }}>
                    {JSON.stringify(sampleInput.input, null, 2)}
                  </pre>
                </>
              )}
            </div>
          )}

          {templateVisible && (
            <div style={{
              marginTop: '14px',
              background: templateError ? '#fff7ed' : '#f8fafc',
              border: `1px solid ${templateError ? '#fed7aa' : '#e2e8f0'}`,
              borderRadius: '8px',
              padding: '16px'
            }}>
              {templateError ? (
                <p style={{ margin: 0, color: '#9a3412', fontSize: '13px' }}>
                  ⚠️ {templateError}
                </p>
              ) : template && (
                <>
                  <h4 style={{ margin: '0 0 10px', color: '#1e293b' }}>
                    📄 {template.name || rule.template_name}
                  </h4>
                  {template.description && (
                    <p style={{ color: '#475569', marginBottom: '12px', fontSize: '14px' }}>
                      {template.description}
                    </p>
                  )}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    {template.suitable_for && (
                      <div>
                        <strong style={{ fontSize: '13px', color: '#64748b' }}>✅ Suitable For</strong>
                        <ul style={{ margin: '6px 0 0', paddingLeft: '16px', fontSize: '13px' }}>
                          {template.suitable_for.map((s, i) => <li key={i}>{s}</li>)}
                        </ul>
                      </div>
                    )}
                    {template.tools_available && (
                      <div>
                        <strong style={{ fontSize: '13px', color: '#64748b' }}>🔧 Tools Available</strong>
                        <ul style={{ margin: '6px 0 0', paddingLeft: '16px', fontSize: '13px', fontFamily: 'monospace' }}>
                          {template.tools_available.map((t, i) => <li key={i}>{t}</li>)}
                        </ul>
                      </div>
                    )}
                    {template.output_fields && (
                      <div>
                        <strong style={{ fontSize: '13px', color: '#64748b' }}>📤 Output Fields</strong>
                        <div style={{ marginTop: '6px', display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                          {template.output_fields.map((f, i) => (
                            <span key={i} style={{
                              background: '#e0f2fe', color: '#0369a1',
                              borderRadius: '4px', padding: '2px 7px', fontSize: '12px'
                            }}>{f}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    {template.phase_logic && (
                      <div>
                        <strong style={{ fontSize: '13px', color: '#64748b' }}>🔄 Phase Logic</strong>
                        <div style={{ marginTop: '6px', fontSize: '13px' }}>
                          {Object.entries(template.phase_logic).map(([phase, logic]) => (
                            <div key={phase} style={{ marginBottom: '4px' }}>
                              <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>{phase}:</span> {logic}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Subject List
function SubjectList({ onSelectSubject }) {
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);

  React.useEffect(() => {
    fetch('/api/subjects')
      .then(res => res.json())
      .then(data => {
        setSubjects(data);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="loading">Loading subjects...</div>;

  return (
    <div className="subject-list">
      <h2>Study Subjects</h2>
      
      <table className="subjects-table">
        <thead>
          <tr>
            <th>Subject ID</th>
            <th>Site</th>
            <th>Treatment Arm</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {subjects.map(subject => (
            <tr key={subject.subject_id}>
              <td>{subject.subject_id}</td>
              <td>{subject.site_id}</td>
              <td>{subject.treatment_arm_name}</td>
              <td>
                <span className={`status-badge ${subject.study_status.toLowerCase()}`}>
                  {subject.study_status}
                </span>
              </td>
              <td>
                <button 
                  className="view-button"
                  onClick={() => onSelectSubject(subject.subject_id)}
                >
                  View Details
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Subject Dashboard — 6-tab CRA workspace ────────────────────────────────
function SubjectDashboard({ subjectId, onBack }) {
  const [activeTab, setActiveTab] = useState('overview');
  const [subject, setSubject] = useState(null);
  const [demo, setDemo] = useState(null);
  const [medHistory, setMedHistory] = useState([]);
  const [visits, setVisits] = useState([]);
  const [labs, setLabs] = useState([]);
  const [aes, setAes] = useState([]);
  const [conmeds, setConmeds] = useState([]);
  const [violations, setViolations] = useState(null);
  const [loading, setLoading] = useState(true);

  React.useEffect(() => {
    Promise.all([
      fetch(`/api/subjects/${subjectId}`).then(r => r.json()),
      fetch(`/api/demographics/${subjectId}`).then(r => r.json()).catch(() => ({})),
      fetch(`/api/medical-history/${subjectId}`).then(r => r.json()).catch(() => []),
    ]).then(([s, d, mh]) => {
      setSubject(s); setDemo(d);
      setMedHistory(Array.isArray(mh) ? mh : mh.medical_history || []);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [subjectId]);

  // Lazy-load tabs
  const loadTab = (tab) => {
    setActiveTab(tab);
    if (tab === 'visits' && visits.length === 0)
      fetch(`/api/subjects/${subjectId}/visits`).then(r => r.json()).then(d => setVisits(d.visits || [])).catch(() => {});
    if (tab === 'labs' && labs.length === 0)
      fetch(`/api/labs/${subjectId}`).then(r => r.json()).then(d => setLabs(Array.isArray(d) ? d : d.labs || [])).catch(() => {});
    if (tab === 'aes' && aes.length === 0)
      fetch(`/api/adverse-events?subject_id=${subjectId}`).then(r => r.json()).then(d => setAes(Array.isArray(d) ? d : [])).catch(() => {});
    if (tab === 'conmeds' && conmeds.length === 0)
      fetch(`/api/conmeds/${subjectId}`).then(r => r.json()).then(d => setConmeds(Array.isArray(d) ? d : d.conmeds || [])).catch(() => {});
    if (tab === 'violations' && !violations)
      fetch(`/api/subjects/${subjectId}/violations`).then(r => r.json()).then(setViolations).catch(() => setViolations({ violations: [], violations_found: 0 }));
  };

  const sevColor = { critical: '#dc2626', major: '#f59e0b', minor: '#10b981', info: '#64748b' };
  const tabs = [
    { id: 'overview', label: '📋 Overview' },
    { id: 'visits',   label: '🗓 Visits' },
    { id: 'labs',     label: '🧪 Labs' },
    { id: 'aes',      label: '⚠️ Adverse Events' },
    { id: 'conmeds',  label: '💊 Conmeds' },
    { id: 'violations', label: '🚨 Violations' },
  ];

  if (loading) return <div className="loading">Loading subject {subjectId}...</div>;

  return (
    <div style={{ padding: '0' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <button onClick={onBack} style={{ padding: '6px 14px', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: '6px', cursor: 'pointer', fontSize: '13px' }}>
          ← Back
        </button>
        <div>
          <h2 style={{ margin: 0, fontSize: '20px' }}>Subject {subjectId}</h2>
          <div style={{ fontSize: '13px', color: '#64748b', marginTop: '2px' }}>
            {subject?.treatment_arm_name} &nbsp;·&nbsp;
            <span style={{ fontWeight: 600, color: subject?.study_status === 'Discontinued' ? '#dc2626' : subject?.study_status === 'Active' ? '#16a34a' : '#374151' }}>
              {subject?.study_status}
            </span>
            &nbsp;·&nbsp; Site {subject?.site_id}
          </div>
        </div>
      </div>

      {/* Tab bar */}
      <div style={{ display: 'flex', gap: '0', borderBottom: '2px solid #e2e8f0', marginBottom: '20px', flexWrap: 'wrap' }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => loadTab(t.id)} style={{
            padding: '9px 18px', border: 'none', cursor: 'pointer', fontSize: '13px', fontWeight: 600,
            background: 'transparent',
            borderBottom: activeTab === t.id ? '2px solid #2563eb' : '2px solid transparent',
            color: activeTab === t.id ? '#2563eb' : '#64748b',
            marginBottom: '-2px'
          }}>{t.label}</button>
        ))}
      </div>

      {/* ── OVERVIEW ── */}
      {activeTab === 'overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          {/* Demographics */}
          <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px' }}>
            <h3 style={{ margin: '0 0 12px', fontSize: '15px', color: '#1e293b' }}>👤 Demographics</h3>
            {[
              ['Age', demo?.age ? `${demo.age} years` : '—'],
              ['Sex', demo?.sex || '—'],
              ['Race / Ethnicity', [demo?.race, demo?.ethnicity].filter(Boolean).join(' / ') || '—'],
              ['Weight / BMI', demo?.weight_kg ? `${demo.weight_kg} kg / BMI ${demo?.bmi}` : '—'],
              ['ECOG Status', demo?.ecog_performance_status !== undefined ? `PS ${demo.ecog_performance_status}` : '—'],
              ['Smoking', demo?.smoking_status ? `${demo.smoking_status}${demo.smoking_pack_years ? ` (${demo.smoking_pack_years} pack-yrs)` : ''}` : '—'],
            ].map(([k, v]) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', borderBottom: '1px solid #f1f5f9', fontSize: '13px' }}>
                <span style={{ color: '#64748b' }}>{k}</span>
                <span style={{ fontWeight: 600 }}>{v}</span>
              </div>
            ))}
          </div>

          {/* Study info */}
          <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px' }}>
            <h3 style={{ margin: '0 0 12px', fontSize: '15px', color: '#1e293b' }}>📋 Study Information</h3>
            {[
              ['Subject ID', subjectId],
              ['Site', subject?.site_id || '—'],
              ['Treatment Arm', subject?.treatment_arm_name || '—'],
              ['Status', subject?.study_status || '—'],
              ['Screening Date', subject?.screening_date || '—'],
              ['Randomization Date', subject?.randomization_date || '—'],
              ['Discontinuation Date', subject?.discontinuation_date || '—'],
              ['Discontinuation Reason', subject?.discontinuation_reason || '—'],
            ].map(([k, v]) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', borderBottom: '1px solid #f1f5f9', fontSize: '13px' }}>
                <span style={{ color: '#64748b' }}>{k}</span>
                <span style={{ fontWeight: 600, textAlign: 'right', maxWidth: '55%' }}>{v}</span>
              </div>
            ))}
          </div>

          {/* Medical History */}
          <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px', gridColumn: '1 / -1' }}>
            <h3 style={{ margin: '0 0 12px', fontSize: '15px', color: '#1e293b' }}>🏥 Medical History ({medHistory.length})</h3>
            {medHistory.length === 0 ? <p style={{ color: '#94a3b8', fontSize: '13px' }}>None recorded</p> : (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ background: '#f8fafc' }}>
                    {['Condition', 'Category', 'Diagnosis Date', 'Status', 'Notes'].map(h => (
                      <th key={h} style={{ padding: '8px 10px', textAlign: 'left', border: '1px solid #e2e8f0', color: '#475569' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {medHistory.map((m, i) => (
                    <tr key={i} style={{ background: i % 2 === 0 ? 'white' : '#f8fafc' }}>
                      <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0', fontWeight: 600 }}>{m.condition}</td>
                      <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0', color: '#7c3aed' }}>{m.condition_category}</td>
                      <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0' }}>{m.diagnosis_date || '—'}</td>
                      <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0' }}>
                        <span style={{ padding: '2px 7px', borderRadius: '99px', fontSize: '11px', fontWeight: 700,
                          background: m.ongoing ? '#fee2e2' : '#dcfce7', color: m.ongoing ? '#dc2626' : '#16a34a' }}>
                          {m.ongoing ? 'Ongoing' : 'Resolved'}
                        </span>
                      </td>
                      <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0', color: '#64748b', fontSize: '12px' }}>{m.condition_notes || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* ── VISITS ── */}
      {activeTab === 'visits' && (
        <div>
          {visits.length === 0 ? <div className="loading">Loading visits...</div> : visits.map((v, vi) => (
            <VisitAccordion key={vi} visit={v} />
          ))}
        </div>
      )}

      {/* ── LABS ── */}
      {activeTab === 'labs' && <LabsTable labs={labs} />}

      {/* ── ADVERSE EVENTS ── */}
      {activeTab === 'aes' && <AETable aes={aes} />}

      {/* ── CONMEDS ── */}
      {activeTab === 'conmeds' && <ConmedsTable conmeds={conmeds} />}

      {/* ── VIOLATIONS ── */}
      {activeTab === 'violations' && (
        <div>
          {!violations ? (
            <div className="loading">Loading violations...</div>
          ) : violations.violations_found === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px', color: '#16a34a', fontSize: '16px' }}>
              ✅ No violations found for this subject in the latest evaluation run.
              {!violations.job_id && <p style={{ color: '#94a3b8', fontSize: '13px', marginTop: '8px' }}>No evaluation has been run yet. Go to Execute to run rules.</p>}
            </div>
          ) : (
            <>
              <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', flexWrap: 'wrap' }}>
                {[['Total', violations.violations_found, '#374151'],
                  ['Critical', violations.violations.filter(v => v.severity === 'critical').length, '#dc2626'],
                  ['Major', violations.violations.filter(v => v.severity === 'major').length, '#f59e0b'],
                  ['Minor', violations.violations.filter(v => v.severity === 'minor').length, '#10b981']
                ].map(([label, count, color]) => (
                  <div key={label} className="stat-card" style={{ minWidth: '80px', flex: 1 }}>
                    <div className="stat-value" style={{ color }}>{count}</div>
                    <div className="stat-label">{label}</div>
                  </div>
                ))}
                {violations.run_date && (
                  <div style={{ fontSize: '12px', color: '#94a3b8', alignSelf: 'center', marginLeft: 'auto' }}>
                    Last run: {violations.run_date?.substring(0, 19)}
                  </div>
                )}
              </div>
              {violations.violations.map((v, i) => (
                <div key={i} style={{
                  border: `1px solid ${sevColor[v.severity] || '#e2e8f0'}33`,
                  borderLeft: `4px solid ${sevColor[v.severity] || '#94a3b8'}`,
                  borderRadius: '6px', padding: '14px', marginBottom: '10px', background: 'white'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '14px' }}>{v.rule_id}</span>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <span style={{ padding: '2px 8px', borderRadius: '99px', fontSize: '11px', fontWeight: 700, background: sevColor[v.severity] || '#94a3b8', color: 'white' }}>{v.severity}</span>
                      <span style={{ padding: '2px 8px', borderRadius: '99px', fontSize: '11px', background: '#ede9fe', color: '#6d28d9', fontWeight: 600 }}>{v.action_required}</span>
                    </div>
                  </div>
                  {v.evidence && v.evidence.length > 0 && (
                    <ul style={{ margin: '0 0 8px', paddingLeft: '18px', fontSize: '12px', color: '#374151' }}>
                      {v.evidence.map((e, ei) => <li key={ei}>{e}</li>)}
                    </ul>
                  )}
                  <div style={{ fontSize: '12px', color: '#64748b', background: '#f8fafc', padding: '8px 10px', borderRadius: '4px', lineHeight: 1.5 }}>
                    {v.reasoning}
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Visit Accordion ──────────────────────────────────────────────────────────
function VisitAccordion({ visit }) {
  const [open, setOpen] = useState(false);
  const isLate = visit.actual_date && visit.scheduled_date && visit.actual_date > visit.scheduled_date &&
    Math.abs((new Date(visit.actual_date) - new Date(visit.scheduled_date)) / 86400000) > (visit.window_upper_days || 3);
  const isMissed = visit.missed_visit;

  return (
    <div style={{ border: `1px solid ${isMissed ? '#fca5a5' : isLate ? '#fde68a' : '#e2e8f0'}`, borderRadius: '8px', marginBottom: '8px', overflow: 'hidden' }}>
      <div onClick={() => setOpen(!open)} style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '12px 16px', cursor: 'pointer',
        background: isMissed ? '#fff5f5' : isLate ? '#fffbeb' : '#f8fafc'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontWeight: 700, fontSize: '14px', color: '#1e293b' }}>{visit.visit_name}</span>
          {isMissed && <span style={{ fontSize: '11px', background: '#fee2e2', color: '#dc2626', padding: '1px 7px', borderRadius: '99px', fontWeight: 700 }}>MISSED</span>}
          {isLate && !isMissed && <span style={{ fontSize: '11px', background: '#fef3c7', color: '#d97706', padding: '1px 7px', borderRadius: '99px', fontWeight: 700 }}>LATE</span>}
          <span style={{ fontSize: '12px', color: '#64748b' }}>
            {visit.actual_date || visit.scheduled_date}
            {visit.days_from_randomization != null && ` · Day ${visit.days_from_randomization}`}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '12px', color: '#94a3b8' }}>
            {(visit.labs || []).length} labs · {(visit.vitals || []).length} vitals · {(visit.ecg || []).length} ECG
          </span>
          <span style={{ color: '#94a3b8' }}>{open ? '▲' : '▼'}</span>
        </div>
      </div>

      {open && (
        <div style={{ padding: '16px', borderTop: '1px solid #e2e8f0', background: 'white' }}>
          {/* Visit notes */}
          {visit.visit_notes && (
            <div style={{ background: '#fffbeb', border: '1px solid #fde68a', borderRadius: '6px', padding: '10px 12px', marginBottom: '14px', fontSize: '13px', color: '#92400e' }}>
              📝 <strong>Notes:</strong> {visit.visit_notes}
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            {/* Vitals */}
            {(visit.vitals || []).length > 0 && (
              <div>
                <h4 style={{ margin: '0 0 8px', fontSize: '13px', color: '#475569' }}>💓 Vitals</h4>
                {visit.vitals.map((vt, i) => (
                  <div key={i} style={{ fontSize: '12px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px' }}>
                    {vt.systolic_bp && <div>BP: <strong>{vt.systolic_bp}/{vt.diastolic_bp} mmHg</strong></div>}
                    {vt.heart_rate && <div>HR: <strong>{vt.heart_rate} bpm</strong></div>}
                    {vt.temperature_celsius && <div>Temp: <strong>{vt.temperature_celsius}°C</strong></div>}
                    {vt.oxygen_saturation && <div>SpO₂: <strong>{vt.oxygen_saturation}%</strong></div>}
                    {vt.weight_kg && <div>Weight: <strong>{vt.weight_kg} kg</strong></div>}
                    {vt.respiratory_rate && <div>RR: <strong>{vt.respiratory_rate}/min</strong></div>}
                  </div>
                ))}
              </div>
            )}

            {/* ECG */}
            {(visit.ecg || []).length > 0 && (
              <div>
                <h4 style={{ margin: '0 0 8px', fontSize: '13px', color: '#475569' }}>📈 ECG</h4>
                {visit.ecg.map((e, i) => (
                  <div key={i} style={{ fontSize: '12px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px' }}>
                    {e.qtcf_interval && (
                      <div style={{ color: e.qtcf_interval > 470 ? '#dc2626' : '#374151' }}>
                        QTcF: <strong>{e.qtcf_interval} ms{e.qtcf_interval > 470 ? ' ⚠️' : ''}</strong>
                      </div>
                    )}
                    {e.heart_rate && <div>HR: <strong>{e.heart_rate} bpm</strong></div>}
                    {e.pr_interval && <div>PR: <strong>{e.pr_interval} ms</strong></div>}
                    {e.interpretation && <div style={{ gridColumn: '1/-1', color: '#64748b' }}>{e.interpretation}</div>}
                  </div>
                ))}
              </div>
            )}

            {/* Tumor assessment */}
            {visit.tumor_assessment && (
              <div>
                <h4 style={{ margin: '0 0 8px', fontSize: '13px', color: '#475569' }}>🔬 Tumor Assessment</h4>
                <div style={{ fontSize: '12px' }}>
                  <div>Response: <strong style={{ color: visit.tumor_assessment.overall_response === 'Progressive Disease' ? '#dc2626' : visit.tumor_assessment.overall_response === 'Partial Response' ? '#16a34a' : '#374151' }}>{visit.tumor_assessment.overall_response}</strong></div>
                  {visit.tumor_assessment.target_lesion_sum != null && <div>Target sum: <strong>{visit.tumor_assessment.target_lesion_sum} mm</strong></div>}
                  {visit.tumor_assessment.new_lesions > 0 && <div style={{ color: '#dc2626' }}>New lesions: <strong>{visit.tumor_assessment.new_lesions}</strong></div>}
                  {visit.tumor_assessment.assessment_notes && <div style={{ color: '#64748b', marginTop: '4px' }}>{visit.tumor_assessment.assessment_notes}</div>}
                </div>
              </div>
            )}
          </div>

          {/* Labs */}
          {(visit.labs || []).length > 0 && (
            <div style={{ marginTop: '14px' }}>
              <h4 style={{ margin: '0 0 8px', fontSize: '13px', color: '#475569' }}>🧪 Labs ({visit.labs.length} results)</h4>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                  <thead>
                    <tr style={{ background: '#f1f5f9' }}>
                      {['Category', 'Test', 'Value', 'Unit', 'Range', 'Flag'].map(h => (
                        <th key={h} style={{ padding: '5px 8px', textAlign: 'left', border: '1px solid #e2e8f0', color: '#475569' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {visit.labs.map((lab, li) => {
                      const isH = lab.abnormal_flag === 'H' || lab.abnormal_flag === 'HH';
                      const isL = lab.abnormal_flag === 'L' || lab.abnormal_flag === 'LL';
                      const isCrit = lab.clinically_significant;
                      return (
                        <tr key={li} style={{ background: isCrit ? '#fff5f5' : li % 2 === 0 ? 'white' : '#f8fafc' }}>
                          <td style={{ padding: '4px 8px', border: '1px solid #e2e8f0', color: '#7c3aed', fontSize: '11px' }}>{lab.lab_category}</td>
                          <td style={{ padding: '4px 8px', border: '1px solid #e2e8f0', fontWeight: 600 }}>{lab.test_name}</td>
                          <td style={{ padding: '4px 8px', border: '1px solid #e2e8f0', fontWeight: 700, color: isH ? '#dc2626' : isL ? '#2563eb' : '#374151' }}>{lab.test_value}</td>
                          <td style={{ padding: '4px 8px', border: '1px solid #e2e8f0', color: '#64748b' }}>{lab.test_unit}</td>
                          <td style={{ padding: '4px 8px', border: '1px solid #e2e8f0', color: '#94a3b8' }}>
                            {lab.normal_range_lower != null && lab.normal_range_upper != null ? `${lab.normal_range_lower}–${lab.normal_range_upper}` : '—'}
                          </td>
                          <td style={{ padding: '4px 8px', border: '1px solid #e2e8f0' }}>
                            {lab.abnormal_flag ? (
                              <span style={{ fontWeight: 700, color: isH ? '#dc2626' : isL ? '#2563eb' : '#374151' }}>{lab.abnormal_flag}{isCrit ? ' ⚠️' : ''}</span>
                            ) : '—'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Labs flat table ──────────────────────────────────────────────────────────
function LabsTable({ labs }) {
  const [filter, setFilter] = useState('all');
  if (labs.length === 0) return <div className="loading">Loading labs...</div>;
  const cats = [...new Set(labs.map(l => l.lab_category))];
  const filtered = filter === 'all' ? labs : filter === 'abnormal' ? labs.filter(l => l.abnormal_flag) : labs.filter(l => l.lab_category === filter);
  return (
    <div>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '14px', flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ fontSize: '13px', color: '#64748b', fontWeight: 600 }}>Filter:</span>
        {[['all', 'All'], ['abnormal', '⚠️ Abnormal Only'], ...cats.map(c => [c, c])].map(([val, label]) => (
          <button key={val} onClick={() => setFilter(val)} style={{
            padding: '4px 12px', borderRadius: '99px', border: 'none', cursor: 'pointer', fontSize: '12px',
            background: filter === val ? '#2563eb' : '#e2e8f0',
            color: filter === val ? 'white' : '#374151', fontWeight: filter === val ? 700 : 400
          }}>{label}</button>
        ))}
        <span style={{ marginLeft: 'auto', fontSize: '12px', color: '#94a3b8' }}>{filtered.length} results</span>
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ background: '#f1f5f9' }}>
              {['Date', 'Category', 'Test', 'Value', 'Unit', 'Normal Range', 'Flag', 'CS', 'Comments'].map(h => (
                <th key={h} style={{ padding: '8px 10px', textAlign: 'left', border: '1px solid #e2e8f0', color: '#475569', whiteSpace: 'nowrap' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((lab, i) => {
              const isH = lab.abnormal_flag === 'H' || lab.abnormal_flag === 'HH';
              const isL = lab.abnormal_flag === 'L' || lab.abnormal_flag === 'LL';
              return (
                <tr key={i} style={{ background: lab.clinically_significant ? '#fff5f5' : i % 2 === 0 ? 'white' : '#f8fafc', verticalAlign: 'top' }}>
                  <td style={{ padding: '6px 10px', border: '1px solid #e2e8f0', whiteSpace: 'nowrap', color: '#64748b' }}>{lab.collection_date}</td>
                  <td style={{ padding: '6px 10px', border: '1px solid #e2e8f0', color: '#7c3aed', fontSize: '11px' }}>{lab.lab_category}</td>
                  <td style={{ padding: '6px 10px', border: '1px solid #e2e8f0', fontWeight: 600 }}>{lab.test_name}</td>
                  <td style={{ padding: '6px 10px', border: '1px solid #e2e8f0', fontWeight: 700, color: isH ? '#dc2626' : isL ? '#2563eb' : '#374151' }}>{lab.test_value}</td>
                  <td style={{ padding: '6px 10px', border: '1px solid #e2e8f0', color: '#94a3b8' }}>{lab.test_unit}</td>
                  <td style={{ padding: '6px 10px', border: '1px solid #e2e8f0', color: '#64748b' }}>
                    {lab.normal_range_lower != null ? `${lab.normal_range_lower}–${lab.normal_range_upper}` : '—'}
                  </td>
                  <td style={{ padding: '6px 10px', border: '1px solid #e2e8f0', fontWeight: 700, color: isH ? '#dc2626' : isL ? '#2563eb' : '#374151' }}>{lab.abnormal_flag || '—'}</td>
                  <td style={{ padding: '6px 10px', border: '1px solid #e2e8f0' }}>{lab.clinically_significant ? '⚠️' : '—'}</td>
                  <td style={{ padding: '6px 10px', border: '1px solid #e2e8f0', color: '#64748b', fontSize: '12px', maxWidth: '180px' }}>{lab.lab_comments || '—'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── AE Table ─────────────────────────────────────────────────────────────────
function AETable({ aes }) {
  if (aes.length === 0) return <div className="loading">Loading adverse events...</div>;
  const gradeBg = { 1: '#f0fdf4', 2: '#fefce8', 3: '#fff7ed', 4: '#fff5f5', 5: '#fef2f2' };
  const gradeColor = { 1: '#16a34a', 2: '#ca8a04', 3: '#ea580c', 4: '#dc2626', 5: '#7f1d1d' };
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
        <thead>
          <tr style={{ background: '#f1f5f9' }}>
            {['AE Term', 'CTCAE Grade', 'Onset', 'Resolution', 'Ongoing', 'SAE', 'Relationship', 'Action Taken', 'Outcome'].map(h => (
              <th key={h} style={{ padding: '8px 10px', textAlign: 'left', border: '1px solid #e2e8f0', color: '#475569', whiteSpace: 'nowrap' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {aes.map((ae, i) => (
            <tr key={i} style={{ background: gradeBg[ae.ctcae_grade] || (i % 2 === 0 ? 'white' : '#f8fafc'), verticalAlign: 'top' }}>
              <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0', fontWeight: 600 }}>{ae.ae_term}</td>
              <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0' }}>
                <span style={{ fontWeight: 700, padding: '2px 8px', borderRadius: '99px', background: gradeBg[ae.ctcae_grade] || '#f1f5f9', color: gradeColor[ae.ctcae_grade] || '#374151', border: `1px solid ${gradeColor[ae.ctcae_grade] || '#e2e8f0'}` }}>
                  Grade {ae.ctcae_grade}
                </span>
              </td>
              <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0', whiteSpace: 'nowrap' }}>{ae.onset_date || '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0', whiteSpace: 'nowrap' }}>{ae.resolution_date || '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0' }}>{ae.ongoing ? '✅' : '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0' }}>
                <span style={{ fontWeight: 700, color: ae.seriousness && ae.seriousness !== 'No' ? '#dc2626' : '#16a34a' }}>
                  {ae.seriousness && ae.seriousness !== 'No' ? '⚠️ SAE' : 'No'}
                </span>
              </td>
              <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0', color: '#64748b' }}>{ae.relationship_to_study_drug || '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0', color: '#64748b' }}>{ae.action_taken || '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0', color: '#64748b' }}>{ae.outcome || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Conmeds Table ────────────────────────────────────────────────────────────
function ConmedsTable({ conmeds }) {
  if (conmeds.length === 0) return <div className="loading">Loading concomitant medications...</div>;
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
        <thead>
          <tr style={{ background: '#f1f5f9' }}>
            {['Medication', 'Class', 'Indication', 'Dose', 'Frequency', 'Route', 'Start Date', 'End Date', 'Ongoing'].map(h => (
              <th key={h} style={{ padding: '8px 10px', textAlign: 'left', border: '1px solid #e2e8f0', color: '#475569', whiteSpace: 'nowrap' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {conmeds.map((c, i) => (
            <tr key={i} style={{ background: c.ongoing ? '#f0fdf4' : i % 2 === 0 ? 'white' : '#f8fafc', verticalAlign: 'top' }}>
              <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0', fontWeight: 600 }}>{c.medication_name}</td>
              <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0', color: '#7c3aed', fontSize: '12px' }}>{c.medication_class || '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0', color: '#64748b' }}>{c.indication || '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0', fontWeight: 600 }}>{c.dose ? `${c.dose} ${c.dose_unit || ''}` : '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0' }}>{c.frequency || '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0', color: '#64748b' }}>{c.route || '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0', whiteSpace: 'nowrap' }}>{c.start_date || '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0', whiteSpace: 'nowrap' }}>{c.end_date || '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid #e2e8f0' }}>
                <span style={{ fontWeight: 700, color: c.ongoing ? '#16a34a' : '#64748b' }}>{c.ongoing ? '✅ Yes' : 'No'}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Global Violations Dashboard ─────────────────────────────────────────────
function ViolationsDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [filterSubject, setFilterSubject] = useState('');
  const [filterRule, setFilterRule] = useState('all');
  const [expandedIdx, setExpandedIdx] = useState(null);

  React.useEffect(() => {
    fetch('/api/violations')
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading violations...</div>;
  if (!data) return <div style={{ padding: '40px', color: '#94a3b8' }}>Could not load violations.</div>;

  const sevColor = { critical: '#dc2626', major: '#f59e0b', minor: '#10b981', info: '#64748b' };
  const allV = data.violations || [];

  const filtered = allV.filter(v => {
    const sevOk = filterSeverity === 'all' || v.severity === filterSeverity;
    const subOk = !filterSubject || v.subject_id?.toLowerCase().includes(filterSubject.toLowerCase());
    const ruleOk = filterRule === 'all' || v.rule_id === filterRule;
    return sevOk && subOk && ruleOk;
  });

  const uniqueRules = [...new Set(allV.map(v => v.rule_id))].sort();

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ margin: 0 }}>🚨 Violations Dashboard</h2>
          <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: '14px' }}>
            All study violations across {data.unique_subjects} subject(s) · {data.unique_rules} rules flagged
          </p>
        </div>
        <button onClick={() => { setLoading(true); fetch('/api/violations').then(r => r.json()).then(d => { setData(d); setLoading(false); }); }}
          style={{ padding: '6px 14px', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: '6px', cursor: 'pointer', fontSize: '13px' }}>
          🔄 Refresh
        </button>
      </div>

      {/* Summary cards */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', flexWrap: 'wrap' }}>
        {[
          ['Total', data.summary.total, '#374151', 'all'],
          ['Critical', data.summary.critical, '#dc2626', 'critical'],
          ['Major', data.summary.major, '#f59e0b', 'major'],
          ['Minor', data.summary.minor, '#10b981', 'minor'],
          ['Info', data.summary.info, '#64748b', 'info'],
        ].map(([label, count, color, sev]) => (
          <div key={label} onClick={() => setFilterSeverity(filterSeverity === sev ? 'all' : sev)}
            className="stat-card" style={{ flex: 1, minWidth: '80px', cursor: 'pointer', border: `2px solid ${filterSeverity === sev ? color : '#e2e8f0'}` }}>
            <div className="stat-value" style={{ color }}>{count}</div>
            <div className="stat-label">{label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
        <input type="text" placeholder="Search subject ID..." value={filterSubject}
          onChange={e => setFilterSubject(e.target.value)}
          style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid #e2e8f0', fontSize: '13px', width: '160px' }} />
        <select value={filterRule} onChange={e => setFilterRule(e.target.value)}
          style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid #e2e8f0', fontSize: '13px' }}>
          <option value="all">All Rules</option>
          {uniqueRules.map(r => <option key={r} value={r}>{r}</option>)}
        </select>
        <span style={{ fontSize: '13px', color: '#64748b' }}>{filtered.length} of {allV.length} violations</span>
      </div>

      {/* Violations list */}
      {filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px', color: '#16a34a', fontSize: '16px' }}>
          ✅ No violations match the current filters
        </div>
      ) : (
        filtered.map((v, i) => (
          <div key={i} style={{
            border: `1px solid ${sevColor[v.severity] || '#e2e8f0'}44`,
            borderLeft: `4px solid ${sevColor[v.severity] || '#94a3b8'}`,
            borderRadius: '6px', marginBottom: '8px', overflow: 'hidden'
          }}>
            {/* Row header */}
            <div onClick={() => setExpandedIdx(expandedIdx === i ? null : i)}
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 16px', cursor: 'pointer', background: expandedIdx === i ? '#f8fafc' : 'white', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                <span style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '14px', color: '#1e293b' }}>{v.rule_id}</span>
                <span style={{ fontWeight: 700, color: '#2563eb', fontSize: '13px' }}>{v.subject_id}</span>
                <span style={{ padding: '2px 8px', borderRadius: '99px', fontSize: '11px', fontWeight: 700, background: sevColor[v.severity] || '#94a3b8', color: 'white' }}>{v.severity}</span>
                <span style={{ padding: '2px 8px', borderRadius: '99px', fontSize: '11px', background: '#ede9fe', color: '#6d28d9', fontWeight: 600 }}>{v.action_required}</span>
              </div>
              <span style={{ color: '#94a3b8', fontSize: '13px' }}>{expandedIdx === i ? '▲' : '▼'}</span>
            </div>
            {/* Expanded */}
            {expandedIdx === i && (
              <div style={{ padding: '12px 16px', borderTop: '1px solid #e2e8f0', background: 'white' }}>
                {v.evidence && v.evidence.length > 0 && (
                  <div style={{ marginBottom: '10px' }}>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: '#475569', marginBottom: '4px' }}>Evidence:</div>
                    <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '13px', color: '#374151', lineHeight: 1.6 }}>
                      {v.evidence.map((e, ei) => <li key={ei}>{e}</li>)}
                    </ul>
                  </div>
                )}
                <div style={{ fontSize: '12px', fontWeight: 700, color: '#475569', marginBottom: '4px' }}>LLM Reasoning:</div>
                <div style={{ fontSize: '13px', color: '#374151', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '10px 12px', lineHeight: 1.6 }}>
                  {v.reasoning}
                </div>
                {v.run_date && <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '8px' }}>Run: {v.run_date?.substring(0, 19)} · Job: {v.job_id}</div>}
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
}

function ViolationCard({ violation }) {
  const severityColor = {
    critical: '#dc2626',
    major: '#f59e0b',
    minor: '#10b981'
  };

  return (
    <div 
      className="violation-card"
      style={{ borderLeft: `4px solid ${severityColor[violation.severity]}` }}
    >
      <div className="violation-header">
        <h4>{violation.rule_id}</h4>
        <span 
          className="severity-badge"
          style={{ backgroundColor: severityColor[violation.severity] }}
        >
          {violation.severity}
        </span>
      </div>
      
      <p className="violation-description">
        {violation.violation_description}
      </p>
      
      {violation.evidence && violation.evidence.length > 0 && (
        <div className="evidence">
          <strong>Evidence:</strong>
          <ul>
            {violation.evidence.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="violation-actions">
        <button className="acknowledge-btn">Acknowledge</button>
        <button className="create-query-btn">Create Query</button>
      </div>
    </div>
  );
}

// Rule Executor
function RuleExecutor({ onNavigate }) {
  const [mode, setMode] = useState('single'); // 'single' or 'batch'
  const [selectedSubject, setSelectedSubject] = useState('');
  const [executing, setExecuting] = useState(false);
  const [results, setResults] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [savedJobId, setSavedJobId] = useState(null);
  const [ruleStats, setRuleStats] = useState({ total: 0, active: 0 });

  React.useEffect(() => {
    fetch('/api/rules')
      .then(r => r.json())
      .then(data => {
        const all = data.rules || [];
        setRuleStats({ total: all.length, active: all.filter(r => r.status === 'active').length });
      })
      .catch(() => {});
  }, []);
  const pollRef = React.useRef(null);

  const stopPolling = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  };

  React.useEffect(() => () => stopPolling(), []);

  const pollJob = (id) => {
    stopPolling();
    pollRef.current = setInterval(() => {
      fetch(`/api/evaluate/batch/${id}`)
        .then(r => r.json())
        .then(data => {
          setJobStatus(data);
          if (data.status === 'done' || data.status === 'error') {
            stopPolling();
            setExecuting(false);
            if (data.status === 'done') setResults(data);
          }
        })
        .catch(() => { stopPolling(); setExecuting(false); });
    }, 1500);
  };

  const executeSingle = () => {
    if (!selectedSubject) return;
    setExecuting(true);
    setResults(null);
    setJobStatus(null);
    setSavedJobId(null);
    fetch(`/api/evaluate/subject/${selectedSubject}`, { method: 'POST' })
      .then(r => r.json())
      .then(data => {
        setResults(data);
        setExecuting(false);
        if (data.job_id) setSavedJobId(data.job_id);
      })
      .catch(() => setExecuting(false));
  };

  const executeBatch = (scope) => {
    setExecuting(true);
    setResults(null);
    setJobStatus(null);
    const body = scope === 'all'
      ? { subject_ids: 'all', rule_ids: [] }
      : { subject_ids: [selectedSubject], rule_ids: [] };
    fetch('/api/evaluate/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
      .then(r => r.json())
      .then(data => { setJobId(data.job_id); setJobStatus(data); pollJob(data.job_id); })
      .catch(() => setExecuting(false));
  };

  const severityColor = { critical: '#dc2626', major: '#f59e0b', minor: '#10b981' };

  return (
    <div className="rule-executor">
      <h2>▶️ Execute Rules</h2>

      {/* Mode Toggle */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <button onClick={() => setMode('single')}
          style={{ padding: '8px 20px', borderRadius: '6px', border: 'none', cursor: 'pointer',
            background: mode === 'single' ? '#2563eb' : '#e5e7eb',
            color: mode === 'single' ? 'white' : '#374151', fontWeight: 600 }}>
          👤 Single Subject
        </button>
        <button
          disabled
          title="Batch execution disabled — runs all 100 subjects and may incur significant API costs"
          style={{ padding: '8px 20px', borderRadius: '6px', border: 'none',
            cursor: 'not-allowed', background: '#e5e7eb', color: '#9ca3af',
            fontWeight: 600, opacity: 0.6 }}>
          👥 All Subjects (Batch) 🔒
        </button>
      </div>
      <p style={{ fontSize: '12px', color: '#94a3b8', margin: '-12px 0 16px 0' }}>
        ⚠️ Batch mode disabled — contact admin to enable
      </p>

      {/* Single Subject Mode */}
      {mode === 'single' && (
        <div className="executor-form">
          <div className="form-group">
            <label>Subject ID:</label>
            <input type="text" value={selectedSubject}
              onChange={e => setSelectedSubject(e.target.value)}
              placeholder="e.g., 101-001" />
          </div>
          <button className="execute-button" onClick={executeSingle}
            disabled={executing || !selectedSubject}>
            {executing ? '⏳ Running...' : '▶️ Run All Rules'}
          </button>
        </div>
      )}

      {/* Batch Mode */}
      {mode === 'batch' && (
        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px' }}>
          <p style={{ color: '#475569', marginBottom: '16px', fontSize: '14px' }}>
            Runs all <strong>{ruleStats.active} active rules</strong> across <strong>all subjects</strong> and their visits.
            LLM rules use Claude API — this may take a few minutes.
          </p>
          <button onClick={() => executeBatch('all')} disabled={executing}
            style={{ padding: '10px 28px', background: executing ? '#94a3b8' : '#7c3aed',
              color: 'white', border: 'none', borderRadius: '6px', cursor: executing ? 'not-allowed' : 'pointer',
              fontWeight: 700, fontSize: '15px' }}>
            {executing ? '⏳ Running Batch...' : '🚀 Run All Rules for All Subjects'}
          </button>
        </div>
      )}

      {/* Progress Bar for Batch */}
      {jobStatus && (jobStatus.status === 'running' || jobStatus.status === 'queued') && (
        <div style={{ marginTop: '24px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <strong>Batch Progress</strong>
            <span style={{ color: '#64748b', fontSize: '14px' }}>
              {jobStatus.completed || 0} / {jobStatus.total} subjects
            </span>
          </div>
          <div style={{ background: '#e2e8f0', borderRadius: '99px', height: '12px', overflow: 'hidden' }}>
            <div style={{
              height: '100%', borderRadius: '99px', background: '#7c3aed',
              width: `${jobStatus.progress_pct || 0}%`, transition: 'width 0.5s ease'
            }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', fontSize: '13px', color: '#64748b' }}>
            <span>🚨 Violations found so far: <strong>{jobStatus.violations_so_far || 0}</strong></span>
            <span>{jobStatus.progress_pct || 0}% complete</span>
          </div>
        </div>
      )}

      {/* Single Subject Results */}
      {results && mode === 'single' && (
        <div className="execution-results" style={{ marginTop: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 style={{ margin: 0 }}>Results for {results.subject_id}</h3>
            {savedJobId && onNavigate && (
              <button onClick={() => onNavigate('results')}
                style={{ padding: '6px 14px', background: '#2563eb', color: 'white', border: 'none',
                  borderRadius: '6px', cursor: 'pointer', fontSize: '13px', fontWeight: 600 }}>
                📁 View in Results →
              </button>
            )}
            {savedJobId && !onNavigate && (
              <span style={{ fontSize: '12px', color: '#16a34a', background: '#dcfce7',
                padding: '4px 10px', borderRadius: '99px' }}>
                ✅ Saved to Results tab
              </span>
            )}
          </div>
          <div style={{ display: 'flex', gap: '16px', marginBottom: '16px', flexWrap: 'wrap' }}>
            <div className="stat-card" style={{ flex: 1, minWidth: '120px' }}>
              <div className="stat-value">{results.total_rules_executed}</div>
              <div className="stat-label">Rules Executed</div>
            </div>
            <div className="stat-card" style={{ flex: 1, minWidth: '120px' }}>
              <div className="stat-value" style={{ color: results.violations_found > 0 ? '#dc2626' : '#10b981' }}>
                {results.violations_found}
              </div>
              <div className="stat-label">Violations Found</div>
            </div>
            {results.usage && results.usage.total_api_calls > 0 && (
              <div className="stat-card" style={{ flex: 2, minWidth: '200px', background: '#f0fdf4', border: '1px solid #bbf7d0' }}>
                <div className="stat-value" style={{ fontSize: '18px', color: '#16a34a' }}>
                  {results.usage.estimated_cost_display}
                </div>
                <div className="stat-label">
                  Est. Cost · {results.usage.total_tokens.toLocaleString()} tokens · {results.usage.total_api_calls} API calls
                </div>
              </div>
            )}
          </div>

          {results.results && results.results.map((r, i) => (
            <div key={i} style={{ background: '#f8fafc', border: `1px solid ${r.violated ? '#fca5a5' : '#bbf7d0'}`,
              borderRadius: '8px', padding: '14px', marginBottom: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong>{r.rule_id}</strong>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={{ fontSize: '12px', color: '#64748b' }}>{r.evaluation_method}</span>
                  <span style={{ padding: '2px 10px', borderRadius: '99px', fontSize: '12px', fontWeight: 700,
                    background: r.violated ? '#fee2e2' : '#dcfce7', color: r.violated ? '#dc2626' : '#16a34a' }}>
                    {r.violated ? '❌ VIOLATION' : '✅ PASS'}
                  </span>
                </div>
              </div>
              {r.violated && (
                <>
                  <p style={{ color: '#dc2626', fontSize: '13px', margin: '8px 0 4px' }}>{r.reasoning}</p>
                  <p style={{ color: '#7c3aed', fontSize: '12px', fontWeight: 600 }}>Action: {r.action_required}</p>
                  {r.evidence && r.evidence.length > 0 && (
                    <ul style={{ margin: '6px 0 0', paddingLeft: '18px', fontSize: '12px', color: '#475569' }}>
                      {r.evidence.map((e, ei) => <li key={ei}>{e}</li>)}
                    </ul>
                  )}
                </>
              )}
              {!r.violated && <p style={{ color: '#64748b', fontSize: '13px', margin: '6px 0 0' }}>{r.reasoning}</p>}
              <p style={{ fontSize: '11px', color: '#94a3b8', margin: '6px 0 0' }}>⏱ {r.execution_time_ms}ms</p>
            </div>
          ))}
        </div>
      )}

      {/* Batch Results Summary */}
      {results && mode === 'batch' && jobStatus?.status === 'done' && (
        <div style={{ marginTop: '24px' }}>
          <h3>Batch Execution Complete</h3>
          <div style={{ display: 'flex', gap: '16px', marginBottom: '20px', flexWrap: 'wrap' }}>
            <div className="stat-card" style={{ flex: 1, minWidth: '120px' }}>
              <div className="stat-value">{results.total_subjects}</div>
              <div className="stat-label">Subjects Evaluated</div>
            </div>
            <div className="stat-card" style={{ flex: 1, minWidth: '120px' }}>
              <div className="stat-value" style={{ color: '#dc2626' }}>{results.total_violations}</div>
              <div className="stat-label">Total Violations</div>
            </div>
          </div>

          {results.all_violations && results.all_violations.length > 0 && (
            <div>
              <h4 style={{ marginBottom: '12px' }}>🚨 All Violations ({results.all_violations.length})</h4>
              {results.all_violations.map((v, i) => (
                <div key={i} style={{ background: '#fff7ed', border: '1px solid #fed7aa',
                  borderLeft: `4px solid ${severityColor[v.severity] || '#f59e0b'}`,
                  borderRadius: '6px', padding: '12px', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <strong>{v.subject_id} — {v.rule_id}</strong>
                    <span style={{ padding: '2px 8px', borderRadius: '99px', fontSize: '12px',
                      background: severityColor[v.severity] || '#f59e0b', color: 'white' }}>
                      {v.severity}
                    </span>
                  </div>
                  <p style={{ color: '#7c3aed', fontSize: '12px', margin: '4px 0', fontWeight: 600 }}>
                    Action: {v.action_required}
                  </p>
                  <p style={{ color: '#475569', fontSize: '13px', margin: 0 }}>{v.reasoning}</p>
                </div>
              ))}
            </div>
          )}

          {results.total_violations === 0 && (
            <div style={{ textAlign: 'center', padding: '40px', color: '#16a34a', fontSize: '18px' }}>
              ✅ No violations found across all subjects!
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Per-rule result row — expandable to show full evidence + reasoning
function RuleResultRow({ r }) {
  const [expanded, setExpanded] = useState(false);
  const methodColor = {
    deterministic: '#0369a1',
    llm_with_tools: '#7c3aed',
    llm_with_tools_mock: '#9333ea',
    not_applicable: '#94a3b8',
  };
  return (
    <div style={{
      border: `1px solid ${r.violated ? '#fca5a5' : r.evaluation_method === 'not_applicable' ? '#e2e8f0' : '#bbf7d0'}`,
      borderLeft: `4px solid ${r.violated ? '#dc2626' : r.evaluation_method === 'not_applicable' ? '#cbd5e1' : '#16a34a'}`,
      borderRadius: '6px', marginBottom: '8px', overflow: 'hidden'
    }}>
      {/* Header row — always visible */}
      <div onClick={() => setExpanded(!expanded)}
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '10px 14px', cursor: 'pointer',
          background: r.violated ? '#fff5f5' : r.evaluation_method === 'not_applicable' ? '#f8fafc' : '#f0fdf4' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '14px' }}>{r.rule_id}</span>
          <span style={{ fontSize: '11px', color: methodColor[r.evaluation_method] || '#64748b',
            background: '#f1f5f9', padding: '1px 7px', borderRadius: '99px', fontWeight: 600 }}>
            {r.evaluation_method === 'llm_with_tools' ? '🤖 LLM' :
             r.evaluation_method === 'llm_with_tools_mock' ? '🤖 Mock' :
             r.evaluation_method === 'deterministic' ? '⚙️ Det.' :
             r.evaluation_method === 'not_applicable' ? '⏭ N/A' : r.evaluation_method}
          </span>
          {r.tools_used && r.tools_used.length > 0 && (
            <span style={{ fontSize: '11px', color: '#64748b' }}>
              🔧 {r.tools_used.join(', ')}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {r.execution_time_ms && (
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>⏱ {r.execution_time_ms}ms</span>
          )}
          <span style={{ padding: '3px 10px', borderRadius: '99px', fontSize: '12px', fontWeight: 700,
            background: r.violated ? '#dc2626' : r.evaluation_method === 'not_applicable' ? '#e2e8f0' : '#16a34a',
            color: r.evaluation_method === 'not_applicable' ? '#64748b' : 'white' }}>
            {r.violated ? '❌ VIOLATION' : r.evaluation_method === 'not_applicable' ? '⏭ SKIPPED' : '✅ PASS'}
          </span>
          <span style={{ color: '#94a3b8', fontSize: '13px' }}>{expanded ? '▲' : '▼'}</span>
        </div>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div style={{ padding: '12px 16px', background: 'white', borderTop: '1px solid #e2e8f0' }}>
          {/* Action required */}
          {r.action_required && (
            <div style={{ marginBottom: '10px' }}>
              <span style={{ fontSize: '12px', fontWeight: 700, color: '#dc2626',
                background: '#fee2e2', padding: '3px 10px', borderRadius: '99px' }}>
                ⚠️ Action: {r.action_required}
              </span>
            </div>
          )}

          {/* Confidence */}
          {r.confidence && r.evaluation_method !== 'not_applicable' && (
            <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '8px' }}>
              Confidence: <strong style={{ color: r.confidence === 'high' ? '#16a34a' : r.confidence === 'low' ? '#dc2626' : '#f59e0b' }}>
                {r.confidence}
              </strong>
            </div>
          )}

          {/* Reasoning */}
          {r.reasoning && (
            <div style={{ marginBottom: '10px' }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: '#475569', marginBottom: '4px' }}>Reasoning:</div>
              <div style={{ fontSize: '13px', color: '#374151', lineHeight: '1.5',
                background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '6px',
                padding: '10px 12px', maxHeight: '200px', overflowY: 'auto' }}>
                {r.reasoning}
              </div>
            </div>
          )}

          {/* Evidence */}
          {r.evidence && r.evidence.length > 0 && (
            <div style={{ marginBottom: '10px' }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: '#475569', marginBottom: '4px' }}>
                Evidence ({r.evidence.length}):
              </div>
              <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '13px', color: '#374151', lineHeight: '1.6' }}>
                {r.evidence.map((e, i) => <li key={i}>{e}</li>)}
              </ul>
            </div>
          )}

          {/* Recommendation */}
          {r.recommendation && (
            <div style={{ fontSize: '12px', color: '#7c3aed', fontStyle: 'italic', marginTop: '6px' }}>
              💡 {r.recommendation}
            </div>
          )}

          {/* Missing data */}
          {r.missing_data && r.missing_data.length > 0 && (
            <div style={{ fontSize: '12px', color: '#f59e0b', marginTop: '6px' }}>
              ⚠️ Missing data: {r.missing_data.join(', ')}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Results Viewer - Browse past runs (single subject and batch)
function ResultsViewer() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRun, setSelectedRun] = useState(null);
  const [runDetail, setRunDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [filterRule, setFilterRule] = useState('all');
  const [filterType, setFilterType] = useState('all');
  const [searchSubject, setSearchSubject] = useState('');
  const [detailTab, setDetailTab] = useState('results'); // 'results' | 'violations'

  const severityColor = { critical: '#dc2626', major: '#f59e0b', minor: '#10b981' };

  React.useEffect(() => {
    fetch('/api/results')
      .then(r => r.json())
      .then(data => { setRuns(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const filteredRuns = filterType === 'all' ? runs
    : runs.filter(r => (filterType === 'single' ? r.run_type === 'single' : r.run_type !== 'single'));

  const detailRef = React.useRef(null);

  const loadRunDetail = (jobId) => {
    if (selectedRun === jobId) { setSelectedRun(null); setRunDetail(null); return; }
    setSelectedRun(jobId);
    setRunDetail(null);
    setDetailLoading(true);
    setDetailTab('results');
    fetch(`/api/results/${jobId}`)
      .then(r => r.json())
      .then(data => {
        setRunDetail(data);
        setDetailLoading(false);
        // Scroll the detail panel into view after render
        setTimeout(() => {
          if (detailRef.current) {
            detailRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }, 50);
      })
      .catch(() => setDetailLoading(false));
  };

  // Filter violations for violations tab
  const filteredViolations = runDetail?.all_violations?.filter(v => {
    const sevOk = filterSeverity === 'all' || v.severity === filterSeverity;
    const ruleOk = filterRule === 'all' || v.rule_id === filterRule;
    const subOk = !searchSubject || v.subject_id.toLowerCase().includes(searchSubject.toLowerCase());
    return sevOk && ruleOk && subOk;
  }) || [];

  const uniqueRules = [...new Set(runDetail?.all_violations?.map(v => v.rule_id) || [])];

  if (loading) return <div className="loading">Loading results...</div>;

  return (
    <div style={{ padding: '0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <h2 style={{ margin: 0 }}>📁 Evaluation Results</h2>
        <div style={{ display: 'flex', gap: '8px' }}>
          {['all', 'single', 'batch'].map(t => (
            <button key={t} onClick={() => setFilterType(t)}
              style={{ padding: '4px 14px', borderRadius: '99px', border: 'none', cursor: 'pointer', fontSize: '13px',
                background: filterType === t ? '#2563eb' : '#e2e8f0',
                color: filterType === t ? 'white' : '#374151', fontWeight: filterType === t ? 700 : 400 }}>
              {t === 'all' ? 'All' : t === 'single' ? '👤 Single' : '👥 Batch'}
            </button>
          ))}
        </div>
      </div>

      {runs.length === 0 && (
        <div style={{ textAlign: 'center', padding: '60px', color: '#94a3b8' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>📭</div>
          <p>No results yet. Go to <strong>Execute</strong> to run rules for a subject or all subjects.</p>
        </div>
      )}

      {/* Run list — detail panel opens inline below each selected run */}
      {filteredRuns.length > 0 && (
        <div style={{ marginBottom: '16px', marginTop: '16px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {filteredRuns.map(run => (
              <div key={run.job_id}>
                {/* Run row header */}
                <div onClick={() => loadRunDetail(run.job_id)}
                  style={{
                    background: selectedRun === run.job_id ? '#eff6ff' : '#f8fafc',
                    border: `1px solid ${selectedRun === run.job_id ? '#93c5fd' : '#e2e8f0'}`,
                    borderRadius: selectedRun === run.job_id ? '8px 8px 0 0' : '8px',
                    padding: '12px 18px', cursor: 'pointer',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    flexWrap: 'wrap', gap: '8px'
                  }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                    <span style={{ padding: '2px 8px', borderRadius: '99px', fontSize: '11px', fontWeight: 700,
                      background: run.run_type === 'single' ? '#dbeafe' : '#ede9fe',
                      color: run.run_type === 'single' ? '#1d4ed8' : '#6d28d9' }}>
                      {run.run_type === 'single' ? '👤 Single' : '👥 Batch'}
                    </span>
                    {run.run_type === 'single' && run.subject_id && (
                      <span style={{ fontWeight: 700, fontFamily: 'monospace', color: '#2563eb', fontSize: '14px' }}>
                        {run.subject_id}
                      </span>
                    )}
                    {run.run_type !== 'single' && (
                      <span style={{ fontWeight: 700, fontFamily: 'monospace', color: '#7c3aed', fontSize: '13px' }}>
                        #{run.job_id}
                      </span>
                    )}
                    <span style={{ fontSize: '12px', color: '#94a3b8' }}>{run.saved_at}</span>
                  </div>
                  <div style={{ display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '13px', fontWeight: 700,
                      color: run.total_violations > 0 ? '#dc2626' : '#16a34a' }}>
                      {run.total_violations > 0 ? `🚨 ${run.total_violations} violation${run.total_violations !== 1 ? 's' : ''}` : '✅ Clean'}
                    </span>
                    {run.usage?.estimated_cost_display && run.usage.estimated_cost_display !== '$0.0000' && (
                      <span style={{ fontSize: '12px', color: '#7c3aed' }}>💰 {run.usage.estimated_cost_display}</span>
                    )}
                    <span style={{ fontSize: '12px', color: '#94a3b8' }}>
                      {selectedRun === run.job_id ? '▲ Hide' : '▼ Details'}
                    </span>
                  </div>
                </div>

                {/* Inline detail panel — only shows for the selected run */}
                {selectedRun === run.job_id && (
                  <div ref={detailRef} style={{ background: '#f8fafc', border: '1px solid #93c5fd', borderTop: 'none',
                    borderRadius: '0 0 8px 8px', padding: '20px', marginBottom: '6px' }}>
          {detailLoading && <div className="loading">Loading run details...</div>}

          {runDetail && (
            <>
              {/* Summary stat cards */}
              <div style={{ display: 'flex', gap: '10px', marginBottom: '16px', flexWrap: 'wrap' }}>
                <div className="stat-card" style={{ flex: 1, minWidth: '100px' }}>
                  <div className="stat-value">{runDetail.total_subjects}</div>
                  <div className="stat-label">Subjects</div>
                </div>
                <div className="stat-card" style={{ flex: 1, minWidth: '100px' }}>
                  <div className="stat-value" style={{ color: runDetail.total_violations > 0 ? '#dc2626' : '#16a34a' }}>
                    {runDetail.total_violations}
                  </div>
                  <div className="stat-label">Violations</div>
                </div>
                <div className="stat-card" style={{ flex: 1, minWidth: '100px' }}>
                  <div className="stat-value" style={{ color: '#dc2626' }}>
                    {runDetail.all_violations?.filter(v => v.severity === 'critical').length || 0}
                  </div>
                  <div className="stat-label">Critical</div>
                </div>
                <div className="stat-card" style={{ flex: 1, minWidth: '100px' }}>
                  <div className="stat-value" style={{ color: '#f59e0b' }}>
                    {runDetail.all_violations?.filter(v => v.severity === 'major').length || 0}
                  </div>
                  <div className="stat-label">Major</div>
                </div>
                {runDetail.usage?.estimated_cost_display && runDetail.usage.estimated_cost_display !== '$0.0000' && (
                  <div className="stat-card" style={{ flex: 1, minWidth: '100px', background: '#f0fdf4', border: '1px solid #bbf7d0' }}>
                    <div className="stat-value" style={{ fontSize: '16px', color: '#16a34a' }}>
                      {runDetail.usage.estimated_cost_display}
                    </div>
                    <div className="stat-label">{(runDetail.usage.total_tokens || 0).toLocaleString()} tokens</div>
                  </div>
                )}
              </div>

              {/* Tab switcher: Per-Rule Results | Violations Only */}
              <div style={{ display: 'flex', gap: '0', marginBottom: '16px', borderBottom: '2px solid #e2e8f0' }}>
                {[
                  { id: 'results', label: '📋 Per-Rule Results' },
                  { id: 'violations', label: `🚨 Violations (${runDetail.total_violations})` }
                ].map(tab => (
                  <button key={tab.id} onClick={() => setDetailTab(tab.id)}
                    style={{ padding: '8px 20px', border: 'none', cursor: 'pointer', fontSize: '13px', fontWeight: 600,
                      background: 'transparent',
                      borderBottom: detailTab === tab.id ? '2px solid #2563eb' : '2px solid transparent',
                      color: detailTab === tab.id ? '#2563eb' : '#64748b',
                      marginBottom: '-2px' }}>
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* TAB: Per-Rule Results — shows every subject + every rule */}
              {detailTab === 'results' && (
                <div>
                  {runDetail.results && runDetail.results.map((subjectResult, si) => (
                    <div key={si} style={{ marginBottom: '20px' }}>
                      {/* Subject header */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                        <span style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '15px', color: '#1e293b' }}>
                          👤 {subjectResult.subject_id}
                        </span>
                        <span style={{ fontSize: '12px', padding: '2px 8px', borderRadius: '99px', fontWeight: 700,
                          background: subjectResult.violations_found > 0 ? '#fee2e2' : '#dcfce7',
                          color: subjectResult.violations_found > 0 ? '#dc2626' : '#16a34a' }}>
                          {subjectResult.violations_found > 0
                            ? `${subjectResult.violations_found} violation${subjectResult.violations_found !== 1 ? 's' : ''}`
                            : 'No violations'}
                        </span>
                      </div>
                      {/* Per-rule result rows */}
                      {subjectResult.results && subjectResult.results.map((r, ri) => (
                        <RuleResultRow key={ri} r={r} />
                      ))}
                      {(!subjectResult.results || subjectResult.results.length === 0) && (
                        <div style={{ color: '#94a3b8', fontSize: '13px', padding: '8px' }}>No rule results available</div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* TAB: Violations Only */}
              {detailTab === 'violations' && (
                <>
                  {runDetail.total_violations > 0 ? (
                    <>
                      {/* Filters */}
                      <div style={{ display: 'flex', gap: '10px', marginBottom: '14px', flexWrap: 'wrap', alignItems: 'center' }}>
                        <input type="text" placeholder="Search subject..." value={searchSubject}
                          onChange={e => setSearchSubject(e.target.value)}
                          style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid #e2e8f0', fontSize: '13px', width: '150px' }} />
                        <select value={filterSeverity} onChange={e => setFilterSeverity(e.target.value)}
                          style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid #e2e8f0', fontSize: '13px' }}>
                          <option value="all">All Severities</option>
                          <option value="critical">Critical</option>
                          <option value="major">Major</option>
                          <option value="minor">Minor</option>
                        </select>
                        <select value={filterRule} onChange={e => setFilterRule(e.target.value)}
                          style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid #e2e8f0', fontSize: '13px' }}>
                          <option value="all">All Rules</option>
                          {uniqueRules.map(r => <option key={r} value={r}>{r}</option>)}
                        </select>
                        <span style={{ fontSize: '13px', color: '#64748b' }}>
                          {filteredViolations.length} of {runDetail.total_violations}
                        </span>
                      </div>
                      <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                          <thead>
                            <tr style={{ background: '#f1f5f9', textAlign: 'left' }}>
                              <th style={{ padding: '10px 12px', border: '1px solid #e2e8f0' }}>Subject</th>
                              <th style={{ padding: '10px 12px', border: '1px solid #e2e8f0' }}>Rule</th>
                              <th style={{ padding: '10px 12px', border: '1px solid #e2e8f0' }}>Severity</th>
                              <th style={{ padding: '10px 12px', border: '1px solid #e2e8f0' }}>Action</th>
                              <th style={{ padding: '10px 12px', border: '1px solid #e2e8f0' }}>Evidence</th>
                              <th style={{ padding: '10px 12px', border: '1px solid #e2e8f0' }}>Reasoning</th>
                            </tr>
                          </thead>
                          <tbody>
                            {filteredViolations.map((v, i) => (
                              <tr key={i} style={{ background: i % 2 === 0 ? 'white' : '#f8fafc', verticalAlign: 'top' }}>
                                <td style={{ padding: '10px 12px', border: '1px solid #e2e8f0', fontWeight: 700, fontFamily: 'monospace' }}>
                                  {v.subject_id}
                                </td>
                                <td style={{ padding: '10px 12px', border: '1px solid #e2e8f0', fontFamily: 'monospace', color: '#7c3aed' }}>
                                  {v.rule_id}
                                </td>
                                <td style={{ padding: '10px 12px', border: '1px solid #e2e8f0' }}>
                                  <span style={{ padding: '2px 8px', borderRadius: '99px', fontSize: '11px', fontWeight: 700,
                                    background: severityColor[v.severity] || '#94a3b8', color: 'white' }}>
                                    {v.severity || 'unknown'}
                                  </span>
                                </td>
                                <td style={{ padding: '10px 12px', border: '1px solid #e2e8f0', color: '#dc2626', fontWeight: 600 }}>
                                  {v.action_required || '—'}
                                </td>
                                <td style={{ padding: '10px 12px', border: '1px solid #e2e8f0', color: '#374151', maxWidth: '200px' }}>
                                  {v.evidence && v.evidence.length > 0 ? (
                                    <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '12px' }}>
                                      {v.evidence.slice(0, 3).map((e, ei) => <li key={ei}>{e}</li>)}
                                      {v.evidence.length > 3 && <li style={{ color: '#94a3b8' }}>+{v.evidence.length - 3} more</li>}
                                    </ul>
                                  ) : '—'}
                                </td>
                                <td style={{ padding: '10px 12px', border: '1px solid #e2e8f0', color: '#475569', maxWidth: '280px', fontSize: '12px' }}>
                                  {v.reasoning?.substring(0, 200)}{v.reasoning?.length > 200 ? '...' : ''}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '40px', color: '#16a34a', fontSize: '18px' }}>
                      ✅ No violations found in this run
                    </div>
                  )}
                </>
              )}
            </>
          )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {filteredRuns.length === 0 && runs.length > 0 && (
        <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
          No {filterType === 'single' ? 'single-subject' : 'batch'} runs found.
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// CTMS — SITE MONITORING VISITS
// ═══════════════════════════════════════════════════════════════════════════

// ─── Shared helpers for SiteMonitoring ───────────────────────────────────────
const statusColor = (s) => ({ 'Completed':'#10b981','Confirmed':'#3b82f6','Planned':'#f59e0b','In Progress':'#8b5cf6','Cancelled':'#94a3b8' }[s]||'#94a3b8');
const visitIcon  = (s) => ({ 'Completed':'✅','Confirmed':'📋','Planned':'📅','In Progress':'🔄','Cancelled':'❌' }[s]||'📅');
const riskColors = { 'High': { bg:'#fef2f2', border:'#fca5a5', text:'#dc2626' }, 'Medium': { bg:'#fffbeb', border:'#fde68a', text:'#d97706' }, 'Low': { bg:'#f0fdf4', border:'#86efac', text:'#16a34a' } };
const countryFlag = (country) => {
  const map = { 'United States':'🇺🇸','USA':'🇺🇸','United Kingdom':'🇬🇧','UK':'🇬🇧','Canada':'🇨🇦','Australia':'🇦🇺','Singapore':'🇸🇬' };
  return map[country] || '🌍';
};

function SiteMonitoring({ onNavigate, onSelectSubject, onContextChange, showToast }) {
  const [viewLevel, setViewLevel] = useState('study');       // 'study' | 'site' | 'visit'
  const [selectedSiteId, setSelectedSiteId] = useState(null);
  const [selectedVisitId, setSelectedVisitId] = useState(null);
  const [overviewData, setOverviewData] = useState(null);
  const [siteData, setSiteData] = useState(null);
  const [tmfData, setTmfData] = useState(null);
  const [tmfOpen, setTmfOpen] = useState(false);
  const [loadingOverview, setLoadingOverview] = useState(true);
  const [loadingSite, setLoadingSite] = useState(false);

  // Fetch study overview on mount
  React.useEffect(() => {
    fetch('/api/ctms/sites-overview')
      .then(r => r.json())
      .then(d => { setOverviewData(d); setLoadingOverview(false); })
      .catch(() => setLoadingOverview(false));
  }, []);

  const goToSite = (siteId) => {
    setSelectedSiteId(siteId);
    setSelectedVisitId(null);
    setSiteData(null);
    setTmfData(null);
    setTmfOpen(false);
    setLoadingSite(true);
    setViewLevel('site');
    if (onContextChange) onContextChange({ site_id: siteId, visit_id: null });
    fetch(`/api/ctms/site/${siteId}`).then(r => r.json()).then(d => { setSiteData(d); setLoadingSite(false); }).catch(() => setLoadingSite(false));
  };

  const goToVisit = (visitId) => {
    setSelectedVisitId(visitId);
    setViewLevel('visit');
    if (onContextChange) onContextChange({ site_id: selectedSiteId, visit_id: visitId });
  };

  const goBackToStudy = () => { setViewLevel('study'); setSelectedSiteId(null); setSelectedVisitId(null); setSiteData(null); setTmfData(null); if (onContextChange) onContextChange({ site_id:'', visit_id:null }); };
  const goBackToSite  = () => { setViewLevel('site'); setSelectedVisitId(null); if (onContextChange) onContextChange({ site_id: selectedSiteId, visit_id: null }); };

  const loadTmf = () => {
    if (!selectedSiteId) return;
    fetch(`/api/tmf/site/${selectedSiteId}`).then(r => r.json()).then(setTmfData).catch(() => {});
    setTmfOpen(true);
  };

  const refreshSite = () => {
    if (!selectedSiteId) return;
    fetch(`/api/ctms/site/${selectedSiteId}`).then(r => r.json()).then(setSiteData).catch(() => {});
  };

  if (loadingOverview) return <div style={{ padding:'40px', textAlign:'center', color:'#64748b' }}>Loading workstation...</div>;
  if (!overviewData) return <div style={{ padding:'40px', textAlign:'center', color:'#ef4444' }}>Failed to load workstation data.</div>;

  const { protocol, sites } = overviewData;
  const totalEnrolled = sites.reduce((s, x) => s + (x.actual_enrollment || 0), 0);

  // ── BREADCRUMB ───────────────────────────────────────────────────────────
  const Breadcrumb = () => viewLevel === 'study' ? null : (
    <div style={{ display:'flex', alignItems:'center', gap:'6px', marginBottom:'20px', fontSize:'13px', color:'#64748b' }}>
      <button onClick={goBackToStudy} style={{ background:'none', border:'none', cursor:'pointer', color:'#2563eb', fontWeight:600, padding:0, fontSize:'13px' }}>My Sites</button>
      {selectedSiteId && (<><span>/</span>
        {viewLevel === 'visit'
          ? <button onClick={goBackToSite} style={{ background:'none', border:'none', cursor:'pointer', color:'#2563eb', fontWeight:600, padding:0, fontSize:'13px' }}>Site {selectedSiteId}</button>
          : <span style={{ color:'#374151', fontWeight:600 }}>Site {selectedSiteId}</span>
        }
      </>)}
      {viewLevel === 'visit' && selectedVisitId && (<><span>/</span><span style={{ color:'#374151', fontWeight:600 }}>Visit {selectedVisitId}</span></>)}
    </div>
  );

  // ── LEVEL 1: STUDY OVERVIEW ──────────────────────────────────────────────
  if (viewLevel === 'study') return (
    <div style={{ padding:'24px', maxWidth:'1200px', margin:'0 auto' }}>
      {/* Study Banner */}
      <div style={{ background:'linear-gradient(135deg, #1e3a5f 0%, #1e40af 100%)', borderRadius:'12px', padding:'22px 28px', color:'white', marginBottom:'28px' }}>
        <div style={{ fontSize:'11px', opacity:0.65, letterSpacing:'0.05em', textTransform:'uppercase', marginBottom:'4px' }}>
          {protocol.sponsor_name} · {protocol.phase}
        </div>
        <h2 style={{ margin:0, fontSize:'20px', fontWeight:700 }}>{protocol.protocol_number} — {protocol.protocol_name}</h2>
        <div style={{ marginTop:'10px', fontSize:'13px', opacity:0.8, display:'flex', gap:'24px', flexWrap:'wrap' }}>
          <span>📍 {sites.length} Active Sites</span>
          <span>👥 {totalEnrolled} Subjects Enrolled</span>
          <span>🌍 Global Study</span>
          <span>📅 Est. Completion: {protocol.estimated_completion_date || 'TBD'}</span>
        </div>
      </div>

      {/* Site Portfolio */}
      <h3 style={{ margin:'0 0 16px', color:'#1e3a5f', fontSize:'16px', fontWeight:700 }}>Site Portfolio</h3>
      <div style={{ display:'flex', flexDirection:'column', gap:'14px' }}>
        {sites.map(s => {
          const rc = riskColors[s.risk] || riskColors['Low'];
          const enrollPct = Math.min(100, Math.round((s.actual_enrollment||0) / (s.planned_enrollment||1) * 100));
          const tmfColor = s.tmf_score >= 90 ? '#10b981' : s.tmf_score >= 75 ? '#f59e0b' : '#ef4444';
          return (
            <div key={s.site_id} style={{ background:'white', borderRadius:'12px', border:'1px solid #e2e8f0', padding:'18px 22px', boxShadow:'0 1px 4px rgba(0,0,0,0.06)', display:'flex', alignItems:'center', gap:'20px', flexWrap:'wrap' }}>
              {/* Site info */}
              <div style={{ flex:'2', minWidth:'220px' }}>
                <div style={{ display:'flex', alignItems:'center', gap:'8px', marginBottom:'4px' }}>
                  <span style={{ fontSize:'18px' }}>{countryFlag(s.country)}</span>
                  <span style={{ fontWeight:700, fontSize:'15px', color:'#1e3a5f' }}>{s.site_name}</span>
                  <span style={{ fontSize:'12px', color:'#94a3b8', background:'#f1f5f9', padding:'2px 8px', borderRadius:'8px' }}>Site {s.site_id}</span>
                </div>
                <div style={{ fontSize:'13px', color:'#64748b' }}>{s.city}{s.state_province ? `, ${s.state_province}` : ''}, {s.country}</div>
                <div style={{ fontSize:'12px', color:'#94a3b8', marginTop:'2px' }}>PI: {s.principal_investigator}</div>
              </div>
              {/* Enrollment */}
              <div style={{ flex:'1', minWidth:'140px' }}>
                <div style={{ fontSize:'12px', color:'#64748b', marginBottom:'4px', fontWeight:600 }}>Enrollment</div>
                <div style={{ fontSize:'13px', color:'#1e3a5f', fontWeight:700, marginBottom:'4px' }}>{s.actual_enrollment} / {s.planned_enrollment}</div>
                <div style={{ background:'#e2e8f0', borderRadius:'4px', height:'6px', overflow:'hidden' }}>
                  <div style={{ width:`${enrollPct}%`, background:'#2563eb', height:'6px', borderRadius:'4px' }}/>
                </div>
                <div style={{ fontSize:'11px', color:'#94a3b8', marginTop:'2px' }}>{enrollPct}% enrolled</div>
              </div>
              {/* Stats */}
              <div style={{ flex:'1', minWidth:'140px' }}>
                <div style={{ fontSize:'12px', color:'#64748b', marginBottom:'6px', fontWeight:600 }}>Activity</div>
                <div style={{ fontSize:'12px', color:'#374151' }}>🔍 {s.visit_count} visit{s.visit_count!==1?'s':''}</div>
                <div style={{ fontSize:'12px', color: s.open_findings>0 ? '#ef4444':'#10b981', fontWeight: s.open_findings>0 ? 600:400 }}>
                  {s.open_findings>0 ? `⚠️ ${s.open_findings} open finding${s.open_findings!==1?'s':''}` : '✅ No open findings'}
                </div>
                <div style={{ fontSize:'12px', color:'#94a3b8', marginTop:'2px' }}>Last: {s.last_visit_date || 'None'}</div>
              </div>
              {/* TMF */}
              <div style={{ flex:'1', minWidth:'120px' }}>
                <div style={{ fontSize:'12px', color:'#64748b', marginBottom:'4px', fontWeight:600 }}>TMF Readiness</div>
                <div style={{ fontSize:'18px', fontWeight:700, color:tmfColor }}>{s.tmf_score}%</div>
                <div style={{ background:'#e2e8f0', borderRadius:'4px', height:'5px', overflow:'hidden', marginTop:'4px' }}>
                  <div style={{ width:`${s.tmf_score}%`, background:tmfColor, height:'5px', borderRadius:'4px' }}/>
                </div>
                {s.tmf_missing>0 && <div style={{ fontSize:'11px', color:'#ef4444', marginTop:'2px' }}>❌ {s.tmf_missing} missing</div>}
                {s.tmf_expiring>0 && <div style={{ fontSize:'11px', color:'#f59e0b', marginTop:'2px' }}>⚠️ {s.tmf_expiring} expiring</div>}
              </div>
              {/* Risk + action */}
              <div style={{ display:'flex', flexDirection:'column', alignItems:'flex-end', gap:'8px', minWidth:'120px' }}>
                <span style={{ padding:'4px 12px', borderRadius:'20px', fontSize:'12px', fontWeight:700, background:rc.bg, border:`1px solid ${rc.border}`, color:rc.text }}>
                  {s.risk === 'High' ? '🔴' : s.risk === 'Medium' ? '🟡' : '🟢'} {s.risk} Risk
                </span>
                <button onClick={() => goToSite(s.site_id)} style={{ background:'#2563eb', color:'white', border:'none', borderRadius:'8px', padding:'7px 16px', cursor:'pointer', fontWeight:600, fontSize:'13px', whiteSpace:'nowrap' }}>
                  View Site →
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  // ── LEVEL 2: SITE DETAIL ──────────────────────────────────────────────────
  if (viewLevel === 'site') {
    if (loadingSite) return <div style={{ padding:'40px', textAlign:'center', color:'#64748b' }}><Breadcrumb/>Loading site data...</div>;
    if (!siteData) return <div style={{ padding:'40px', textAlign:'center', color:'#ef4444' }}><Breadcrumb/>Failed to load site data.</div>;
    const { site, monitoring_visits } = siteData;
    const siteRisk = overviewData.sites.find(s => s.site_id === selectedSiteId) || {};
    const rc = riskColors[siteRisk.risk] || riskColors['Low'];
    const tmfScore = siteRisk.tmf_score;
    const tmfColor = tmfScore >= 90 ? '#10b981' : tmfScore >= 75 ? '#f59e0b' : '#ef4444';

    // Group TMF docs by category
    const tmfByCategory = {};
    if (tmfData) {
      tmfData.documents.forEach(d => {
        if (!tmfByCategory[d.category]) tmfByCategory[d.category] = [];
        tmfByCategory[d.category].push(d);
      });
    }
    const tmfStatusIcon = s => ({ 'Present':'✅', 'Missing':'❌', 'Expiring':'⚠️', 'Superseded':'🔄' }[s]||'❓');

    return (
      <div style={{ padding:'24px', maxWidth:'1200px', margin:'0 auto' }}>
        <Breadcrumb/>
        {/* Site Header */}
        <div style={{ background:'linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%)', borderRadius:'12px', padding:'24px', color:'white', marginBottom:'24px' }}>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', flexWrap:'wrap', gap:'12px' }}>
            <div>
              <div style={{ fontSize:'13px', opacity:0.7, marginBottom:'4px' }}>
                {countryFlag(site.country)} Site {site.site_id} · {site.city}{site.state_province?`, ${site.state_province}`:''}, {site.country}
                <span style={{ marginLeft:'10px', padding:'2px 8px', borderRadius:'10px', fontSize:'11px', fontWeight:700, background: rc.bg, color: rc.text, border:`1px solid ${rc.border}` }}>
                  {siteRisk.risk} Risk
                </span>
              </div>
              <h2 style={{ margin:0, fontSize:'22px', fontWeight:700 }}>🏥 {site.site_name}</h2>
              <div style={{ marginTop:'8px', fontSize:'14px', opacity:0.85 }}>PI: {site.principal_investigator} &nbsp;|&nbsp; Coordinator: {site.site_coordinator}</div>
            </div>
            <div style={{ display:'flex', gap:'12px', flexWrap:'wrap' }}>
              {[{label:'Enrolled', val:`${site.actual_enrollment}/${site.planned_enrollment}`}, {label:'Monitoring Visits', val:monitoring_visits.length}, {label:'TMF Score', val:`${tmfScore}%`}].map(c => (
                <div key={c.label} style={{ textAlign:'center', background:'rgba(255,255,255,0.15)', borderRadius:'8px', padding:'10px 16px' }}>
                  <div style={{ fontSize:'20px', fontWeight:700 }}>{c.val}</div>
                  <div style={{ fontSize:'11px', opacity:0.8 }}>{c.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Visit Timeline */}
        <h3 style={{ margin:'0 0 14px', color:'#1e3a5f', fontSize:'16px', fontWeight:700 }}>Monitoring Visit Timeline</h3>
        {monitoring_visits.length === 0 ? (
          <div style={{ textAlign:'center', padding:'48px', color:'#94a3b8', background:'#f8fafc', borderRadius:'12px', border:'1px dashed #e2e8f0', marginBottom:'24px' }}>
            <div style={{ fontSize:'36px', marginBottom:'10px' }}>📅</div>
            <div style={{ fontWeight:600, fontSize:'15px', marginBottom:'6px' }}>No monitoring visits scheduled</div>
            <div style={{ fontSize:'13px' }}>No visits have been scheduled for this site yet.</div>
          </div>
        ) : (
          <div style={{ display:'flex', gap:'14px', marginBottom:'28px', flexWrap:'wrap' }}>
            {monitoring_visits.map(mv => (
              <div key={mv.monitoring_visit_id}
                onClick={() => goToVisit(mv.monitoring_visit_id)}
                style={{ flex:'1', minWidth:'180px', cursor:'pointer', borderRadius:'10px', padding:'16px', border:`2px solid ${selectedVisitId === mv.monitoring_visit_id ? statusColor(mv.status) : '#e2e8f0'}`, background: selectedVisitId === mv.monitoring_visit_id ? '#f0f9ff':'white', boxShadow:'0 1px 4px rgba(0,0,0,0.07)', transition:'all 0.2s' }}>
                <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'8px' }}>
                  <span style={{ fontWeight:700, fontSize:'15px' }}>{visitIcon(mv.status)} {mv.visit_label}</span>
                  <span style={{ fontSize:'11px', fontWeight:600, padding:'2px 8px', borderRadius:'12px', background:statusColor(mv.status)+'20', color:statusColor(mv.status) }}>{mv.status}</span>
                </div>
                <div style={{ fontSize:'12px', color:'#64748b' }}>{mv.visit_type} · {mv.planned_date}</div>
                <div style={{ fontSize:'11px', color:'#94a3b8', marginTop:'3px' }}>CRA: {mv.cra_name}</div>
                {mv.open_findings > 0 && <div style={{ marginTop:'6px', fontSize:'12px', color:'#ef4444', fontWeight:600 }}>⚠️ {mv.open_findings} open finding(s)</div>}
                {mv.report_status && <div style={{ marginTop:'3px', fontSize:'11px', color: mv.report_status==='Finalised'?'#10b981':'#f59e0b' }}>📄 {mv.report_status}</div>}
              </div>
            ))}
          </div>
        )}

        {/* TMF Status Section */}
        <div style={{ background:'white', borderRadius:'12px', border:'1px solid #e2e8f0', marginBottom:'24px', overflow:'hidden' }}>
          <div style={{ padding:'16px 20px', display:'flex', justifyContent:'space-between', alignItems:'center', cursor:'pointer', background: tmfOpen ? '#f8fafc' : 'white' }} onClick={() => { if(!tmfOpen) loadTmf(); else setTmfOpen(false); }}>
            <div style={{ display:'flex', alignItems:'center', gap:'12px' }}>
              <span style={{ fontSize:'16px', fontWeight:700, color:'#1e3a5f' }}>📁 TMF / Document Status</span>
              <span style={{ fontSize:'13px', fontWeight:700, color:tmfColor }}>{tmfScore}% Readiness</span>
              {siteRisk.tmf_missing>0 && <span style={{ fontSize:'12px', color:'#ef4444' }}>❌ {siteRisk.tmf_missing} missing</span>}
              {siteRisk.tmf_expiring>0 && <span style={{ fontSize:'12px', color:'#f59e0b' }}>⚠️ {siteRisk.tmf_expiring} expiring</span>}
            </div>
            <span style={{ fontSize:'12px', color:'#2563eb', fontWeight:600 }}>{tmfOpen ? '▲ Collapse' : '▼ Expand'}</span>
          </div>
          {tmfOpen && tmfData && (
            <div style={{ padding:'0 20px 20px' }}>
              {/* TMF progress bar */}
              <div style={{ background:'#e2e8f0', borderRadius:'4px', height:'8px', overflow:'hidden', marginBottom:'20px' }}>
                <div style={{ width:`${tmfScore}%`, background:tmfColor, height:'8px', borderRadius:'4px' }}/>
              </div>
              {Object.entries(tmfByCategory).map(([cat, docs]) => (
                <div key={cat} style={{ marginBottom:'16px' }}>
                  <div style={{ fontSize:'12px', fontWeight:700, color:'#64748b', textTransform:'uppercase', letterSpacing:'0.05em', marginBottom:'8px' }}>{cat}</div>
                  {docs.map(d => (
                    <div key={d.document_id} style={{ display:'flex', alignItems:'center', gap:'10px', padding:'8px 12px', borderRadius:'8px', background:'#f8fafc', marginBottom:'6px', border:'1px solid #e2e8f0' }}>
                      <span style={{ fontSize:'16px' }}>{tmfStatusIcon(d.status)}</span>
                      <div style={{ flex:1 }}>
                        <div style={{ fontSize:'13px', fontWeight:600, color:'#1e3a5f' }}>{d.title}</div>
                        {d.notes && <div style={{ fontSize:'11px', color:'#94a3b8', marginTop:'1px' }}>{d.notes}</div>}
                        {d.expiry_date && <div style={{ fontSize:'11px', color: d.status==='Expiring'?'#f59e0b':'#94a3b8' }}>Expires: {d.expiry_date}</div>}
                      </div>
                      {d.file_path && (
                        <button onClick={() => window.open(`/api/tmf/files/${selectedSiteId}/${d.file_path.split('/').pop()}`, '_blank')} style={{ background:'#eff6ff', color:'#2563eb', border:'1px solid #bfdbfe', borderRadius:'6px', padding:'4px 10px', cursor:'pointer', fontSize:'12px', fontWeight:600, whiteSpace:'nowrap' }}>
                          View PDF ↗
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
          {tmfOpen && !tmfData && (
            <div style={{ padding:'20px', textAlign:'center', color:'#94a3b8' }}>Loading TMF documents...</div>
          )}
        </div>

        {/* Visit Detail Panel */}
        {selectedVisitId && (
          <MonitoringVisitDetail visitId={selectedVisitId} onSelectSubject={onSelectSubject} onRefresh={refreshSite} showToast={showToast} />
        )}
      </div>
    );
  }

  // ── LEVEL 3: VISIT DETAIL (full page within site context) ────────────────
  if (viewLevel === 'visit') return (
    <div style={{ padding:'24px', maxWidth:'1200px', margin:'0 auto' }}>
      <Breadcrumb/>
      <MonitoringVisitDetail visitId={selectedVisitId} onSelectSubject={onSelectSubject} onRefresh={refreshSite} showToast={showToast} />
    </div>
  );

  return null;
}

function MonitoringVisitDetail({ visitId, onSelectSubject, onRefresh }) {
  const [data, setData] = useState(null);
  const [activePhase, setActivePhase] = useState('planning');
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState('');
  const [showFindingForm, setShowFindingForm] = useState(false);
  const [newFinding, setNewFinding] = useState({ subject_id: '', finding_type: 'Query', description: '', severity: 'Major', assigned_to: '', due_date: '' });
  const [craNotes, setCraNotes] = useState('');
  const [msg, setMsg] = useState('');

  const load = () => {
    setLoading(true);
    fetch(`/api/ctms/monitoring-visits/${visitId}`)
      .then(r => r.json())
      .then(d => { setData(d); setCraNotes(d.report?.cra_notes || ''); setLoading(false); })
      .catch(() => setLoading(false));
  };

  React.useEffect(() => { load(); }, [visitId]);

  const doAction = (url, method = 'PUT', body = null) => {
    setActionLoading(url);
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    return fetch(url, opts)
      .then(r => r.json())
      .then(d => { setMsg(d.success ? '✅ Done' : '❌ Error'); load(); onRefresh(); return d; })
      .catch(() => setMsg('❌ Request failed'))
      .finally(() => setActionLoading(''));
  };

  if (loading) return <div style={{ padding: '32px', textAlign: 'center', color: '#64748b' }}>Loading visit details...</div>;
  if (!data) return null;

  const { visit, subjects, findings, report } = data;
  const open_findings = findings.filter(f => f.status === 'Open');
  const resolved_findings = findings.filter(f => f.status === 'Resolved');
  const isUpcoming = ['Planned', 'Confirmed'].includes(visit.status);
  const isCompleted = visit.status === 'Completed';

  const severityColor = s => ({ Critical: '#dc2626', Major: '#f59e0b', Minor: '#10b981' }[s] || '#94a3b8');
  const priorityColor = p => ({ High: '#dc2626', Medium: '#f59e0b', Low: '#10b981' }[p] || '#94a3b8');
  const findingTypeColor = t => ({ 'Protocol Deviation': '#7c3aed', 'Query': '#2563eb', 'SDV Finding': '#f59e0b', 'Action Item': '#64748b' }[t] || '#94a3b8');

  const phases = [
    { id: 'planning', label: '1. Pre-Visit Planning' },
    { id: 'during', label: '2. During Visit' },
    { id: 'report', label: '3. Post-Visit Report' }
  ];

  return (
    <div style={{ background: 'white', borderRadius: '12px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
      {/* Visit Header */}
      <div style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', padding: '16px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '17px', color: '#1e3a5f' }}>{visit.visit_label} — {visit.visit_type}</h3>
          <div style={{ fontSize: '13px', color: '#64748b', marginTop: '3px' }}>
            Planned: {visit.planned_date} {visit.actual_date ? `· Actual: ${visit.actual_date}` : ''} · CRA: {visit.cra_name}
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {msg && <span style={{ fontSize: '13px', color: '#10b981' }}>{msg}</span>}
          <span style={{ fontSize: '12px', fontWeight: 600, padding: '4px 12px', borderRadius: '12px', background: '#e0f2fe', color: '#0369a1' }}>{visit.status}</span>
        </div>
      </div>

      {/* Phase Tabs */}
      <div style={{ display: 'flex', borderBottom: '2px solid #e2e8f0' }}>
        {phases.map(p => (
          <button key={p.id} onClick={() => setActivePhase(p.id)}
            style={{ flex: 1, padding: '12px', border: 'none', background: activePhase === p.id ? 'white' : '#f8fafc',
              borderBottom: activePhase === p.id ? '2px solid #2563eb' : '2px solid transparent',
              color: activePhase === p.id ? '#2563eb' : '#64748b', fontWeight: activePhase === p.id ? 700 : 400,
              cursor: 'pointer', fontSize: '13px', marginBottom: '-2px' }}>
            {p.label}
          </button>
        ))}
      </div>

      <div style={{ padding: '24px' }}>

        {/* ── PHASE 1: PRE-VISIT PLANNING ────────────────────────────────── */}
        {activePhase === 'planning' && (
          <div>
            <div style={{ display: 'flex', gap: '12px', marginBottom: '24px', flexWrap: 'wrap' }}>
              {/* Confirm Visit Date */}
              {visit.status === 'Planned' && (
                <button onClick={() => doAction(`/api/ctms/monitoring-visits/${visitId}/confirm`)}
                  disabled={!!actionLoading}
                  style={{ padding: '10px 20px', background: '#2563eb', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '14px' }}>
                  📅 Confirm Visit Date
                </button>
              )}
              {visit.status === 'Confirmed' && (
                <div style={{ padding: '10px 16px', background: '#f0fdf4', border: '1px solid #10b981', borderRadius: '8px', fontSize: '13px', color: '#10b981', fontWeight: 600 }}>
                  ✅ Visit Date Confirmed
                </div>
              )}
              {/* Generate Prep */}
              {!isCompleted && (
                <button onClick={() => doAction(`/api/ctms/monitoring-visits/${visitId}/generate-prep`, 'POST')}
                  disabled={!!actionLoading}
                  style={{ padding: '10px 20px', background: visit.prep_generated ? '#e2e8f0' : '#7c3aed', color: visit.prep_generated ? '#64748b' : 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '14px' }}>
                  🤖 {visit.prep_generated ? 'Regenerate Visit Prep' : 'Generate Visit Prep'}
                </button>
              )}
              {/* Approve Prep */}
              {visit.prep_generated && !visit.prep_approved && !isCompleted && (
                <button onClick={() => doAction(`/api/ctms/monitoring-visits/${visitId}/approve-prep`)}
                  disabled={!!actionLoading}
                  style={{ padding: '10px 20px', background: '#10b981', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '14px' }}>
                  ✅ Approve Prep Agenda
                </button>
              )}
              {visit.prep_approved && (
                <div style={{ padding: '10px 16px', background: '#f0fdf4', border: '1px solid #10b981', borderRadius: '8px', fontSize: '13px', color: '#10b981', fontWeight: 600 }}>
                  ✅ Prep Agenda Approved
                </div>
              )}
            </div>

            {/* Visit Objectives */}
            {visit.visit_objectives && Array.isArray(visit.visit_objectives) && (
              <div style={{ marginBottom: '24px' }}>
                <h4 style={{ margin: '0 0 12px', color: '#1e3a5f', fontSize: '14px' }}>📋 Visit Objectives</h4>
                <div style={{ background: '#f8fafc', borderRadius: '8px', padding: '16px' }}>
                  {visit.visit_objectives.map((obj, i) => (
                    <div key={i} style={{ display: 'flex', gap: '8px', marginBottom: '8px', fontSize: '13px', color: '#374151' }}>
                      <span style={{ color: '#94a3b8' }}>☐</span>
                      <span>{obj}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Subject Priority List */}
            {subjects.length > 0 && (
              <div>
                <h4 style={{ margin: '0 0 12px', color: '#1e3a5f', fontSize: '14px' }}>
                  👥 Subject Priority List ({subjects.length} subjects)
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {subjects.map(s => (
                    <div key={s.subject_id} style={{
                      display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px 16px',
                      background: '#f8fafc', borderRadius: '8px', border: `1px solid ${priorityColor(s.priority)}30`
                    }}>
                      <span style={{ fontSize: '11px', fontWeight: 700, padding: '2px 8px', borderRadius: '10px',
                        background: priorityColor(s.priority) + '20', color: priorityColor(s.priority), whiteSpace: 'nowrap', marginTop: '2px' }}>
                        {s.priority}
                      </span>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
                          <span style={{ fontWeight: 700, fontSize: '14px', color: '#1e3a5f' }}>{s.subject_id}</span>
                          <span style={{ fontSize: '12px', color: '#64748b' }}>SDV: {s.sdv_percent}%</span>
                          <span style={{ fontSize: '11px', padding: '1px 8px', borderRadius: '10px',
                            background: s.sdv_status === 'Complete' ? '#d1fae5' : s.sdv_status === 'In Progress' ? '#fef3c7' : '#f1f5f9',
                            color: s.sdv_status === 'Complete' ? '#10b981' : s.sdv_status === 'In Progress' ? '#f59e0b' : '#94a3b8' }}>
                            {s.sdv_status}
                          </span>
                          <button onClick={() => onSelectSubject(s.subject_id)}
                            style={{ fontSize: '11px', padding: '2px 10px', border: '1px solid #2563eb', background: 'white', color: '#2563eb', borderRadius: '6px', cursor: 'pointer' }}>
                            View Clinical Data →
                          </button>
                        </div>
                        {s.priority_reason && <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>{s.priority_reason}</div>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {!visit.prep_generated && subjects.length === 0 && (
              <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8', background: '#f8fafc', borderRadius: '8px' }}>
                <div style={{ fontSize: '32px', marginBottom: '12px' }}>🤖</div>
                <div style={{ fontWeight: 600, marginBottom: '4px' }}>Visit prep not yet generated</div>
                <div style={{ fontSize: '13px' }}>Click "Generate Visit Prep" to analyse site subjects and create a prioritised review agenda</div>
              </div>
            )}
          </div>
        )}

        {/* ── PHASE 2: DURING VISIT ──────────────────────────────────────── */}
        {activePhase === 'during' && (
          <div>
            {/* Log Finding Button */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h4 style={{ margin: 0, color: '#1e3a5f', fontSize: '14px' }}>Visit Findings ({open_findings.length} open, {resolved_findings.length} resolved)</h4>
              {!isCompleted && (
                <button onClick={() => setShowFindingForm(!showFindingForm)}
                  style={{ padding: '8px 16px', background: '#2563eb', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '13px' }}>
                  + Log Finding
                </button>
              )}
            </div>

            {/* Log Finding Form */}
            {showFindingForm && (
              <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '20px', marginBottom: '20px' }}>
                <h5 style={{ margin: '0 0 16px', color: '#1e3a5f' }}>Log New Finding</h5>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Subject ID</label>
                    <input value={newFinding.subject_id} onChange={e => setNewFinding({...newFinding, subject_id: e.target.value})}
                      placeholder="e.g. 101-901"
                      style={{ width: '100%', padding: '8px', border: '1px solid #e2e8f0', borderRadius: '6px', fontSize: '13px', boxSizing: 'border-box' }} />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Finding Type</label>
                    <select value={newFinding.finding_type} onChange={e => setNewFinding({...newFinding, finding_type: e.target.value})}
                      style={{ width: '100%', padding: '8px', border: '1px solid #e2e8f0', borderRadius: '6px', fontSize: '13px' }}>
                      {['Protocol Deviation', 'Query', 'SDV Finding', 'Action Item'].map(t => <option key={t}>{t}</option>)}
                    </select>
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Severity</label>
                    <select value={newFinding.severity} onChange={e => setNewFinding({...newFinding, severity: e.target.value})}
                      style={{ width: '100%', padding: '8px', border: '1px solid #e2e8f0', borderRadius: '6px', fontSize: '13px' }}>
                      {['Critical', 'Major', 'Minor'].map(s => <option key={s}>{s}</option>)}
                    </select>
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Assigned To</label>
                    <input value={newFinding.assigned_to} onChange={e => setNewFinding({...newFinding, assigned_to: e.target.value})}
                      placeholder="Site staff name"
                      style={{ width: '100%', padding: '8px', border: '1px solid #e2e8f0', borderRadius: '6px', fontSize: '13px', boxSizing: 'border-box' }} />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Due Date</label>
                    <input type="date" value={newFinding.due_date} onChange={e => setNewFinding({...newFinding, due_date: e.target.value})}
                      style={{ width: '100%', padding: '8px', border: '1px solid #e2e8f0', borderRadius: '6px', fontSize: '13px' }} />
                  </div>
                </div>
                <div style={{ marginBottom: '12px' }}>
                  <label style={{ display: 'block', fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Description</label>
                  <textarea value={newFinding.description} onChange={e => setNewFinding({...newFinding, description: e.target.value})}
                    rows={3} placeholder="Describe the finding in detail..."
                    style={{ width: '100%', padding: '8px', border: '1px solid #e2e8f0', borderRadius: '6px', fontSize: '13px', resize: 'vertical', boxSizing: 'border-box' }} />
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button onClick={() => {
                    doAction(`/api/ctms/monitoring-visits/${visitId}/findings`, 'POST', newFinding)
                      .then(() => { setNewFinding({ subject_id: '', finding_type: 'Query', description: '', severity: 'Major', assigned_to: '', due_date: '' }); setShowFindingForm(false); });
                  }}
                    style={{ padding: '8px 20px', background: '#2563eb', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 600, fontSize: '13px' }}>
                    Save Finding
                  </button>
                  <button onClick={() => setShowFindingForm(false)}
                    style={{ padding: '8px 16px', background: '#f1f5f9', color: '#64748b', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px' }}>
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {/* Findings List */}
            {findings.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8', background: '#f8fafc', borderRadius: '8px' }}>
                No findings logged yet. Click "+ Log Finding" to record issues found during the visit.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {findings.map(f => (
                  <div key={f.finding_id} style={{
                    padding: '14px 16px', borderRadius: '8px', border: '1px solid #e2e8f0',
                    borderLeft: `4px solid ${severityColor(f.severity)}`,
                    background: f.status === 'Resolved' ? '#f8fafc' : 'white', opacity: f.status === 'Resolved' ? 0.75 : 1
                  }}>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center', marginBottom: '6px' }}>
                      <span style={{ fontSize: '11px', fontWeight: 700, padding: '2px 8px', borderRadius: '10px',
                        background: severityColor(f.severity) + '20', color: severityColor(f.severity) }}>{f.severity}</span>
                      <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '10px',
                        background: findingTypeColor(f.finding_type) + '15', color: findingTypeColor(f.finding_type) }}>{f.finding_type}</span>
                      {f.subject_id && <span style={{ fontSize: '12px', fontWeight: 600, color: '#1e3a5f' }}>{f.subject_id}</span>}
                      <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '10px',
                        background: f.status === 'Resolved' ? '#d1fae5' : '#fef3c7', color: f.status === 'Resolved' ? '#10b981' : '#f59e0b', marginLeft: 'auto' }}>
                        {f.status}
                      </span>
                    </div>
                    <div style={{ fontSize: '13px', color: '#374151', marginBottom: '6px' }}>{f.description}</div>
                    <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                      Assigned to: {f.assigned_to || 'TBD'} · Due: {f.due_date || 'TBD'}
                      {f.resolved_date && ` · Resolved: ${f.resolved_date}`}
                    </div>
                    {f.status === 'Open' && !isCompleted && (
                      <button onClick={() => doAction(`/api/ctms/findings/${f.finding_id}/resolve`)}
                        style={{ marginTop: '8px', padding: '4px 12px', fontSize: '12px', border: '1px solid #10b981', color: '#10b981', background: 'white', borderRadius: '6px', cursor: 'pointer' }}>
                        Mark Resolved
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Objectives checklist (compact) */}
            {visit.visit_objectives && Array.isArray(visit.visit_objectives) && (
              <div style={{ marginTop: '24px' }}>
                <h4 style={{ margin: '0 0 10px', color: '#1e3a5f', fontSize: '14px' }}>📋 Objectives Checklist</h4>
                <div style={{ background: '#f8fafc', borderRadius: '8px', padding: '14px' }}>
                  {visit.visit_objectives.map((obj, i) => (
                    <div key={i} style={{ display: 'flex', gap: '8px', marginBottom: '6px', fontSize: '13px', color: '#374151' }}>
                      <span style={{ color: '#94a3b8' }}>☐</span><span>{obj}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── PHASE 3: POST-VISIT REPORT ─────────────────────────────────── */}
        {activePhase === 'report' && (
          <div>
            {/* Action buttons */}
            <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap', alignItems: 'center' }}>
              <button onClick={() => doAction(`/api/ctms/monitoring-visits/${visitId}/generate-report`, 'POST')}
                disabled={!!actionLoading}
                style={{ padding: '10px 20px', background: report?.report_status === 'Finalised' ? '#e2e8f0' : '#7c3aed', color: report?.report_status === 'Finalised' ? '#94a3b8' : 'white', border: 'none', borderRadius: '8px', cursor: report?.report_status === 'Finalised' ? 'not-allowed' : 'pointer', fontWeight: 600, fontSize: '14px' }}
                title={report?.report_status === 'Finalised' ? 'Report is finalised' : ''}>
                📝 {report ? 'Regenerate Draft' : 'Generate Visit Report'}
              </button>
              {report && report.report_status !== 'CRA Reviewed' && report.report_status !== 'Finalised' && (
                <button onClick={() => doAction(`/api/ctms/monitoring-visits/${visitId}/report-status?status=CRA+Reviewed&cra_notes=${encodeURIComponent(craNotes)}`)}
                  style={{ padding: '10px 20px', background: '#f59e0b', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '14px' }}>
                  👁 Mark as CRA Reviewed
                </button>
              )}
              {report && report.report_status === 'CRA Reviewed' && (
                <button onClick={() => doAction(`/api/ctms/monitoring-visits/${visitId}/report-status?status=Finalised&cra_notes=${encodeURIComponent(craNotes)}`)}
                  style={{ padding: '10px 20px', background: '#10b981', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '14px' }}>
                  ✅ Finalise Report
                </button>
              )}
              {report && (
                <span style={{ fontSize: '12px', fontWeight: 600, padding: '4px 12px', borderRadius: '12px',
                  background: report.report_status === 'Finalised' ? '#d1fae5' : report.report_status === 'CRA Reviewed' ? '#fef3c7' : '#f1f5f9',
                  color: report.report_status === 'Finalised' ? '#10b981' : report.report_status === 'CRA Reviewed' ? '#f59e0b' : '#94a3b8' }}>
                  {report.report_status}
                </span>
              )}
            </div>

            {/* Report content */}
            {report?.draft_content ? (
              <div>
                <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '20px', marginBottom: '16px', maxHeight: '500px', overflowY: 'auto' }}>
                  <pre style={{ margin: 0, fontFamily: 'inherit', fontSize: '13px', whiteSpace: 'pre-wrap', color: '#374151', lineHeight: '1.6' }}>
                    {report.draft_content}
                  </pre>
                </div>
                {/* CRA Notes */}
                <div style={{ marginBottom: '16px' }}>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#1e3a5f', marginBottom: '6px' }}>
                    ✏️ CRA Notes {report.report_status === 'Finalised' ? '(locked)' : '(add your comments/edits)'}
                  </label>
                  <textarea value={craNotes} onChange={e => setCraNotes(e.target.value)}
                    disabled={report.report_status === 'Finalised'}
                    rows={4} placeholder="Add any additional notes, corrections, or context here..."
                    style={{ width: '100%', padding: '10px', border: '1px solid #e2e8f0', borderRadius: '8px', fontSize: '13px', resize: 'vertical', background: report.report_status === 'Finalised' ? '#f8fafc' : 'white', boxSizing: 'border-box' }} />
                </div>
                {report.cra_notes && report.report_status === 'Finalised' && (
                  <div style={{ background: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: '8px', padding: '12px', fontSize: '13px', color: '#0369a1' }}>
                    <strong>CRA Notes (finalised):</strong> {report.cra_notes}
                  </div>
                )}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '60px', color: '#94a3b8', background: '#f8fafc', borderRadius: '8px' }}>
                <div style={{ fontSize: '36px', marginBottom: '12px' }}>📄</div>
                <div style={{ fontWeight: 600, marginBottom: '4px' }}>No report generated yet</div>
                <div style={{ fontSize: '13px' }}>Click "Generate Visit Report" to auto-draft a monitoring visit report from the visit data and findings</div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================
// COPILOT PANEL — slide-in CRA AI assistant
// ============================================================
function CopilotPanel({ context, onClose }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = React.useRef(null);

  const siteLabel = context.site_id ? `Site ${context.site_id}` : 'Study Level';
  const siteIcon = context.site_id ? '📍' : '📋';

  const starters = context.site_id ? [
    'Show delegation log',
    'What are the open findings for this site?',
    'What do I need for my next visit?',
    'Check TMF compliance',
    'What are the exclusion criteria?',
  ] : [
    'Which sites have critical findings?',
    'What is the dosing regimen?',
    'What are the key exclusion criteria?',
    'What is the primary endpoint?',
    'Summarise the visit schedule',
  ];

  React.useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading]);

  const sendMessage = async (text) => {
    const msg = text || input.trim();
    if (!msg || loading) return;
    setInput('');

    const userMsg = { role: 'user', content: msg };
    const history = messages.map(m => ({
      role: m.role,
      content: m.role === 'user' ? m.content : (m.text || ''),
    }));
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Session-ID': SESSION_ID },
        body: JSON.stringify({
          message: msg,
          site_id: context.site_id || '',
          visit_id: context.visit_id || null,
          history,
        }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', ...data }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', type: 'text', text: 'Sorry, I encountered an error. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  // Render a single assistant message bubble
  const renderAssistantContent = (msg) => {
    if ((msg.type === 'document' || msg.type === 'document_fetch') && msg.document) {
      const doc = msg.document;
      const statusColors = { Present: '#16a34a', Missing: '#dc2626', Expiring: '#d97706', Superseded: '#9333ea' };
      const statusBg    = { Present: '#f0fdf4', Missing: '#fef2f2', Expiring: '#fffbeb', Superseded: '#faf5ff' };
      return (
        <div>
          {msg.text && <p style={{ margin: '0 0 10px', fontSize: '13px', lineHeight: '1.5' }}>{msg.text}</p>}
          <div style={{
            background: doc.status ? statusBg[doc.status] || '#f8fafc' : '#f8fafc',
            border: `1px solid ${doc.status ? statusColors[doc.status] || '#e2e8f0' : '#e2e8f0'}`,
            borderRadius: '8px', padding: '12px',
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px' }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: '13px', color: '#1e3a5f', marginBottom: '4px' }}>
                  📄 {doc.title || doc.document_type || 'Document'}
                </div>
                {doc.version && <div style={{ fontSize: '12px', color: '#64748b' }}>Version: {doc.version}</div>}
                {doc.status && (
                  <div style={{ marginTop: '4px' }}>
                    <span style={{
                      background: statusColors[doc.status] || '#94a3b8', color: 'white',
                      fontSize: '11px', padding: '2px 8px', borderRadius: '12px', fontWeight: 600,
                    }}>{doc.status}</span>
                  </div>
                )}
              </div>
              {doc.url && (
                <button
                  onClick={() => window.open(doc.url, '_blank')}
                  style={{
                    background: '#2563eb', color: 'white', border: 'none',
                    borderRadius: '6px', padding: '6px 12px', fontSize: '12px',
                    cursor: 'pointer', fontWeight: 600, whiteSpace: 'nowrap', flexShrink: 0,
                  }}
                >
                  Open PDF ↗
                </button>
              )}
            </div>
          </div>
        </div>
      );
    }

    if (msg.type === 'table' && msg.table) {
      const { headers, rows } = msg.table;
      return (
        <div>
          {msg.text && <p style={{ margin: '0 0 10px', fontSize: '13px', lineHeight: '1.5' }}>{msg.text}</p>}
          <div style={{ overflowX: 'auto', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr style={{ background: '#1e3a5f' }}>
                  {headers.map((h, i) => (
                    <th key={i} style={{ padding: '8px 10px', color: 'white', textAlign: 'left', fontWeight: 600, whiteSpace: 'nowrap' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, ri) => (
                  <tr key={ri} style={{ background: ri % 2 === 0 ? 'white' : '#f8fafc', borderBottom: '1px solid #f1f5f9' }}>
                    {row.map((cell, ci) => (
                      <td key={ci} style={{ padding: '7px 10px', color: '#374151', verticalAlign: 'top' }}>{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      );
    }

    // Default: text
    return (
      <p style={{ margin: 0, fontSize: '13px', lineHeight: '1.6', whiteSpace: 'pre-wrap', color: '#1e293b' }}>
        {msg.text || ''}
      </p>
    );
  };

  return (
    <div style={{
      width: '400px', flexShrink: 0,
      display: 'flex', flexDirection: 'column',
      background: '#f8fafc', borderLeft: '2px solid #e2e8f0',
      height: 'calc(100vh - 56px)', position: 'sticky', top: '56px',
      fontFamily: 'inherit',
    }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #1e3a5f 0%, #1e40af 100%)',
        color: 'white', padding: '14px 16px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        flexShrink: 0,
      }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: '15px' }}>💬 CRA Copilot</div>
          <div style={{ fontSize: '11px', opacity: 0.8, marginTop: '2px' }}>
            {siteIcon} {siteLabel} · NVX-1218.22
          </div>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'rgba(255,255,255,0.15)', border: 'none', color: 'white',
            borderRadius: '6px', padding: '4px 10px', cursor: 'pointer',
            fontSize: '16px', lineHeight: 1,
          }}
          title="Close Copilot"
        >×</button>
      </div>

      {/* Messages area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>

        {/* Empty state — starter suggestions */}
        {messages.length === 0 && !loading && (
          <div>
            <div style={{ textAlign: 'center', marginBottom: '20px' }}>
              <div style={{ fontSize: '32px', marginBottom: '8px' }}>🤖</div>
              <div style={{ fontWeight: 600, color: '#1e3a5f', fontSize: '14px' }}>Hi, I'm your CRA Copilot!</div>
              <div style={{ color: '#64748b', fontSize: '12px', marginTop: '4px' }}>
                {context.site_id
                  ? 'Ask me about site data, findings, documents, or protocol.'
                  : 'No site selected — I can answer study-level and protocol questions.'}
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {starters.map((s, i) => (
                <button
                  key={i}
                  onClick={() => sendMessage(s)}
                  style={{
                    background: 'white', border: '1px solid #e2e8f0', borderRadius: '8px',
                    padding: '10px 14px', textAlign: 'left', cursor: 'pointer',
                    fontSize: '13px', color: '#374151', fontWeight: 500,
                    transition: 'border-color 0.15s', fontFamily: 'inherit',
                  }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = '#2563eb'}
                  onMouseLeave={e => e.currentTarget.style.borderColor = '#e2e8f0'}
                >
                  💡 {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message bubbles */}
        {messages.map((msg, i) => (
          <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{
              maxWidth: '90%',
              background: msg.role === 'user' ? '#2563eb' : 'white',
              color: msg.role === 'user' ? 'white' : '#1e293b',
              borderRadius: msg.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
              padding: '10px 14px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
              border: msg.role === 'user' ? 'none' : '1px solid #f1f5f9',
              fontSize: '13px',
            }}>
              {msg.role === 'user' ? (
                <p style={{ margin: 0, lineHeight: '1.5' }}>{msg.content}</p>
              ) : (
                renderAssistantContent(msg)
              )}
            </div>
            <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '3px', paddingLeft: '4px', paddingRight: '4px' }}>
              {msg.role === 'user' ? 'You' : '🤖 Copilot'}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {loading && (
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
            <div style={{
              background: 'white', border: '1px solid #f1f5f9', borderRadius: '12px 12px 12px 2px',
              padding: '12px 16px', boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
            }}>
              <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                {[0, 1, 2].map(n => (
                  <div key={n} style={{
                    width: '7px', height: '7px', borderRadius: '50%', background: '#94a3b8',
                    animation: `bounce 1.2s ${n * 0.2}s ease-in-out infinite`,
                  }} />
                ))}
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div style={{
        padding: '12px 16px', borderTop: '1px solid #e2e8f0',
        background: 'white', flexShrink: 0,
      }}>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask about protocol, data, findings, documents..."
            rows={2}
            style={{
              flex: 1, padding: '10px 12px', border: '1px solid #e2e8f0', borderRadius: '8px',
              fontSize: '13px', resize: 'none', fontFamily: 'inherit', outline: 'none',
              lineHeight: '1.5', color: '#1e293b',
            }}
            onFocus={e => e.target.style.borderColor = '#2563eb'}
            onBlur={e => e.target.style.borderColor = '#e2e8f0'}
          />
          <button
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
            style={{
              background: loading || !input.trim() ? '#94a3b8' : '#2563eb',
              color: 'white', border: 'none', borderRadius: '8px',
              padding: '10px 14px', cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
              fontSize: '16px', flexShrink: 0, height: '52px',
              transition: 'background 0.15s',
            }}
          >
            {loading ? '⏳' : '➤'}
          </button>
        </div>
        <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '6px', textAlign: 'center' }}>
          Press Enter to send · Shift+Enter for new line
        </div>
      </div>

      {/* Bounce animation via inline style tag */}
      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); }
          40% { transform: translateY(-6px); }
        }
      `}</style>
    </div>
  );
}

export default App;
