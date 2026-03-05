import React, { useState } from 'react';
import './App.css';

// Usage Pill — compact indicator for top bar
function UsagePill() {
  const [usage, setUsage] = useState(null);
  const [expanded, setExpanded] = useState(false);

  React.useEffect(() => {
    const fetch_usage = () => {
      fetch('/api/usage').then(r => r.json()).then(setUsage).catch(() => {});
    };
    fetch_usage();
    const interval = setInterval(fetch_usage, 5000);
    return () => clearInterval(interval);
  }, []);

  if (!usage || usage.total_api_calls === 0) return null;

  const isWarning = usage.estimated_cost_usd > 0.10;

  return (
    <div style={{ position: 'relative' }}>
      <button
        className={`usage-pill${isWarning ? ' warning' : ''}`}
        onClick={() => setExpanded(e => !e)}
      >
        <span className={`usage-dot${isWarning ? ' warning' : ''}`} />
        AI: {usage.total_tokens.toLocaleString()} tokens · {usage.estimated_cost_display}
      </button>
      {expanded && (
        <div style={{
          position: 'absolute', right: 0, top: '32px', zIndex: 200,
          background: '#0A2540', color: '#E2E8F0', borderRadius: '6px',
          padding: '12px 16px', fontSize: '12px', fontFamily: 'monospace',
          whiteSpace: 'nowrap', boxShadow: '0 4px 16px rgba(0,0,0,0.25)',
          minWidth: '320px'
        }}>
          <div style={{ marginBottom: '6px', fontWeight: 700, color: '#fff', fontSize: '11px', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
            API Usage This Session
          </div>
          <div>Input: {usage.total_input_tokens.toLocaleString()} tokens × $3.00/M = ${((usage.total_input_tokens / 1e6) * 3).toFixed(6)}</div>
          <div>Output: {usage.total_output_tokens.toLocaleString()} tokens × $15.00/M = ${((usage.total_output_tokens / 1e6) * 15).toFixed(6)}</div>
          <div style={{ marginTop: '6px', borderTop: '1px solid rgba(255,255,255,0.15)', paddingTop: '6px' }}>
            Calls: {usage.total_api_calls} &nbsp;|&nbsp; LLM evals: {usage.llm_rule_evaluations} &nbsp;|&nbsp;
            <strong style={{ color: isWarning ? '#FBBF24' : '#6EE7B7' }}> {usage.estimated_cost_display}</strong>
          </div>
          <button
            onClick={() => fetch('/api/usage/reset', { method: 'POST' }).then(() => { setUsage(null); setExpanded(false); })}
            style={{ marginTop: '8px', padding: '2px 10px', fontSize: '11px', background: '#C0392B', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
          >
            Reset
          </button>
        </div>
      )}
    </div>
  );
}

// SVG icons — inline, no icon library needed
const Icons = {
  dashboard: <svg viewBox="0 0 16 16" fill="currentColor" className="nav-item-icon"><path d="M2 2h5v5H2V2zm0 7h5v5H2V9zm7-7h5v5H9V2zm0 7h5v5H9V9z"/></svg>,
  subjects:  <svg viewBox="0 0 16 16" fill="currentColor" className="nav-item-icon"><path d="M8 8a3 3 0 100-6 3 3 0 000 6zm-5 6a5 5 0 0110 0H3z"/></svg>,
  rules:     <svg viewBox="0 0 16 16" fill="currentColor" className="nav-item-icon"><path d="M2 3h12v1.5H2V3zm0 4h12v1.5H2V7zm0 4h8v1.5H2V11z"/></svg>,
  execute:   <svg viewBox="0 0 16 16" fill="currentColor" className="nav-item-icon"><path d="M4 2l10 6-10 6V2z"/></svg>,
  results:   <svg viewBox="0 0 16 16" fill="currentColor" className="nav-item-icon"><path d="M2 2h12v12H2V2zm2 4v6h2V6H4zm3 2v4h2V8H7zm3-3v7h2V5h-2z"/></svg>,
  violations:<svg viewBox="0 0 16 16" fill="currentColor" className="nav-item-icon"><path d="M8 1L1 14h14L8 1zm0 3l4.5 8h-9L8 4zm-.75 3v2.5h1.5V7h-1.5zm0 3v1.5h1.5V10h-1.5z"/></svg>,
  site:      <svg viewBox="0 0 16 16" fill="currentColor" className="nav-item-icon"><path d="M8 1a4 4 0 00-4 4c0 3 4 9 4 9s4-6 4-9a4 4 0 00-4-4zm0 5.5a1.5 1.5 0 110-3 1.5 1.5 0 010 3z"/></svg>,
  risk:      <svg viewBox="0 0 16 16" fill="currentColor" className="nav-item-icon"><path d="M8 1L1 14h14L8 1zm0 3l4.5 8h-9L8 4zm-.75 3v2.5h1.5V7h-1.5zm0 3v1.5h1.5V10h-1.5z"/><circle cx="12" cy="4" r="3.5" fill="#E67E22"/><text x="12" y="5.5" textAnchor="middle" fontSize="4" fill="white" fontWeight="bold">!</text></svg>,
  copilot:   <svg viewBox="0 0 16 16" fill="currentColor" style={{ width:14, height:14, flexShrink:0 }}><path d="M14 1H2a1 1 0 00-1 1v9a1 1 0 001 1h2v3l4-3h6a1 1 0 001-1V2a1 1 0 00-1-1z"/></svg>,
};

const VIEW_META = {
  dashboard:        { label: 'Dashboard',    icon: Icons.dashboard },
  subjects:         { label: 'Subjects',     icon: Icons.subjects },
  'subject-detail': { label: 'Subjects',     icon: Icons.subjects },
  rules:            { label: 'Rules',        icon: Icons.rules },
  execute:          { label: 'Execute',      icon: Icons.execute },
  results:          { label: 'Results',      icon: Icons.results },
  violations:       { label: 'Violations',   icon: Icons.violations },
  site:             { label: 'My Sites',     icon: Icons.site },
  risk:             { label: 'Risk',         icon: Icons.risk },
  'risk-rankings':  { label: 'Risk',         icon: Icons.risk },
  'risk-site':      { label: 'Risk',         icon: Icons.risk },
};

// Main App Component
function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [selectedRiskSite, setSelectedRiskSite] = useState(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [chatContext, setChatContext] = useState({ site_id: '', visit_id: null });

  const navItems = [
    { id: 'dashboard',  label: 'Dashboard',  icon: Icons.dashboard },
    { id: 'subjects',   label: 'Subjects',   icon: Icons.subjects },
    { id: 'rules',      label: 'Rules',      icon: Icons.rules },
    { id: 'execute',    label: 'Execute',    icon: Icons.execute },
    { id: 'results',    label: 'Results',    icon: Icons.results },
    { id: 'violations', label: 'Violations', icon: Icons.violations },
    { id: 'site',       label: 'My Sites',   icon: Icons.site },
    { id: 'risk',       label: 'Risk',       icon: Icons.risk },
  ];

  const breadcrumb = VIEW_META[currentView] || VIEW_META['dashboard'];

  return (
    <div className="App">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">+</div>
          <div className="sidebar-brand-text">
            <span className="sidebar-brand-name">Trial Monitor</span>
            <span className="sidebar-brand-sub">NVX-1218.22</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="sidebar-section-label">Study</div>
          {navItems.map(item => (
            <button
              key={item.id}
              className={`nav-item${
                currentView === item.id ||
                (item.id === 'subjects' && currentView === 'subject-detail') ||
                (item.id === 'risk' && (currentView === 'risk-rankings' || currentView === 'risk-site'))
                  ? ' active' : ''}`}
              onClick={() => setCurrentView(item.id)}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button
            className={`copilot-btn${chatOpen ? ' active' : ''}`}
            onClick={() => setChatOpen(o => !o)}
          >
            {Icons.copilot}
            AI Copilot
          </button>
        </div>
      </aside>

      {/* Right: top bar + scrollable content */}
      <div className="content-area">
        {/* Top bar */}
        <div className="topbar">
          <div className="topbar-breadcrumb">
            <span>NVX-1218.22</span>
            <span className="topbar-breadcrumb-sep">/</span>
            <span className="topbar-breadcrumb-current">{breadcrumb.label}</span>
            {currentView === 'subject-detail' && selectedSubject && (
              <>
                <span className="topbar-breadcrumb-sep">/</span>
                <span className="topbar-breadcrumb-current">{selectedSubject}</span>
              </>
            )}
          </div>
          <div className="topbar-right">
            <UsagePill />
          </div>
        </div>

        {/* Content + optional copilot panel */}
        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          <main className="main-content">
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
              />
            )}
            {currentView === 'risk' && (
              <RiskDashboard
                onViewRankings={() => setCurrentView('risk-rankings')}
                onViewSite={(id) => { setSelectedRiskSite(id); setCurrentView('risk-site'); }}
              />
            )}
            {currentView === 'risk-rankings' && (
              <SiteRankings
                onBack={() => setCurrentView('risk')}
                onViewSite={(id) => { setSelectedRiskSite(id); setCurrentView('risk-site'); }}
              />
            )}
            {currentView === 'risk-site' && selectedRiskSite && (
              <SiteRiskDetail
                siteId={selectedRiskSite}
                onBack={() => setCurrentView('risk-rankings')}
                onOpenInMySites={() => setCurrentView('site')}
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
    </div>
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
      <div className="page-header">
        <div>
          <div className="page-title">Study Overview</div>
          <div className="page-subtitle">Protocol NVX-1218.22 — NovaPlex-450 in Advanced NSCLC</div>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{stats?.subjects || 0}</div>
          <div className="stat-label">Total Subjects</div>
        </div>
        <div className="stat-card minor">
          <div className="stat-value">{stats?.subjects_enrolled || 0}</div>
          <div className="stat-label">Enrolled</div>
        </div>
        <div className="stat-card major">
          <div className="stat-value">{stats?.adverse_events || 0}</div>
          <div className="stat-label">Adverse Events</div>
        </div>
        <div className="stat-card critical">
          <div className="stat-value">{stats?.serious_adverse_events || 0}</div>
          <div className="stat-label">Serious AEs</div>
        </div>
        <div className="stat-card info">
          <div className="stat-value">{stats?.open_queries || 0}</div>
          <div className="stat-label">Open Queries</div>
        </div>
        <div className="stat-card neutral">
          <div className="stat-value">{stats?.protocol_deviations || 0}</div>
          <div className="stat-label">Deviations</div>
        </div>
      </div>

      <div className="quick-actions">
        <h3>Quick Actions</h3>
        <div className="actions-grid">
          <ActionCard
            title="Execute Rules"
            description="Run active rules against study subjects"
            iconSvg={<svg viewBox="0 0 16 16" fill="#2D6BE4" width="18" height="18"><path d="M4 2l10 6-10 6V2z"/></svg>}
            action="execute"
            onNavigate={onNavigate}
          />
          <ActionCard
            title="Violations"
            description="Review and manage flagged protocol issues"
            iconSvg={<svg viewBox="0 0 16 16" fill="#C0392B" width="18" height="18"><path d="M8 1L1 14h14L8 1zm0 3l4.5 8h-9L8 4zm-.75 3v2.5h1.5V7h-1.5zm0 3v1.5h1.5V10h-1.5z"/></svg>}
            action="violations"
            onNavigate={onNavigate}
          />
          <ActionCard
            title="Rule Library"
            description="Configure and manage protocol rules"
            iconSvg={<svg viewBox="0 0 16 16" fill="#2D6BE4" width="18" height="18"><path d="M2 3h12v1.5H2V3zm0 4h12v1.5H2V7zm0 4h8v1.5H2V11z"/></svg>}
            action="rules"
            onNavigate={onNavigate}
          />
        </div>
      </div>
    </div>
  );
}

function ActionCard({ title, description, iconSvg, action, onNavigate }) {
  return (
    <div className="action-card" onClick={() => onNavigate && onNavigate(action)}>
      <div className="action-icon-wrap">{iconSvg}</div>
      <div>
        <h4>{title}</h4>
        <p>{description}</p>
      </div>
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
    exclusion:      { label: 'Exclusion',  color: '#C0392B' },
    inclusion:      { label: 'Inclusion',  color: '#1E7E4A' },
    safety_ae:      { label: 'AE Safety',  color: '#C96A00' },
    safety_lab:     { label: 'Lab Safety', color: '#2563EB' },
    protocol_visit: { label: 'Deviations', color: '#5B6E8C' },
    protocol_dose:  { label: 'Deviations', color: '#5B6E8C' },
    efficacy:       { label: 'Endpoints',  color: 'var(--color-blue-dk)' },
  };

  // Unique categories present in loaded rules, mapped to display groups
  const categoryGroups = [
    { key: 'all',       label: 'All' },
    { key: 'exclusion', label: 'Exclusion' },
    { key: 'inclusion', label: 'Inclusion' },
    { key: 'safety',    label: 'AE Safety' },
    { key: 'lab',       label: 'Lab Safety' },
    { key: 'deviation', label: 'Deviations' },
    { key: 'efficacy',  label: 'Endpoints' },
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

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">Rule Library</div>
          <div className="page-subtitle">
            {rules.filter(r => r.status === 'active').length} active rules across {Object.keys(categoryMeta).filter(c => rules.some(r => r.category === c)).length} categories
          </div>
        </div>
        <div className="filter-row" style={{ margin: 0 }}>
          {[['all', 'All'], ['active', 'Active'], ['inactive', 'Inactive']].map(([val, label]) => (
            <button key={val} className={`filter-pill${statusFilter === val ? ' active' : ''}`}
              onClick={() => setStatusFilter(val)}>
              {label} ({val === 'all' ? rules.length : rules.filter(r => r.status === val).length})
            </button>
          ))}
        </div>
      </div>

      {/* Category filter row */}
      <div className="filter-row" style={{ marginBottom: '20px' }}>
        {categoryGroups.map(({ key, label }) => {
          const count = countFor(key);
          return (
            <button key={key} className={`filter-pill${categoryFilter === key ? ' active' : ''}`}
              onClick={() => setCategoryFilter(key)}
              style={{ opacity: count === 0 ? 0.4 : 1 }}>
              {label} ({count})
            </button>
          );
        })}
      </div>

      {filteredRules.length === 0 ? (
        <div className="empty-state">No rules match the selected filters.</div>
      ) : (
        <div className="rules-list">
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

  const severityBadge = {
    critical: 'badge-critical',
    major:    'badge-major',
    minor:    'badge-minor',
    info:     'badge-info',
  };

  const typeBadge = {
    llm_with_tools: 'badge-neutral',
    deterministic:  'badge-blue',
  };

  const cat = categoryMeta[rule.category] || { label: rule.category, color: 'var(--color-muted)' };

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
          <div className="rule-id">{rule.rule_id}</div>
          <div className="rule-name">{rule.name}</div>
          <div className="rule-description">{rule.description}</div>
        </div>

        <div className="rule-meta">
          <span className={`badge ${severityBadge[rule.severity] || 'badge-neutral'}`}>{rule.severity}</span>
          <span className={`badge ${rule.status === 'active' ? 'badge-minor' : 'badge-neutral'}`}>{rule.status}</span>
          <span className="badge badge-blue">{cat.label}</span>
        </div>
      </div>

      {expanded && (
        <div className="rule-details">
          <div className="detail-row">
            <span className="detail-label">Category</span>
            <span className="detail-value">{cat.label} <span className="text-muted text-xs">({rule.category})</span></span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Evaluation Type</span>
            <span className="detail-value">
              <span className={`badge ${typeBadge[rule.evaluation_type] || 'badge-neutral'}`}>
                {rule.evaluation_type === 'llm_with_tools' ? 'LLM + Tools' : 'Deterministic'}
              </span>
            </span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Template</span>
            <span className="detail-value" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {rule.template_name}
              <button className={`btn btn-sm ${templateVisible ? 'btn-ghost' : 'btn-primary'}`} onClick={handleViewTemplate}>
                {templateLoading ? '…' : templateVisible ? 'Hide' : 'View Template'}
              </button>
            </span>
          </div>
          {rule.protocol_reference && (
            <div className="detail-row">
              <strong>Protocol Reference:</strong> {rule.protocol_reference}
            </div>
          )}

          <div className="detail-row">
            <span className="detail-label">Sample Input</span>
            <span className="detail-value" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button className={`btn btn-sm ${sampleVisible ? 'btn-ghost' : 'btn-primary'}`} onClick={handleViewSampleInput}>
                {sampleLoading ? '…' : sampleVisible ? 'Hide' : 'View Sample'}
              </button>
              <span className="text-muted text-xs">subject 101-001</span>
            </span>
          </div>

          {sampleVisible && (
            <div style={{
              marginTop: '10px', borderRadius: '6px', overflow: 'hidden',
              border: `1px solid ${sampleError ? 'var(--color-major)' : 'var(--color-border)'}`,
            }}>
              {sampleError ? (
                <p style={{ margin: 0, color: 'var(--color-major)', fontSize: '12px', padding: '10px 12px' }}>
                  {sampleError}
                </p>
              ) : sampleInput && (
                <>
                  <div style={{ padding: '8px 12px', background: 'var(--color-minor-bg)', borderBottom: '1px solid var(--color-border-lt)', fontSize: '12px', fontWeight: 600, color: 'var(--color-minor)' }}>
                    Sample Input — {sampleInput.template}
                  </div>
                  <pre style={{
                    background: 'var(--color-navy)', color: '#E2E8F0', padding: '12px',
                    fontSize: '11px', overflowX: 'auto', whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word', maxHeight: '360px', overflowY: 'auto',
                    fontFamily: 'var(--font-mono)', margin: 0
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
              background: templateError ? 'var(--color-major-bg)' : 'var(--color-surface)',
              border: `1px solid ${templateError ? '#fed7aa' : 'var(--color-border)'}`,
              borderRadius: '8px',
              padding: '16px'
            }}>
              {templateError ? (
                <p style={{ margin: 0, color: '#9a3412', fontSize: '13px' }}>
                  ⚠️ {templateError}
                </p>
              ) : template && (
                <>
                  <h4 style={{ margin: '0 0 10px', color: 'var(--color-navy)' }}>
                    📄 {template.name || rule.template_name}
                  </h4>
                  {template.description && (
                    <p style={{ color: 'var(--color-text-soft)', marginBottom: '12px', fontSize: '14px' }}>
                      {template.description}
                    </p>
                  )}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    {template.suitable_for && (
                      <div>
                        <strong style={{ fontSize: '13px', color: 'var(--color-muted)' }}>✅ Suitable For</strong>
                        <ul style={{ margin: '6px 0 0', paddingLeft: '16px', fontSize: '13px' }}>
                          {template.suitable_for.map((s, i) => <li key={i}>{s}</li>)}
                        </ul>
                      </div>
                    )}
                    {template.tools_available && (
                      <div>
                        <strong style={{ fontSize: '13px', color: 'var(--color-muted)' }}>🔧 Tools Available</strong>
                        <ul style={{ margin: '6px 0 0', paddingLeft: '16px', fontSize: '13px', fontFamily: 'monospace' }}>
                          {template.tools_available.map((t, i) => <li key={i}>{t}</li>)}
                        </ul>
                      </div>
                    )}
                    {template.output_fields && (
                      <div>
                        <strong style={{ fontSize: '13px', color: 'var(--color-muted)' }}>📤 Output Fields</strong>
                        <div style={{ marginTop: '6px', display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                          {template.output_fields.map((f, i) => (
                            <span key={i} style={{
                              background: '#e0f2fe', color: 'var(--color-blue-dk)',
                              borderRadius: '4px', padding: '2px 7px', fontSize: '12px'
                            }}>{f}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    {template.phase_logic && (
                      <div>
                        <strong style={{ fontSize: '13px', color: 'var(--color-muted)' }}>🔄 Phase Logic</strong>
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
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">Subjects</div>
          <div className="page-subtitle">{subjects.length} subjects across all sites</div>
        </div>
      </div>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Subject ID</th>
              <th>Site</th>
              <th>Treatment Arm</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {subjects.map(subject => {
              const statusKey = (subject.study_status || '').toLowerCase().replace(' ', '');
              return (
                <tr key={subject.subject_id}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: '12px' }}>{subject.subject_id}</td>
                  <td>{subject.site_id}</td>
                  <td style={{ fontSize: '12px' }}>{subject.treatment_arm_name}</td>
                  <td>
                    <span className={`badge badge-${statusKey}`}>{subject.study_status}</span>
                  </td>
                  <td>
                    <button className="btn btn-ghost btn-sm" onClick={() => onSelectSubject(subject.subject_id)}>
                      View
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
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

  const sevColor = { critical: '#C0392B', major: '#C96A00', minor: '#1E7E4A', info: '#2563EB' };
  const tabs = [
    { id: 'overview',   label: 'Overview' },
    { id: 'visits',     label: 'Visits' },
    { id: 'labs',       label: 'Labs' },
    { id: 'aes',        label: 'Adverse Events' },
    { id: 'conmeds',    label: 'Conmeds' },
    { id: 'violations', label: 'Violations' },
  ];

  const statusKey = (subject?.study_status || '').toLowerCase().replace(' ', '');

  if (loading) return <div className="loading">Loading subject {subjectId}...</div>;

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <button onClick={onBack} className="back-button">← Back</button>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '16px', fontWeight: 700, color: 'var(--color-text)' }}>Subject {subjectId}</span>
            <span className={`badge badge-${statusKey}`}>{subject?.study_status}</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-muted)', marginTop: '2px' }}>
            {subject?.treatment_arm_name} &nbsp;·&nbsp; Site {subject?.site_id}
          </div>
        </div>
      </div>

      {/* Tab bar */}
      <div className="tab-bar">
        {tabs.map(t => (
          <button key={t.id} className={`tab-btn${activeTab === t.id ? ' active' : ''}`} onClick={() => loadTab(t.id)}>{t.label}</button>
        ))}
      </div>

      {/* ── OVERVIEW ── */}
      {activeTab === 'overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          {/* Demographics */}
          <div style={{ background: 'white', border: '1px solid var(--color-border)', borderRadius: '8px', padding: '16px' }}>
            <h3 style={{ margin: '0 0 12px', fontSize: '15px', color: 'var(--color-navy)' }}>👤 Demographics</h3>
            {[
              ['Age', demo?.age ? `${demo.age} years` : '—'],
              ['Sex', demo?.sex || '—'],
              ['Race / Ethnicity', [demo?.race, demo?.ethnicity].filter(Boolean).join(' / ') || '—'],
              ['Weight / BMI', demo?.weight_kg ? `${demo.weight_kg} kg / BMI ${demo?.bmi}` : '—'],
              ['ECOG Status', demo?.ecog_performance_status !== undefined ? `PS ${demo.ecog_performance_status}` : '—'],
              ['Smoking', demo?.smoking_status ? `${demo.smoking_status}${demo.smoking_pack_years ? ` (${demo.smoking_pack_years} pack-yrs)` : ''}` : '—'],
            ].map(([k, v]) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', borderBottom: '1px solid var(--color-surface)', fontSize: '13px' }}>
                <span style={{ color: 'var(--color-muted)' }}>{k}</span>
                <span style={{ fontWeight: 600 }}>{v}</span>
              </div>
            ))}
          </div>

          {/* Study info */}
          <div style={{ background: 'white', border: '1px solid var(--color-border)', borderRadius: '8px', padding: '16px' }}>
            <h3 style={{ margin: '0 0 12px', fontSize: '15px', color: 'var(--color-navy)' }}>📋 Study Information</h3>
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
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', borderBottom: '1px solid var(--color-surface)', fontSize: '13px' }}>
                <span style={{ color: 'var(--color-muted)' }}>{k}</span>
                <span style={{ fontWeight: 600, textAlign: 'right', maxWidth: '55%' }}>{v}</span>
              </div>
            ))}
          </div>

          {/* Medical History */}
          <div style={{ background: 'white', border: '1px solid var(--color-border)', borderRadius: '8px', padding: '16px', gridColumn: '1 / -1' }}>
            <h3 style={{ margin: '0 0 12px', fontSize: '15px', color: 'var(--color-navy)' }}>🏥 Medical History ({medHistory.length})</h3>
            {medHistory.length === 0 ? <p style={{ color: 'var(--color-muted)', fontSize: '13px' }}>None recorded</p> : (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ background: 'var(--color-surface)' }}>
                    {['Condition', 'Category', 'Diagnosis Date', 'Status', 'Notes'].map(h => (
                      <th key={h} style={{ padding: '8px 10px', textAlign: 'left', border: '1px solid var(--color-border)', color: 'var(--color-text-soft)' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {medHistory.map((m, i) => (
                    <tr key={i} style={{ background: i % 2 === 0 ? 'white' : 'var(--color-surface)' }}>
                      <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)', fontWeight: 600 }}>{m.condition}</td>
                      <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)', color: 'var(--color-neutral)' }}>{m.condition_category}</td>
                      <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)' }}>{m.diagnosis_date || '—'}</td>
                      <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)' }}>
                        <span style={{ padding: '2px 7px', borderRadius: '99px', fontSize: '11px', fontWeight: 700,
                          background: m.ongoing ? '#fee2e2' : '#dcfce7', color: m.ongoing ? 'var(--color-critical)' : 'var(--color-minor)' }}>
                          {m.ongoing ? 'Ongoing' : 'Resolved'}
                        </span>
                      </td>
                      <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)', color: 'var(--color-muted)', fontSize: '12px' }}>{m.condition_notes || '—'}</td>
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
            <div style={{ textAlign: 'center', padding: '60px', color: 'var(--color-minor)', fontSize: '16px' }}>
              ✅ No violations found for this subject in the latest evaluation run.
              {!violations.job_id && <p style={{ color: 'var(--color-muted)', fontSize: '13px', marginTop: '8px' }}>No evaluation has been run yet. Go to Execute to run rules.</p>}
            </div>
          ) : (
            <>
              <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', flexWrap: 'wrap' }}>
                {[['Total', violations.violations_found, 'var(--color-text)'],
                  ['Critical', violations.violations.filter(v => v.severity === 'critical').length, 'var(--color-critical)'],
                  ['Major', violations.violations.filter(v => v.severity === 'major').length, 'var(--color-major)'],
                  ['Minor', violations.violations.filter(v => v.severity === 'minor').length, 'var(--color-minor)']
                ].map(([label, count, color]) => (
                  <div key={label} className="stat-card" style={{ minWidth: '80px', flex: 1 }}>
                    <div className="stat-value" style={{ color }}>{count}</div>
                    <div className="stat-label">{label}</div>
                  </div>
                ))}
                {violations.run_date && (
                  <div style={{ fontSize: '12px', color: 'var(--color-muted)', alignSelf: 'center', marginLeft: 'auto' }}>
                    Last run: {violations.run_date?.substring(0, 19)}
                  </div>
                )}
              </div>
              {violations.violations.map((v, i) => (
                <div key={i} style={{
                  border: `1px solid ${sevColor[v.severity] || 'var(--color-border)'}33`,
                  borderLeft: `4px solid ${sevColor[v.severity] || 'var(--color-muted)'}`,
                  borderRadius: '6px', padding: '14px', marginBottom: '10px', background: 'white'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '14px' }}>{v.rule_id}</span>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <span style={{ padding: '2px 8px', borderRadius: '99px', fontSize: '11px', fontWeight: 700, background: sevColor[v.severity] || 'var(--color-muted)', color: 'white' }}>{v.severity}</span>
                      <span style={{ padding: '2px 8px', borderRadius: '99px', fontSize: '11px', background: 'var(--color-neutral-bg)', color: 'var(--color-neutral)', fontWeight: 600 }}>{v.action_required}</span>
                    </div>
                  </div>
                  {v.evidence && v.evidence.length > 0 && (
                    <ul style={{ margin: '0 0 8px', paddingLeft: '18px', fontSize: '12px', color: 'var(--color-text)' }}>
                      {v.evidence.map((e, ei) => <li key={ei}>{e}</li>)}
                    </ul>
                  )}
                  <div style={{ fontSize: '12px', color: 'var(--color-muted)', background: 'var(--color-surface)', padding: '8px 10px', borderRadius: '4px', lineHeight: 1.5 }}>
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
    <div style={{ border: `1px solid ${isMissed ? 'var(--color-critical-bg)' : isLate ? 'var(--color-major-bg)' : 'var(--color-border)'}`, borderRadius: '8px', marginBottom: '8px', overflow: 'hidden' }}>
      <div onClick={() => setOpen(!open)} style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '12px 16px', cursor: 'pointer',
        background: isMissed ? 'var(--color-critical-bg)' : isLate ? 'var(--color-major-bg)' : 'var(--color-surface)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontWeight: 700, fontSize: '14px', color: 'var(--color-navy)' }}>{visit.visit_name}</span>
          {isMissed && <span style={{ fontSize: '11px', background: '#fee2e2', color: 'var(--color-critical)', padding: '1px 7px', borderRadius: '99px', fontWeight: 700 }}>MISSED</span>}
          {isLate && !isMissed && <span style={{ fontSize: '11px', background: 'var(--color-major-bg)', color: 'var(--color-major)', padding: '1px 7px', borderRadius: '99px', fontWeight: 700 }}>LATE</span>}
          <span style={{ fontSize: '12px', color: 'var(--color-muted)' }}>
            {visit.actual_date || visit.scheduled_date}
            {visit.days_from_randomization != null && ` · Day ${visit.days_from_randomization}`}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '12px', color: 'var(--color-muted)' }}>
            {(visit.labs || []).length} labs · {(visit.vitals || []).length} vitals · {(visit.ecg || []).length} ECG
          </span>
          <span style={{ color: 'var(--color-muted)' }}>{open ? '▲' : '▼'}</span>
        </div>
      </div>

      {open && (
        <div style={{ padding: '16px', borderTop: '1px solid var(--color-border)', background: 'white' }}>
          {/* Visit notes */}
          {visit.visit_notes && (
            <div style={{ background: 'var(--color-major-bg)', border: '1px solid var(--color-major-bg)', borderRadius: '6px', padding: '10px 12px', marginBottom: '14px', fontSize: '13px', color: 'var(--color-major)' }}>
              📝 <strong>Notes:</strong> {visit.visit_notes}
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            {/* Vitals */}
            {(visit.vitals || []).length > 0 && (
              <div>
                <h4 style={{ margin: '0 0 8px', fontSize: '13px', color: 'var(--color-text-soft)' }}>💓 Vitals</h4>
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
                <h4 style={{ margin: '0 0 8px', fontSize: '13px', color: 'var(--color-text-soft)' }}>📈 ECG</h4>
                {visit.ecg.map((e, i) => (
                  <div key={i} style={{ fontSize: '12px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px' }}>
                    {e.qtcf_interval && (
                      <div style={{ color: e.qtcf_interval > 470 ? 'var(--color-critical)' : 'var(--color-text)' }}>
                        QTcF: <strong>{e.qtcf_interval} ms{e.qtcf_interval > 470 ? ' ⚠️' : ''}</strong>
                      </div>
                    )}
                    {e.heart_rate && <div>HR: <strong>{e.heart_rate} bpm</strong></div>}
                    {e.pr_interval && <div>PR: <strong>{e.pr_interval} ms</strong></div>}
                    {e.interpretation && <div style={{ gridColumn: '1/-1', color: 'var(--color-muted)' }}>{e.interpretation}</div>}
                  </div>
                ))}
              </div>
            )}

            {/* Tumor assessment */}
            {visit.tumor_assessment && (
              <div>
                <h4 style={{ margin: '0 0 8px', fontSize: '13px', color: 'var(--color-text-soft)' }}>🔬 Tumor Assessment</h4>
                <div style={{ fontSize: '12px' }}>
                  <div>Response: <strong style={{ color: visit.tumor_assessment.overall_response === 'Progressive Disease' ? 'var(--color-critical)' : visit.tumor_assessment.overall_response === 'Partial Response' ? 'var(--color-minor)' : 'var(--color-text)' }}>{visit.tumor_assessment.overall_response}</strong></div>
                  {visit.tumor_assessment.target_lesion_sum != null && <div>Target sum: <strong>{visit.tumor_assessment.target_lesion_sum} mm</strong></div>}
                  {visit.tumor_assessment.new_lesions > 0 && <div style={{ color: 'var(--color-critical)' }}>New lesions: <strong>{visit.tumor_assessment.new_lesions}</strong></div>}
                  {visit.tumor_assessment.assessment_notes && <div style={{ color: 'var(--color-muted)', marginTop: '4px' }}>{visit.tumor_assessment.assessment_notes}</div>}
                </div>
              </div>
            )}
          </div>

          {/* Labs */}
          {(visit.labs || []).length > 0 && (
            <div style={{ marginTop: '14px' }}>
              <h4 style={{ margin: '0 0 8px', fontSize: '13px', color: 'var(--color-text-soft)' }}>🧪 Labs ({visit.labs.length} results)</h4>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                  <thead>
                    <tr style={{ background: 'var(--color-surface)' }}>
                      {['Category', 'Test', 'Value', 'Unit', 'Range', 'Flag'].map(h => (
                        <th key={h} style={{ padding: '5px 8px', textAlign: 'left', border: '1px solid var(--color-border)', color: 'var(--color-text-soft)' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {visit.labs.map((lab, li) => {
                      const isH = lab.abnormal_flag === 'H' || lab.abnormal_flag === 'HH';
                      const isL = lab.abnormal_flag === 'L' || lab.abnormal_flag === 'LL';
                      const isCrit = lab.clinically_significant;
                      return (
                        <tr key={li} style={{ background: isCrit ? 'var(--color-critical-bg)' : li % 2 === 0 ? 'white' : 'var(--color-surface)' }}>
                          <td style={{ padding: '4px 8px', border: '1px solid var(--color-border)', color: 'var(--color-neutral)', fontSize: '11px' }}>{lab.lab_category}</td>
                          <td style={{ padding: '4px 8px', border: '1px solid var(--color-border)', fontWeight: 600 }}>{lab.test_name}</td>
                          <td style={{ padding: '4px 8px', border: '1px solid var(--color-border)', fontWeight: 700, color: isH ? 'var(--color-critical)' : isL ? 'var(--color-blue)' : 'var(--color-text)' }}>{lab.test_value}</td>
                          <td style={{ padding: '4px 8px', border: '1px solid var(--color-border)', color: 'var(--color-muted)' }}>{lab.test_unit}</td>
                          <td style={{ padding: '4px 8px', border: '1px solid var(--color-border)', color: 'var(--color-muted)' }}>
                            {lab.normal_range_lower != null && lab.normal_range_upper != null ? `${lab.normal_range_lower}–${lab.normal_range_upper}` : '—'}
                          </td>
                          <td style={{ padding: '4px 8px', border: '1px solid var(--color-border)' }}>
                            {lab.abnormal_flag ? (
                              <span style={{ fontWeight: 700, color: isH ? 'var(--color-critical)' : isL ? 'var(--color-blue)' : 'var(--color-text)' }}>{lab.abnormal_flag}{isCrit ? ' ⚠️' : ''}</span>
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
        <span style={{ fontSize: '13px', color: 'var(--color-muted)', fontWeight: 600 }}>Filter:</span>
        {[['all', 'All'], ['abnormal', '⚠️ Abnormal Only'], ...cats.map(c => [c, c])].map(([val, label]) => (
          <button key={val} onClick={() => setFilter(val)} style={{
            padding: '4px 12px', borderRadius: '99px', border: 'none', cursor: 'pointer', fontSize: '12px',
            background: filter === val ? 'var(--color-blue)' : 'var(--color-border)',
            color: filter === val ? 'white' : 'var(--color-text)', fontWeight: filter === val ? 700 : 400
          }}>{label}</button>
        ))}
        <span style={{ marginLeft: 'auto', fontSize: '12px', color: 'var(--color-muted)' }}>{filtered.length} results</span>
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ background: 'var(--color-surface)' }}>
              {['Date', 'Category', 'Test', 'Value', 'Unit', 'Normal Range', 'Flag', 'CS', 'Comments'].map(h => (
                <th key={h} style={{ padding: '8px 10px', textAlign: 'left', border: '1px solid var(--color-border)', color: 'var(--color-text-soft)', whiteSpace: 'nowrap' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((lab, i) => {
              const isH = lab.abnormal_flag === 'H' || lab.abnormal_flag === 'HH';
              const isL = lab.abnormal_flag === 'L' || lab.abnormal_flag === 'LL';
              return (
                <tr key={i} style={{ background: lab.clinically_significant ? 'var(--color-critical-bg)' : i % 2 === 0 ? 'white' : 'var(--color-surface)', verticalAlign: 'top' }}>
                  <td style={{ padding: '6px 10px', border: '1px solid var(--color-border)', whiteSpace: 'nowrap', color: 'var(--color-muted)' }}>{lab.collection_date}</td>
                  <td style={{ padding: '6px 10px', border: '1px solid var(--color-border)', color: 'var(--color-neutral)', fontSize: '11px' }}>{lab.lab_category}</td>
                  <td style={{ padding: '6px 10px', border: '1px solid var(--color-border)', fontWeight: 600 }}>{lab.test_name}</td>
                  <td style={{ padding: '6px 10px', border: '1px solid var(--color-border)', fontWeight: 700, color: isH ? 'var(--color-critical)' : isL ? 'var(--color-blue)' : 'var(--color-text)' }}>{lab.test_value}</td>
                  <td style={{ padding: '6px 10px', border: '1px solid var(--color-border)', color: 'var(--color-muted)' }}>{lab.test_unit}</td>
                  <td style={{ padding: '6px 10px', border: '1px solid var(--color-border)', color: 'var(--color-muted)' }}>
                    {lab.normal_range_lower != null ? `${lab.normal_range_lower}–${lab.normal_range_upper}` : '—'}
                  </td>
                  <td style={{ padding: '6px 10px', border: '1px solid var(--color-border)', fontWeight: 700, color: isH ? 'var(--color-critical)' : isL ? 'var(--color-blue)' : 'var(--color-text)' }}>{lab.abnormal_flag || '—'}</td>
                  <td style={{ padding: '6px 10px', border: '1px solid var(--color-border)' }}>{lab.clinically_significant ? '⚠️' : '—'}</td>
                  <td style={{ padding: '6px 10px', border: '1px solid var(--color-border)', color: 'var(--color-muted)', fontSize: '12px', maxWidth: '180px' }}>{lab.lab_comments || '—'}</td>
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
  const gradeBg = { 1: 'var(--color-minor-bg)', 2: 'var(--color-major-bg)', 3: 'var(--color-major-bg)', 4: 'var(--color-critical-bg)', 5: 'var(--color-critical-bg)' };
  const gradeColor = { 1: 'var(--color-minor)', 2: '#ca8a04', 3: 'var(--color-major)', 4: 'var(--color-critical)', 5: '#7f1d1d' };
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
        <thead>
          <tr style={{ background: 'var(--color-surface)' }}>
            {['AE Term', 'CTCAE Grade', 'Onset', 'Resolution', 'Ongoing', 'SAE', 'Relationship', 'Action Taken', 'Outcome'].map(h => (
              <th key={h} style={{ padding: '8px 10px', textAlign: 'left', border: '1px solid var(--color-border)', color: 'var(--color-text-soft)', whiteSpace: 'nowrap' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {aes.map((ae, i) => (
            <tr key={i} style={{ background: gradeBg[ae.ctcae_grade] || (i % 2 === 0 ? 'white' : 'var(--color-surface)'), verticalAlign: 'top' }}>
              <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)', fontWeight: 600 }}>{ae.ae_term}</td>
              <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)' }}>
                <span style={{ fontWeight: 700, padding: '2px 8px', borderRadius: '99px', background: gradeBg[ae.ctcae_grade] || 'var(--color-surface)', color: gradeColor[ae.ctcae_grade] || 'var(--color-text)', border: `1px solid ${gradeColor[ae.ctcae_grade] || 'var(--color-border)'}` }}>
                  Grade {ae.ctcae_grade}
                </span>
              </td>
              <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)', whiteSpace: 'nowrap' }}>{ae.onset_date || '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)', whiteSpace: 'nowrap' }}>{ae.resolution_date || '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)' }}>{ae.ongoing ? '✅' : '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)' }}>
                <span style={{ fontWeight: 700, color: ae.seriousness && ae.seriousness !== 'No' ? 'var(--color-critical)' : 'var(--color-minor)' }}>
                  {ae.seriousness && ae.seriousness !== 'No' ? '⚠️ SAE' : 'No'}
                </span>
              </td>
              <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)', color: 'var(--color-muted)' }}>{ae.relationship_to_study_drug || '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)', color: 'var(--color-muted)' }}>{ae.action_taken || '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)', color: 'var(--color-muted)' }}>{ae.outcome || '—'}</td>
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
          <tr style={{ background: 'var(--color-surface)' }}>
            {['Medication', 'Class', 'Indication', 'Dose', 'Frequency', 'Route', 'Start Date', 'End Date', 'Ongoing'].map(h => (
              <th key={h} style={{ padding: '8px 10px', textAlign: 'left', border: '1px solid var(--color-border)', color: 'var(--color-text-soft)', whiteSpace: 'nowrap' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {conmeds.map((c, i) => (
            <tr key={i} style={{ background: c.ongoing ? 'var(--color-minor-bg)' : i % 2 === 0 ? 'white' : 'var(--color-surface)', verticalAlign: 'top' }}>
              <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)', fontWeight: 600 }}>{c.medication_name}</td>
              <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)', color: 'var(--color-neutral)', fontSize: '12px' }}>{c.medication_class || '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)', color: 'var(--color-muted)' }}>{c.indication || '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)', fontWeight: 600 }}>{c.dose ? `${c.dose} ${c.dose_unit || ''}` : '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)' }}>{c.frequency || '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)', color: 'var(--color-muted)' }}>{c.route || '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)', whiteSpace: 'nowrap' }}>{c.start_date || '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)', whiteSpace: 'nowrap' }}>{c.end_date || '—'}</td>
              <td style={{ padding: '7px 10px', border: '1px solid var(--color-border)' }}>
                <span style={{ fontWeight: 700, color: c.ongoing ? 'var(--color-minor)' : 'var(--color-muted)' }}>{c.ongoing ? '✅ Yes' : 'No'}</span>
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
  if (!data) return <div style={{ padding: '40px', color: 'var(--color-muted)' }}>Could not load violations.</div>;

  const sevColor = { critical: '#C0392B', major: '#C96A00', minor: '#1E7E4A', info: '#2563EB' };
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
      <div className="page-header">
        <div>
          <div className="page-title">Violations</div>
          <div className="page-subtitle">
            {data.unique_subjects} subject(s) · {data.unique_rules} rules flagged
          </div>
        </div>
        <button className="btn btn-ghost btn-sm"
          onClick={() => { setLoading(true); fetch('/api/violations').then(r => r.json()).then(d => { setData(d); setLoading(false); }); }}>
          Refresh
        </button>
      </div>

      {/* Summary cards */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap' }}>
        {[
          ['Total',    data.summary.total,    '',         'all'],
          ['Critical', data.summary.critical, 'critical', 'critical'],
          ['Major',    data.summary.major,    'major',    'major'],
          ['Minor',    data.summary.minor,    'minor',    'minor'],
          ['Info',     data.summary.info,     'info',     'info'],
        ].map(([label, count, variant, sev]) => (
          <div key={label}
            onClick={() => setFilterSeverity(filterSeverity === sev ? 'all' : sev)}
            className={`stat-card clickable${variant ? ' ' + variant : ''}${filterSeverity === sev ? '' : ''}`}
            style={{ flex: 1, minWidth: '80px', outline: filterSeverity === sev ? '2px solid var(--color-blue)' : 'none' }}>
            <div className="stat-value">{count}</div>
            <div className="stat-label">{label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
        <input type="text" placeholder="Search subject ID..." value={filterSubject}
          onChange={e => setFilterSubject(e.target.value)}
          style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--color-border)', fontSize: '13px', width: '160px' }} />
        <select value={filterRule} onChange={e => setFilterRule(e.target.value)}
          style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--color-border)', fontSize: '13px' }}>
          <option value="all">All Rules</option>
          {uniqueRules.map(r => <option key={r} value={r}>{r}</option>)}
        </select>
        <span style={{ fontSize: '13px', color: 'var(--color-muted)' }}>{filtered.length} of {allV.length} violations</span>
      </div>

      {/* Violations list */}
      {filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px', color: 'var(--color-minor)', fontSize: '16px' }}>
          ✅ No violations match the current filters
        </div>
      ) : (
        filtered.map((v, i) => (
          <div key={i} style={{
            border: `1px solid ${sevColor[v.severity] || 'var(--color-border)'}44`,
            borderLeft: `4px solid ${sevColor[v.severity] || 'var(--color-muted)'}`,
            borderRadius: '6px', marginBottom: '8px', overflow: 'hidden'
          }}>
            {/* Row header */}
            <div onClick={() => setExpandedIdx(expandedIdx === i ? null : i)}
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 16px', cursor: 'pointer', background: expandedIdx === i ? 'var(--color-surface)' : 'white', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                <span style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '14px', color: 'var(--color-navy)' }}>{v.rule_id}</span>
                <span style={{ fontWeight: 700, color: 'var(--color-blue)', fontSize: '13px' }}>{v.subject_id}</span>
                <span style={{ padding: '2px 8px', borderRadius: '99px', fontSize: '11px', fontWeight: 700, background: sevColor[v.severity] || 'var(--color-muted)', color: 'white' }}>{v.severity}</span>
                <span style={{ padding: '2px 8px', borderRadius: '99px', fontSize: '11px', background: 'var(--color-neutral-bg)', color: 'var(--color-neutral)', fontWeight: 600 }}>{v.action_required}</span>
              </div>
              <span style={{ color: 'var(--color-muted)', fontSize: '13px' }}>{expandedIdx === i ? '▲' : '▼'}</span>
            </div>
            {/* Expanded */}
            {expandedIdx === i && (
              <div style={{ padding: '12px 16px', borderTop: '1px solid var(--color-border)', background: 'white' }}>
                {v.evidence && v.evidence.length > 0 && (
                  <div style={{ marginBottom: '10px' }}>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-text-soft)', marginBottom: '4px' }}>Evidence:</div>
                    <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '13px', color: 'var(--color-text)', lineHeight: 1.6 }}>
                      {v.evidence.map((e, ei) => <li key={ei}>{e}</li>)}
                    </ul>
                  </div>
                )}
                <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-text-soft)', marginBottom: '4px' }}>LLM Reasoning:</div>
                <div style={{ fontSize: '13px', color: 'var(--color-text)', background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: '6px', padding: '10px 12px', lineHeight: 1.6 }}>
                  {v.reasoning}
                </div>
                {v.run_date && <div style={{ fontSize: '11px', color: 'var(--color-muted)', marginTop: '8px' }}>Run: {v.run_date?.substring(0, 19)} · Job: {v.job_id}</div>}
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
    critical: 'var(--color-critical)',
    major: 'var(--color-major)',
    minor: 'var(--color-minor)'
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

  const severityColor = { critical: 'var(--color-critical)', major: 'var(--color-major)', minor: 'var(--color-minor)' };

  return (
    <div className="rule-executor">
      <h2>▶️ Execute Rules</h2>

      {/* Mode Toggle */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <button onClick={() => setMode('single')}
          style={{ padding: '8px 20px', borderRadius: '6px', border: 'none', cursor: 'pointer',
            background: mode === 'single' ? 'var(--color-blue)' : '#e5e7eb',
            color: mode === 'single' ? 'white' : 'var(--color-text)', fontWeight: 600 }}>
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
      <p style={{ fontSize: '12px', color: 'var(--color-muted)', margin: '-12px 0 16px 0' }}>
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
        <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: '8px', padding: '20px' }}>
          <p style={{ color: 'var(--color-text-soft)', marginBottom: '16px', fontSize: '14px' }}>
            Runs all <strong>{ruleStats.active} active rules</strong> across <strong>all subjects</strong> and their visits.
            LLM rules use Claude API — this may take a few minutes.
          </p>
          <button onClick={() => executeBatch('all')} disabled={executing}
            className="btn btn-primary btn-lg" style={{ opacity: executing ? 0.55 : 1, cursor: executing ? 'not-allowed' : 'pointer' }}>
            {executing ? 'Running Batch…' : 'Run All Rules for All Subjects'}
          </button>
        </div>
      )}

      {/* Progress Bar for Batch */}
      {jobStatus && (jobStatus.status === 'running' || jobStatus.status === 'queued') && (
        <div style={{ marginTop: '24px', background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: '8px', padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <strong>Batch Progress</strong>
            <span style={{ color: 'var(--color-muted)', fontSize: '14px' }}>
              {jobStatus.completed || 0} / {jobStatus.total} subjects
            </span>
          </div>
          <div style={{ background: 'var(--color-border)', borderRadius: '99px', height: '12px', overflow: 'hidden' }}>
            <div style={{
              height: '100%', borderRadius: '99px', background: 'var(--color-blue)',
              width: `${jobStatus.progress_pct || 0}%`, transition: 'width 0.5s ease'
            }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', fontSize: '13px', color: 'var(--color-muted)' }}>
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
                style={{ padding: '6px 14px', background: 'var(--color-blue)', color: 'white', border: 'none',
                  borderRadius: '6px', cursor: 'pointer', fontSize: '13px', fontWeight: 600 }}>
                📁 View in Results →
              </button>
            )}
            {savedJobId && !onNavigate && (
              <span style={{ fontSize: '12px', color: 'var(--color-minor)', background: '#dcfce7',
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
              <div className="stat-value" style={{ color: results.violations_found > 0 ? 'var(--color-critical)' : 'var(--color-minor)' }}>
                {results.violations_found}
              </div>
              <div className="stat-label">Violations Found</div>
            </div>
            {results.usage && results.usage.total_api_calls > 0 && (
              <div className="stat-card" style={{ flex: 2, minWidth: '200px', background: 'var(--color-minor-bg)', border: '1px solid var(--color-border)' }}>
                <div className="stat-value" style={{ fontSize: '18px', color: 'var(--color-minor)' }}>
                  {results.usage.estimated_cost_display}
                </div>
                <div className="stat-label">
                  Est. Cost · {results.usage.total_tokens.toLocaleString()} tokens · {results.usage.total_api_calls} API calls
                </div>
              </div>
            )}
          </div>

          {results.results && results.results.map((r, i) => (
            <div key={i} style={{ background: 'var(--color-surface)', border: `1px solid ${r.violated ? 'var(--color-critical-bg)' : 'var(--color-border)'}`,
              borderRadius: '8px', padding: '14px', marginBottom: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong>{r.rule_id}</strong>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={{ fontSize: '12px', color: 'var(--color-muted)' }}>{r.evaluation_method}</span>
                  <span style={{ padding: '2px 10px', borderRadius: '99px', fontSize: '12px', fontWeight: 700,
                    background: r.violated ? '#fee2e2' : '#dcfce7', color: r.violated ? 'var(--color-critical)' : 'var(--color-minor)' }}>
                    {r.violated ? '❌ VIOLATION' : '✅ PASS'}
                  </span>
                </div>
              </div>
              {r.violated && (
                <>
                  <p style={{ color: 'var(--color-critical)', fontSize: '13px', margin: '8px 0 4px' }}>{r.reasoning}</p>
                  <p style={{ color: 'var(--color-neutral)', fontSize: '12px', fontWeight: 600 }}>Action: {r.action_required}</p>
                  {r.evidence && r.evidence.length > 0 && (
                    <ul style={{ margin: '6px 0 0', paddingLeft: '18px', fontSize: '12px', color: 'var(--color-text-soft)' }}>
                      {r.evidence.map((e, ei) => <li key={ei}>{e}</li>)}
                    </ul>
                  )}
                </>
              )}
              {!r.violated && <p style={{ color: 'var(--color-muted)', fontSize: '13px', margin: '6px 0 0' }}>{r.reasoning}</p>}
              <p style={{ fontSize: '11px', color: 'var(--color-muted)', margin: '6px 0 0' }}>⏱ {r.execution_time_ms}ms</p>
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
              <div className="stat-value" style={{ color: 'var(--color-critical)' }}>{results.total_violations}</div>
              <div className="stat-label">Total Violations</div>
            </div>
          </div>

          {results.all_violations && results.all_violations.length > 0 && (
            <div>
              <h4 style={{ marginBottom: '12px' }}>🚨 All Violations ({results.all_violations.length})</h4>
              {results.all_violations.map((v, i) => (
                <div key={i} style={{ background: 'var(--color-major-bg)', border: '1px solid #fed7aa',
                  borderLeft: `4px solid ${severityColor[v.severity] || 'var(--color-major)'}`,
                  borderRadius: '6px', padding: '12px', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <strong>{v.subject_id} — {v.rule_id}</strong>
                    <span style={{ padding: '2px 8px', borderRadius: '99px', fontSize: '12px',
                      background: severityColor[v.severity] || 'var(--color-major)', color: 'white' }}>
                      {v.severity}
                    </span>
                  </div>
                  <p style={{ color: 'var(--color-neutral)', fontSize: '12px', margin: '4px 0', fontWeight: 600 }}>
                    Action: {v.action_required}
                  </p>
                  <p style={{ color: 'var(--color-text-soft)', fontSize: '13px', margin: 0 }}>{v.reasoning}</p>
                </div>
              ))}
            </div>
          )}

          {results.total_violations === 0 && (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-minor)', fontSize: '18px' }}>
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
    deterministic: 'var(--color-blue-dk)',
    llm_with_tools: 'var(--color-neutral)',
    llm_with_tools_mock: '#9333ea',
    not_applicable: 'var(--color-muted)',
  };
  return (
    <div style={{
      border: `1px solid ${r.violated ? 'var(--color-critical-bg)' : r.evaluation_method === 'not_applicable' ? 'var(--color-border)' : 'var(--color-border)'}`,
      borderLeft: `4px solid ${r.violated ? 'var(--color-critical)' : r.evaluation_method === 'not_applicable' ? '#cbd5e1' : 'var(--color-minor)'}`,
      borderRadius: '6px', marginBottom: '8px', overflow: 'hidden'
    }}>
      {/* Header row — always visible */}
      <div onClick={() => setExpanded(!expanded)}
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '10px 14px', cursor: 'pointer',
          background: r.violated ? 'var(--color-critical-bg)' : r.evaluation_method === 'not_applicable' ? 'var(--color-surface)' : 'var(--color-minor-bg)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '14px' }}>{r.rule_id}</span>
          <span style={{ fontSize: '11px', color: methodColor[r.evaluation_method] || 'var(--color-muted)',
            background: 'var(--color-surface)', padding: '1px 7px', borderRadius: '99px', fontWeight: 600 }}>
            {r.evaluation_method === 'llm_with_tools' ? '🤖 LLM' :
             r.evaluation_method === 'llm_with_tools_mock' ? '🤖 Mock' :
             r.evaluation_method === 'deterministic' ? '⚙️ Det.' :
             r.evaluation_method === 'not_applicable' ? '⏭ N/A' : r.evaluation_method}
          </span>
          {r.tools_used && r.tools_used.length > 0 && (
            <span style={{ fontSize: '11px', color: 'var(--color-muted)' }}>
              🔧 {r.tools_used.join(', ')}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {r.execution_time_ms && (
            <span style={{ fontSize: '11px', color: 'var(--color-muted)' }}>⏱ {r.execution_time_ms}ms</span>
          )}
          <span style={{ padding: '3px 10px', borderRadius: '99px', fontSize: '12px', fontWeight: 700,
            background: r.violated ? 'var(--color-critical)' : r.evaluation_method === 'not_applicable' ? 'var(--color-border)' : 'var(--color-minor)',
            color: r.evaluation_method === 'not_applicable' ? 'var(--color-muted)' : 'white' }}>
            {r.violated ? '❌ VIOLATION' : r.evaluation_method === 'not_applicable' ? '⏭ SKIPPED' : '✅ PASS'}
          </span>
          <span style={{ color: 'var(--color-muted)', fontSize: '13px' }}>{expanded ? '▲' : '▼'}</span>
        </div>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div style={{ padding: '12px 16px', background: 'white', borderTop: '1px solid var(--color-border)' }}>
          {/* Action required */}
          {r.action_required && (
            <div style={{ marginBottom: '10px' }}>
              <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-critical)',
                background: '#fee2e2', padding: '3px 10px', borderRadius: '99px' }}>
                ⚠️ Action: {r.action_required}
              </span>
            </div>
          )}

          {/* Confidence */}
          {r.confidence && r.evaluation_method !== 'not_applicable' && (
            <div style={{ fontSize: '12px', color: 'var(--color-muted)', marginBottom: '8px' }}>
              Confidence: <strong style={{ color: r.confidence === 'high' ? 'var(--color-minor)' : r.confidence === 'low' ? 'var(--color-critical)' : 'var(--color-major)' }}>
                {r.confidence}
              </strong>
            </div>
          )}

          {/* Reasoning */}
          {r.reasoning && (
            <div style={{ marginBottom: '10px' }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-text-soft)', marginBottom: '4px' }}>Reasoning:</div>
              <div style={{ fontSize: '13px', color: 'var(--color-text)', lineHeight: '1.5',
                background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: '6px',
                padding: '10px 12px', maxHeight: '200px', overflowY: 'auto' }}>
                {r.reasoning}
              </div>
            </div>
          )}

          {/* Evidence */}
          {r.evidence && r.evidence.length > 0 && (
            <div style={{ marginBottom: '10px' }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-text-soft)', marginBottom: '4px' }}>
                Evidence ({r.evidence.length}):
              </div>
              <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '13px', color: 'var(--color-text)', lineHeight: '1.6' }}>
                {r.evidence.map((e, i) => <li key={i}>{e}</li>)}
              </ul>
            </div>
          )}

          {/* Recommendation */}
          {r.recommendation && (
            <div style={{ fontSize: '12px', color: 'var(--color-neutral)', fontStyle: 'italic', marginTop: '6px' }}>
              💡 {r.recommendation}
            </div>
          )}

          {/* Missing data */}
          {r.missing_data && r.missing_data.length > 0 && (
            <div style={{ fontSize: '12px', color: 'var(--color-major)', marginTop: '6px' }}>
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

  const severityColor = { critical: 'var(--color-critical)', major: 'var(--color-major)', minor: 'var(--color-minor)' };

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
                background: filterType === t ? 'var(--color-blue)' : 'var(--color-border)',
                color: filterType === t ? 'white' : 'var(--color-text)', fontWeight: filterType === t ? 700 : 400 }}>
              {t === 'all' ? 'All' : t === 'single' ? '👤 Single' : '👥 Batch'}
            </button>
          ))}
        </div>
      </div>

      {runs.length === 0 && (
        <div style={{ textAlign: 'center', padding: '60px', color: 'var(--color-muted)' }}>
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
                    background: selectedRun === run.job_id ? '#eff6ff' : 'var(--color-surface)',
                    border: `1px solid ${selectedRun === run.job_id ? '#93c5fd' : 'var(--color-border)'}`,
                    borderRadius: selectedRun === run.job_id ? '8px 8px 0 0' : '8px',
                    padding: '12px 18px', cursor: 'pointer',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    flexWrap: 'wrap', gap: '8px'
                  }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                    <span style={{ padding: '2px 8px', borderRadius: '99px', fontSize: '11px', fontWeight: 700,
                      background: run.run_type === 'single' ? '#dbeafe' : 'var(--color-neutral-bg)',
                      color: run.run_type === 'single' ? 'var(--color-blue-dk)' : 'var(--color-neutral)' }}>
                      {run.run_type === 'single' ? '👤 Single' : '👥 Batch'}
                    </span>
                    {run.run_type === 'single' && run.subject_id && (
                      <span style={{ fontWeight: 700, fontFamily: 'monospace', color: 'var(--color-blue)', fontSize: '14px' }}>
                        {run.subject_id}
                      </span>
                    )}
                    {run.run_type !== 'single' && (
                      <span style={{ fontWeight: 700, fontFamily: 'monospace', color: 'var(--color-neutral)', fontSize: '13px' }}>
                        #{run.job_id}
                      </span>
                    )}
                    <span style={{ fontSize: '12px', color: 'var(--color-muted)' }}>{run.saved_at}</span>
                  </div>
                  <div style={{ display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '13px', fontWeight: 700,
                      color: run.total_violations > 0 ? 'var(--color-critical)' : 'var(--color-minor)' }}>
                      {run.total_violations > 0 ? `🚨 ${run.total_violations} violation${run.total_violations !== 1 ? 's' : ''}` : '✅ Clean'}
                    </span>
                    {run.usage?.estimated_cost_display && run.usage.estimated_cost_display !== '$0.0000' && (
                      <span style={{ fontSize: '12px', color: 'var(--color-neutral)' }}>💰 {run.usage.estimated_cost_display}</span>
                    )}
                    <span style={{ fontSize: '12px', color: 'var(--color-muted)' }}>
                      {selectedRun === run.job_id ? '▲ Hide' : '▼ Details'}
                    </span>
                  </div>
                </div>

                {/* Inline detail panel — only shows for the selected run */}
                {selectedRun === run.job_id && (
                  <div ref={detailRef} style={{ background: 'var(--color-surface)', border: '1px solid #93c5fd', borderTop: 'none',
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
                  <div className="stat-value" style={{ color: runDetail.total_violations > 0 ? 'var(--color-critical)' : 'var(--color-minor)' }}>
                    {runDetail.total_violations}
                  </div>
                  <div className="stat-label">Violations</div>
                </div>
                <div className="stat-card" style={{ flex: 1, minWidth: '100px' }}>
                  <div className="stat-value" style={{ color: 'var(--color-critical)' }}>
                    {runDetail.all_violations?.filter(v => v.severity === 'critical').length || 0}
                  </div>
                  <div className="stat-label">Critical</div>
                </div>
                <div className="stat-card" style={{ flex: 1, minWidth: '100px' }}>
                  <div className="stat-value" style={{ color: 'var(--color-major)' }}>
                    {runDetail.all_violations?.filter(v => v.severity === 'major').length || 0}
                  </div>
                  <div className="stat-label">Major</div>
                </div>
                {runDetail.usage?.estimated_cost_display && runDetail.usage.estimated_cost_display !== '$0.0000' && (
                  <div className="stat-card" style={{ flex: 1, minWidth: '100px', background: 'var(--color-minor-bg)', border: '1px solid var(--color-border)' }}>
                    <div className="stat-value" style={{ fontSize: '16px', color: 'var(--color-minor)' }}>
                      {runDetail.usage.estimated_cost_display}
                    </div>
                    <div className="stat-label">{(runDetail.usage.total_tokens || 0).toLocaleString()} tokens</div>
                  </div>
                )}
              </div>

              {/* Tab switcher: Per-Rule Results | Violations Only */}
              <div style={{ display: 'flex', gap: '0', marginBottom: '16px', borderBottom: '2px solid var(--color-border)' }}>
                {[
                  { id: 'results', label: '📋 Per-Rule Results' },
                  { id: 'violations', label: `🚨 Violations (${runDetail.total_violations})` }
                ].map(tab => (
                  <button key={tab.id} onClick={() => setDetailTab(tab.id)}
                    style={{ padding: '8px 20px', border: 'none', cursor: 'pointer', fontSize: '13px', fontWeight: 600,
                      background: 'transparent',
                      borderBottom: detailTab === tab.id ? '2px solid var(--color-blue)' : '2px solid transparent',
                      color: detailTab === tab.id ? 'var(--color-blue)' : 'var(--color-muted)',
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
                        <span style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '15px', color: 'var(--color-navy)' }}>
                          👤 {subjectResult.subject_id}
                        </span>
                        <span style={{ fontSize: '12px', padding: '2px 8px', borderRadius: '99px', fontWeight: 700,
                          background: subjectResult.violations_found > 0 ? '#fee2e2' : '#dcfce7',
                          color: subjectResult.violations_found > 0 ? 'var(--color-critical)' : 'var(--color-minor)' }}>
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
                        <div style={{ color: 'var(--color-muted)', fontSize: '13px', padding: '8px' }}>No rule results available</div>
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
                          style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--color-border)', fontSize: '13px', width: '150px' }} />
                        <select value={filterSeverity} onChange={e => setFilterSeverity(e.target.value)}
                          style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--color-border)', fontSize: '13px' }}>
                          <option value="all">All Severities</option>
                          <option value="critical">Critical</option>
                          <option value="major">Major</option>
                          <option value="minor">Minor</option>
                        </select>
                        <select value={filterRule} onChange={e => setFilterRule(e.target.value)}
                          style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--color-border)', fontSize: '13px' }}>
                          <option value="all">All Rules</option>
                          {uniqueRules.map(r => <option key={r} value={r}>{r}</option>)}
                        </select>
                        <span style={{ fontSize: '13px', color: 'var(--color-muted)' }}>
                          {filteredViolations.length} of {runDetail.total_violations}
                        </span>
                      </div>
                      <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                          <thead>
                            <tr style={{ background: 'var(--color-surface)', textAlign: 'left' }}>
                              <th style={{ padding: '10px 12px', border: '1px solid var(--color-border)' }}>Subject</th>
                              <th style={{ padding: '10px 12px', border: '1px solid var(--color-border)' }}>Rule</th>
                              <th style={{ padding: '10px 12px', border: '1px solid var(--color-border)' }}>Severity</th>
                              <th style={{ padding: '10px 12px', border: '1px solid var(--color-border)' }}>Action</th>
                              <th style={{ padding: '10px 12px', border: '1px solid var(--color-border)' }}>Evidence</th>
                              <th style={{ padding: '10px 12px', border: '1px solid var(--color-border)' }}>Reasoning</th>
                            </tr>
                          </thead>
                          <tbody>
                            {filteredViolations.map((v, i) => (
                              <tr key={i} style={{ background: i % 2 === 0 ? 'white' : 'var(--color-surface)', verticalAlign: 'top' }}>
                                <td style={{ padding: '10px 12px', border: '1px solid var(--color-border)', fontWeight: 700, fontFamily: 'monospace' }}>
                                  {v.subject_id}
                                </td>
                                <td style={{ padding: '10px 12px', border: '1px solid var(--color-border)', fontFamily: 'monospace', color: 'var(--color-neutral)' }}>
                                  {v.rule_id}
                                </td>
                                <td style={{ padding: '10px 12px', border: '1px solid var(--color-border)' }}>
                                  <span style={{ padding: '2px 8px', borderRadius: '99px', fontSize: '11px', fontWeight: 700,
                                    background: severityColor[v.severity] || 'var(--color-muted)', color: 'white' }}>
                                    {v.severity || 'unknown'}
                                  </span>
                                </td>
                                <td style={{ padding: '10px 12px', border: '1px solid var(--color-border)', color: 'var(--color-critical)', fontWeight: 600 }}>
                                  {v.action_required || '—'}
                                </td>
                                <td style={{ padding: '10px 12px', border: '1px solid var(--color-border)', color: 'var(--color-text)', maxWidth: '200px' }}>
                                  {v.evidence && v.evidence.length > 0 ? (
                                    <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '12px' }}>
                                      {v.evidence.slice(0, 3).map((e, ei) => <li key={ei}>{e}</li>)}
                                      {v.evidence.length > 3 && <li style={{ color: 'var(--color-muted)' }}>+{v.evidence.length - 3} more</li>}
                                    </ul>
                                  ) : '—'}
                                </td>
                                <td style={{ padding: '10px 12px', border: '1px solid var(--color-border)', color: 'var(--color-text-soft)', maxWidth: '280px', fontSize: '12px' }}>
                                  {v.reasoning?.substring(0, 200)}{v.reasoning?.length > 200 ? '...' : ''}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-minor)', fontSize: '18px' }}>
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
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-muted)' }}>
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
const statusColor = (s) => ({ 'Completed':'var(--color-minor)','Confirmed':'var(--color-blue)','Planned':'var(--color-major)','In Progress':'var(--color-blue)','Cancelled':'var(--color-muted)' }[s]||'var(--color-muted)');
const visitIcon  = (s) => ({ 'Completed':'✓','Confirmed':'·','Planned':'·','In Progress':'·','Cancelled':'×' }[s]||'·');
const riskColors = { 'High': { bg:'var(--color-critical-bg)', border:'#F5B7B1', text:'var(--color-critical)' }, 'Medium': { bg:'var(--color-major-bg)', border:'#F6C27E', text:'var(--color-major)' }, 'Low': { bg:'var(--color-minor-bg)', border:'#82C9A0', text:'var(--color-minor)' } };
const countryFlag = (country) => {
  const map = { 'United States':'🇺🇸','USA':'🇺🇸','United Kingdom':'🇬🇧','UK':'🇬🇧','Canada':'🇨🇦','Australia':'🇦🇺','Singapore':'🇸🇬' };
  return map[country] || '🌍';
};

function SiteMonitoring({ onNavigate, onSelectSubject, onContextChange }) {
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

  if (loadingOverview) return <div style={{ padding:'40px', textAlign:'center', color:'var(--color-muted)' }}>Loading workstation...</div>;
  if (!overviewData) return <div style={{ padding:'40px', textAlign:'center', color:'var(--color-critical)' }}>Failed to load workstation data.</div>;

  const { protocol, sites } = overviewData;
  const totalEnrolled = sites.reduce((s, x) => s + (x.actual_enrollment || 0), 0);

  // ── BREADCRUMB ───────────────────────────────────────────────────────────
  const Breadcrumb = () => viewLevel === 'study' ? null : (
    <div style={{ display:'flex', alignItems:'center', gap:'6px', marginBottom:'20px', fontSize:'13px', color:'var(--color-muted)' }}>
      <button onClick={goBackToStudy} style={{ background:'none', border:'none', cursor:'pointer', color:'var(--color-blue)', fontWeight:600, padding:0, fontSize:'13px' }}>My Sites</button>
      {selectedSiteId && (<><span>/</span>
        {viewLevel === 'visit'
          ? <button onClick={goBackToSite} style={{ background:'none', border:'none', cursor:'pointer', color:'var(--color-blue)', fontWeight:600, padding:0, fontSize:'13px' }}>Site {selectedSiteId}</button>
          : <span style={{ color:'var(--color-text)', fontWeight:600 }}>Site {selectedSiteId}</span>
        }
      </>)}
      {viewLevel === 'visit' && selectedVisitId && (<><span>/</span><span style={{ color:'var(--color-text)', fontWeight:600 }}>Visit {selectedVisitId}</span></>)}
    </div>
  );

  // ── LEVEL 1: STUDY OVERVIEW ──────────────────────────────────────────────
  if (viewLevel === 'study') return (
    <div style={{ padding:'24px', maxWidth:'1200px', margin:'0 auto' }}>
      {/* Study Banner */}
      <div style={{ background:'var(--color-navy)', borderRadius:'8px', padding:'20px 24px', color:'white', marginBottom:'24px', borderLeft:'4px solid var(--color-blue)' }}>
        <div style={{ fontSize:'11px', color:'rgba(255,255,255,0.55)', letterSpacing:'0.08em', textTransform:'uppercase', marginBottom:'6px', fontWeight:600 }}>
          {protocol.sponsor_name} · {protocol.phase}
        </div>
        <h2 style={{ margin:0, fontSize:'17px', fontWeight:700, color:'#FFFFFF', lineHeight:1.3 }}>{protocol.protocol_number} — {protocol.protocol_name}</h2>
        <div style={{ marginTop:'12px', fontSize:'12px', color:'rgba(255,255,255,0.75)', display:'flex', gap:'20px', flexWrap:'wrap', borderTop:'1px solid rgba(255,255,255,0.12)', paddingTop:'10px' }}>
          <span>{sites.length} Active Sites</span>
          <span>{totalEnrolled} Subjects Enrolled</span>
          <span>Global Study</span>
          <span>Est. Completion: {protocol.estimated_completion_date || 'TBD'}</span>
        </div>
      </div>

      {/* Site Portfolio */}
      <h3 style={{ margin:'0 0 14px', color:'var(--color-text)', fontSize:'14px', fontWeight:600, letterSpacing:'0.01em' }}>Site Portfolio</h3>
      <div style={{ display:'flex', flexDirection:'column', gap:'14px' }}>
        {sites.map(s => {
          const rc = riskColors[s.risk] || riskColors['Low'];
          const enrollPct = Math.min(100, Math.round((s.actual_enrollment||0) / (s.planned_enrollment||1) * 100));
          const tmfColor = s.tmf_score >= 90 ? 'var(--color-minor)' : s.tmf_score >= 75 ? 'var(--color-major)' : 'var(--color-critical)';
          return (
            <div key={s.site_id} style={{ background:'white', borderRadius:'12px', border:'1px solid var(--color-border)', padding:'18px 22px', boxShadow:'0 1px 4px rgba(0,0,0,0.06)', display:'flex', alignItems:'center', gap:'20px', flexWrap:'wrap' }}>
              {/* Site info */}
              <div style={{ flex:'2', minWidth:'220px' }}>
                <div style={{ display:'flex', alignItems:'center', gap:'8px', marginBottom:'4px' }}>
                  <span style={{ fontSize:'18px' }}>{countryFlag(s.country)}</span>
                  <span style={{ fontWeight:700, fontSize:'15px', color:'var(--color-text)' }}>{s.site_name}</span>
                  <span style={{ fontSize:'12px', color:'var(--color-muted)', background:'var(--color-surface)', padding:'2px 8px', borderRadius:'8px' }}>Site {s.site_id}</span>
                </div>
                <div style={{ fontSize:'13px', color:'var(--color-muted)' }}>{s.city}{s.state_province ? `, ${s.state_province}` : ''}, {s.country}</div>
                <div style={{ fontSize:'12px', color:'var(--color-muted)', marginTop:'2px' }}>PI: {s.principal_investigator}</div>
              </div>
              {/* Enrollment */}
              <div style={{ flex:'1', minWidth:'140px' }}>
                <div style={{ fontSize:'12px', color:'var(--color-muted)', marginBottom:'4px', fontWeight:600 }}>Enrollment</div>
                <div style={{ fontSize:'13px', color:'var(--color-text)', fontWeight:700, marginBottom:'4px' }}>{s.actual_enrollment} / {s.planned_enrollment}</div>
                <div style={{ background:'var(--color-border)', borderRadius:'4px', height:'6px', overflow:'hidden' }}>
                  <div style={{ width:`${enrollPct}%`, background:'var(--color-blue)', height:'6px', borderRadius:'4px' }}/>
                </div>
                <div style={{ fontSize:'11px', color:'var(--color-muted)', marginTop:'2px' }}>{enrollPct}% enrolled</div>
              </div>
              {/* Stats */}
              <div style={{ flex:'1', minWidth:'140px' }}>
                <div style={{ fontSize:'12px', color:'var(--color-muted)', marginBottom:'6px', fontWeight:600 }}>Activity</div>
                <div style={{ fontSize:'12px', color:'var(--color-text)' }}>{s.visit_count} visit{s.visit_count!==1?'s':''}</div>
                <div style={{ fontSize:'12px', color: s.open_findings>0 ? 'var(--color-critical)':'var(--color-minor)', fontWeight: s.open_findings>0 ? 600:400 }}>
                  {s.open_findings>0 ? `${s.open_findings} open finding${s.open_findings!==1?'s':''}` : 'No open findings'}
                </div>
                <div style={{ fontSize:'12px', color:'var(--color-muted)', marginTop:'2px' }}>Last: {s.last_visit_date || 'None'}</div>
              </div>
              {/* TMF */}
              <div style={{ flex:'1', minWidth:'120px' }}>
                <div style={{ fontSize:'12px', color:'var(--color-muted)', marginBottom:'4px', fontWeight:600 }}>TMF Readiness</div>
                <div style={{ fontSize:'18px', fontWeight:700, color:tmfColor }}>{s.tmf_score}%</div>
                <div style={{ background:'var(--color-border)', borderRadius:'4px', height:'5px', overflow:'hidden', marginTop:'4px' }}>
                  <div style={{ width:`${s.tmf_score}%`, background:tmfColor, height:'5px', borderRadius:'4px' }}/>
                </div>
                {s.tmf_missing>0 && <div style={{ fontSize:'11px', color:'var(--color-critical)', marginTop:'2px', fontWeight:600 }}>{s.tmf_missing} missing</div>}
                {s.tmf_expiring>0 && <div style={{ fontSize:'11px', color:'var(--color-major)', marginTop:'2px', fontWeight:600 }}>{s.tmf_expiring} expiring</div>}
              </div>
              {/* Risk + action */}
              <div style={{ display:'flex', flexDirection:'column', alignItems:'flex-end', gap:'8px', minWidth:'140px' }}>
                {s.risk_level_detail ? (
                  <div style={{ display:'flex', flexDirection:'column', alignItems:'flex-end', gap:4 }}>
                    <span style={{ padding:'3px 10px', borderRadius:'4px', fontSize:'12px', fontWeight:700,
                      background: RISK_COLORS[s.risk_level_detail]?.bg || rc.bg,
                      border:`1px solid ${RISK_COLORS[s.risk_level_detail]?.border || rc.border}`,
                      color: RISK_COLORS[s.risk_level_detail]?.text || rc.text }}>
                      {s.risk_level_detail} · {s.risk_score}
                    </span>
                    {s.risk_trend && (
                      <span style={{ fontSize:11,
                        color: s.risk_trend === 'DETERIORATING' ? '#C0392B' : s.risk_trend === 'IMPROVING' ? '#1E7E4A' : '#5B6E8C',
                        fontWeight:600 }}>
                        {s.risk_trend === 'DETERIORATING' ? '↑' : s.risk_trend === 'IMPROVING' ? '↓' : '→'} {s.risk_trend}
                      </span>
                    )}
                  </div>
                ) : (
                  <span style={{ padding:'4px 12px', borderRadius:'20px', fontSize:'12px', fontWeight:700, background:rc.bg, border:`1px solid ${rc.border}`, color:rc.text }}>
                    {s.risk} Risk
                  </span>
                )}
                <button onClick={() => goToSite(s.site_id)} style={{ background:'var(--color-blue)', color:'white', border:'none', borderRadius:'8px', padding:'7px 16px', cursor:'pointer', fontWeight:600, fontSize:'13px', whiteSpace:'nowrap' }}>
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
    if (loadingSite) return <div style={{ padding:'40px', textAlign:'center', color:'var(--color-muted)' }}><Breadcrumb/>Loading site data...</div>;
    if (!siteData) return <div style={{ padding:'40px', textAlign:'center', color:'var(--color-critical)' }}><Breadcrumb/>Failed to load site data.</div>;
    const { site, monitoring_visits } = siteData;
    const siteRisk = overviewData.sites.find(s => s.site_id === selectedSiteId) || {};
    const rc = riskColors[siteRisk.risk] || riskColors['Low'];
    const tmfScore = siteRisk.tmf_score;
    const tmfColor = tmfScore >= 90 ? 'var(--color-minor)' : tmfScore >= 75 ? 'var(--color-major)' : 'var(--color-critical)';

    // Group TMF docs by category
    const tmfByCategory = {};
    if (tmfData) {
      tmfData.documents.forEach(d => {
        if (!tmfByCategory[d.category]) tmfByCategory[d.category] = [];
        tmfByCategory[d.category].push(d);
      });
    }
    const tmfStatusIcon = s => ({ 'Present':'✓', 'Missing':'✗', 'Expiring':'!', 'Superseded':'↻' }[s]||'?');
    const tmfStatusColor = s => ({ 'Present':'var(--color-minor)', 'Missing':'var(--color-critical)', 'Expiring':'var(--color-major)', 'Superseded':'var(--color-muted)' }[s]||'var(--color-muted)');

    return (
      <div style={{ padding:'24px', maxWidth:'1200px', margin:'0 auto' }}>
        <Breadcrumb/>
        {/* Site Header */}
        <div style={{ background:'var(--color-navy)', borderRadius:'8px', padding:'20px 24px', color:'white', marginBottom:'24px', borderLeft:'4px solid var(--color-blue)' }}>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', flexWrap:'wrap', gap:'12px' }}>
            <div>
              <div style={{ fontSize:'11px', color:'rgba(255,255,255,0.55)', letterSpacing:'0.08em', textTransform:'uppercase', marginBottom:'6px', fontWeight:600, display:'flex', alignItems:'center', gap:'8px' }}>
                <span>{countryFlag(site.country)} Site {site.site_id} · {site.city}{site.state_province?`, ${site.state_province}`:''}, {site.country}</span>
                <span style={{ padding:'2px 8px', borderRadius:'10px', fontSize:'10px', fontWeight:700, background: rc.bg, color: rc.text, border:`1px solid ${rc.border}` }}>
                  {siteRisk.risk} Risk
                </span>
              </div>
              <h2 style={{ margin:0, fontSize:'18px', fontWeight:700, color:'#FFFFFF' }}>{site.site_name}</h2>
              <div style={{ marginTop:'8px', fontSize:'13px', color:'rgba(255,255,255,0.75)' }}>PI: {site.principal_investigator} &nbsp;|&nbsp; Coordinator: {site.site_coordinator}</div>
            </div>
            <div style={{ display:'flex', gap:'12px', flexWrap:'wrap' }}>
              {[{label:'Enrolled', val:`${site.actual_enrollment}/${site.planned_enrollment}`}, {label:'Monitoring Visits', val:monitoring_visits.length}, {label:'TMF Score', val:`${tmfScore}%`}].map(c => (
                <div key={c.label} style={{ textAlign:'center', background:'rgba(255,255,255,0.1)', borderRadius:'6px', padding:'10px 16px', border:'1px solid rgba(255,255,255,0.12)' }}>
                  <div style={{ fontSize:'18px', fontWeight:700, color:'#FFFFFF' }}>{c.val}</div>
                  <div style={{ fontSize:'11px', color:'rgba(255,255,255,0.65)' }}>{c.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Visit Timeline */}
        <h3 style={{ margin:'0 0 14px', color:'var(--color-text)', fontSize:'16px', fontWeight:700 }}>Monitoring Visit Timeline</h3>
        {monitoring_visits.length === 0 ? (
          <div style={{ textAlign:'center', padding:'48px', color:'var(--color-muted)', background:'var(--color-surface)', borderRadius:'12px', border:'1px dashed var(--color-border)', marginBottom:'24px' }}>
            <div style={{ fontSize:'32px', marginBottom:'10px', opacity:0.35 }}>—</div>
            <div style={{ fontWeight:600, fontSize:'15px', marginBottom:'6px' }}>No monitoring visits scheduled</div>
            <div style={{ fontSize:'13px' }}>No visits have been scheduled for this site yet.</div>
          </div>
        ) : (
          <div style={{ display:'flex', gap:'14px', marginBottom:'28px', flexWrap:'wrap' }}>
            {monitoring_visits.map(mv => (
              <div key={mv.monitoring_visit_id}
                onClick={() => goToVisit(mv.monitoring_visit_id)}
                style={{ flex:'1', minWidth:'180px', cursor:'pointer', borderRadius:'10px', padding:'16px', border:`2px solid ${selectedVisitId === mv.monitoring_visit_id ? statusColor(mv.status) : 'var(--color-border)'}`, background: selectedVisitId === mv.monitoring_visit_id ? '#f0f9ff':'white', boxShadow:'0 1px 4px rgba(0,0,0,0.07)', transition:'all 0.2s' }}>
                <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'8px' }}>
                  <span style={{ fontWeight:700, fontSize:'15px' }}>{visitIcon(mv.status)} {mv.visit_label}</span>
                  <span style={{ fontSize:'11px', fontWeight:600, padding:'2px 8px', borderRadius:'12px', background:statusColor(mv.status)+'20', color:statusColor(mv.status) }}>{mv.status}</span>
                </div>
                <div style={{ fontSize:'12px', color:'var(--color-muted)' }}>{mv.visit_type} · {mv.planned_date}</div>
                <div style={{ fontSize:'11px', color:'var(--color-muted)', marginTop:'3px' }}>CRA: {mv.cra_name}</div>
                {mv.open_findings > 0 && <div style={{ marginTop:'6px', fontSize:'12px', color:'var(--color-critical)', fontWeight:600 }}>{mv.open_findings} open finding{mv.open_findings!==1?'s':''}</div>}
                {mv.report_status && <div style={{ marginTop:'3px', fontSize:'11px', color: mv.report_status==='Finalised'?'var(--color-minor)':'var(--color-major)', fontWeight:500 }}>Report: {mv.report_status}</div>}
              </div>
            ))}
          </div>
        )}

        {/* TMF Status Section */}
        <div style={{ background:'white', borderRadius:'12px', border:'1px solid var(--color-border)', marginBottom:'24px', overflow:'hidden' }}>
          <div style={{ padding:'16px 20px', display:'flex', justifyContent:'space-between', alignItems:'center', cursor:'pointer', background: tmfOpen ? 'var(--color-surface)' : 'white' }} onClick={() => { if(!tmfOpen) loadTmf(); else setTmfOpen(false); }}>
            <div style={{ display:'flex', alignItems:'center', gap:'12px' }}>
              <span style={{ fontSize:'16px', fontWeight:700, color:'var(--color-text)' }}>TMF / Document Status</span>
              <span style={{ fontSize:'13px', fontWeight:700, color:tmfColor }}>{tmfScore}% Readiness</span>
              {siteRisk.tmf_missing>0 && <span style={{ fontSize:'12px', color:'var(--color-critical)', fontWeight:600 }}>{siteRisk.tmf_missing} missing</span>}
              {siteRisk.tmf_expiring>0 && <span style={{ fontSize:'12px', color:'var(--color-major)', fontWeight:600 }}>{siteRisk.tmf_expiring} expiring</span>}
            </div>
            <span style={{ fontSize:'12px', color:'var(--color-blue)', fontWeight:600 }}>{tmfOpen ? '▲ Collapse' : '▼ Expand'}</span>
          </div>
          {tmfOpen && tmfData && (
            <div style={{ padding:'0 20px 20px' }}>
              {/* TMF progress bar */}
              <div style={{ background:'var(--color-border)', borderRadius:'4px', height:'8px', overflow:'hidden', marginBottom:'20px' }}>
                <div style={{ width:`${tmfScore}%`, background:tmfColor, height:'8px', borderRadius:'4px' }}/>
              </div>
              {Object.entries(tmfByCategory).map(([cat, docs]) => (
                <div key={cat} style={{ marginBottom:'16px' }}>
                  <div style={{ fontSize:'12px', fontWeight:700, color:'var(--color-muted)', textTransform:'uppercase', letterSpacing:'0.05em', marginBottom:'8px' }}>{cat}</div>
                  {docs.map(d => (
                    <div key={d.document_id} style={{ display:'flex', alignItems:'center', gap:'10px', padding:'8px 12px', borderRadius:'8px', background:'var(--color-surface)', marginBottom:'6px', border:'1px solid var(--color-border)' }}>
                      <span style={{ fontSize:'14px', fontWeight:700, color:tmfStatusColor(d.status), width:'16px', textAlign:'center', flexShrink:0 }}>{tmfStatusIcon(d.status)}</span>
                      <div style={{ flex:1 }}>
                        <div style={{ fontSize:'13px', fontWeight:600, color:'var(--color-text)' }}>{d.title}</div>
                        {d.notes && <div style={{ fontSize:'11px', color:'var(--color-muted)', marginTop:'1px' }}>{d.notes}</div>}
                        {d.expiry_date && <div style={{ fontSize:'11px', color: d.status==='Expiring'?'var(--color-major)':'var(--color-muted)' }}>Expires: {d.expiry_date}</div>}
                      </div>
                      {d.file_path && (
                        <button onClick={() => window.open(`/api/tmf/files/${selectedSiteId}/${d.file_path.split('/').pop()}`, '_blank')} style={{ background:'#eff6ff', color:'var(--color-blue)', border:'1px solid #bfdbfe', borderRadius:'6px', padding:'4px 10px', cursor:'pointer', fontSize:'12px', fontWeight:600, whiteSpace:'nowrap' }}>
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
            <div style={{ padding:'20px', textAlign:'center', color:'var(--color-muted)' }}>Loading TMF documents...</div>
          )}
        </div>

        {/* Visit Detail Panel */}
        {selectedVisitId && (
          <MonitoringVisitDetail visitId={selectedVisitId} onSelectSubject={onSelectSubject} onRefresh={refreshSite} />
        )}
      </div>
    );
  }

  // ── LEVEL 3: VISIT DETAIL (full page within site context) ────────────────
  if (viewLevel === 'visit') return (
    <div style={{ padding:'24px', maxWidth:'1200px', margin:'0 auto' }}>
      <Breadcrumb/>
      <MonitoringVisitDetail visitId={selectedVisitId} onSelectSubject={onSelectSubject} onRefresh={refreshSite} />
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

  if (loading) return <div style={{ padding: '32px', textAlign: 'center', color: 'var(--color-muted)' }}>Loading visit details...</div>;
  if (!data) return null;

  const { visit, subjects, findings, report } = data;
  const open_findings = findings.filter(f => f.status === 'Open');
  const resolved_findings = findings.filter(f => f.status === 'Resolved');
  const isUpcoming = ['Planned', 'Confirmed'].includes(visit.status);
  const isCompleted = visit.status === 'Completed';

  const severityColor = s => ({ Critical: 'var(--color-critical)', Major: 'var(--color-major)', Minor: 'var(--color-minor)' }[s] || 'var(--color-muted)');
  const priorityColor = p => ({ High: 'var(--color-critical)', Medium: 'var(--color-major)', Low: 'var(--color-minor)' }[p] || 'var(--color-muted)');
  const findingTypeColor = t => ({ 'Protocol Deviation': 'var(--color-neutral)', 'Query': 'var(--color-blue)', 'SDV Finding': 'var(--color-major)', 'Action Item': 'var(--color-muted)' }[t] || 'var(--color-muted)');

  const phases = [
    { id: 'planning', label: '1. Pre-Visit Planning' },
    { id: 'during', label: '2. During Visit' },
    { id: 'report', label: '3. Post-Visit Report' }
  ];

  return (
    <div style={{ background: 'white', borderRadius: '12px', border: '1px solid var(--color-border)', overflow: 'hidden' }}>
      {/* Visit Header */}
      <div style={{ background: 'var(--color-surface)', borderBottom: '1px solid var(--color-border)', padding: '16px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '17px', color: 'var(--color-text)' }}>{visit.visit_label} — {visit.visit_type}</h3>
          <div style={{ fontSize: '13px', color: 'var(--color-muted)', marginTop: '3px' }}>
            Planned: {visit.planned_date} {visit.actual_date ? `· Actual: ${visit.actual_date}` : ''} · CRA: {visit.cra_name}
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {msg && <span style={{ fontSize: '13px', color: 'var(--color-minor)' }}>{msg}</span>}
          <span style={{ fontSize: '12px', fontWeight: 600, padding: '4px 12px', borderRadius: '12px', background: '#e0f2fe', color: 'var(--color-blue-dk)' }}>{visit.status}</span>
        </div>
      </div>

      {/* Phase Tabs */}
      <div style={{ display: 'flex', borderBottom: '2px solid var(--color-border)' }}>
        {phases.map(p => (
          <button key={p.id} onClick={() => setActivePhase(p.id)}
            style={{ flex: 1, padding: '12px', border: 'none', background: activePhase === p.id ? 'white' : 'var(--color-surface)',
              borderBottom: activePhase === p.id ? '2px solid var(--color-blue)' : '2px solid transparent',
              color: activePhase === p.id ? 'var(--color-blue)' : 'var(--color-muted)', fontWeight: activePhase === p.id ? 700 : 400,
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
                  style={{ padding: '10px 20px', background: 'var(--color-blue)', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '14px' }}>
                  📅 Confirm Visit Date
                </button>
              )}
              {visit.status === 'Confirmed' && (
                <div style={{ padding: '10px 16px', background: 'var(--color-minor-bg)', border: '1px solid var(--color-minor)', borderRadius: '8px', fontSize: '13px', color: 'var(--color-minor)', fontWeight: 600 }}>
                  ✅ Visit Date Confirmed
                </div>
              )}
              {/* Generate Prep */}
              {!isCompleted && (
                <button onClick={() => doAction(`/api/ctms/monitoring-visits/${visitId}/generate-prep`, 'POST')}
                  disabled={!!actionLoading}
                  style={{ padding: '10px 20px', background: visit.prep_generated ? 'var(--color-border)' : 'var(--color-blue)', color: visit.prep_generated ? 'var(--color-muted)' : 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '14px' }}>
                  🤖 {visit.prep_generated ? 'Regenerate Visit Prep' : 'Generate Visit Prep'}
                </button>
              )}
              {/* Approve Prep */}
              {visit.prep_generated && !visit.prep_approved && !isCompleted && (
                <button onClick={() => doAction(`/api/ctms/monitoring-visits/${visitId}/approve-prep`)}
                  disabled={!!actionLoading}
                  style={{ padding: '10px 20px', background: 'var(--color-minor)', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '14px' }}>
                  ✅ Approve Prep Agenda
                </button>
              )}
              {visit.prep_approved && (
                <div style={{ padding: '10px 16px', background: 'var(--color-minor-bg)', border: '1px solid var(--color-minor)', borderRadius: '8px', fontSize: '13px', color: 'var(--color-minor)', fontWeight: 600 }}>
                  ✅ Prep Agenda Approved
                </div>
              )}
            </div>

            {/* Visit Objectives */}
            {visit.visit_objectives && Array.isArray(visit.visit_objectives) && (
              <div style={{ marginBottom: '24px' }}>
                <h4 style={{ margin: '0 0 12px', color: 'var(--color-text)', fontSize: '14px' }}>📋 Visit Objectives</h4>
                <div style={{ background: 'var(--color-surface)', borderRadius: '8px', padding: '16px' }}>
                  {visit.visit_objectives.map((obj, i) => (
                    <div key={i} style={{ display: 'flex', gap: '8px', marginBottom: '8px', fontSize: '13px', color: 'var(--color-text)' }}>
                      <span style={{ color: 'var(--color-muted)' }}>☐</span>
                      <span>{obj}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Subject Priority List */}
            {subjects.length > 0 && (
              <div>
                <h4 style={{ margin: '0 0 12px', color: 'var(--color-text)', fontSize: '14px' }}>
                  👥 Subject Priority List ({subjects.length} subjects)
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {subjects.map(s => (
                    <div key={s.subject_id} style={{
                      display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px 16px',
                      background: 'var(--color-surface)', borderRadius: '8px', border: `1px solid ${priorityColor(s.priority)}30`
                    }}>
                      <span style={{ fontSize: '11px', fontWeight: 700, padding: '2px 8px', borderRadius: '10px',
                        background: priorityColor(s.priority) + '20', color: priorityColor(s.priority), whiteSpace: 'nowrap', marginTop: '2px' }}>
                        {s.priority}
                      </span>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
                          <span style={{ fontWeight: 700, fontSize: '14px', color: 'var(--color-text)' }}>{s.subject_id}</span>
                          <span style={{ fontSize: '12px', color: 'var(--color-muted)' }}>SDV: {s.sdv_percent}%</span>
                          <span style={{ fontSize: '11px', padding: '1px 8px', borderRadius: '10px',
                            background: s.sdv_status === 'Complete' ? '#d1fae5' : s.sdv_status === 'In Progress' ? 'var(--color-major-bg)' : 'var(--color-surface)',
                            color: s.sdv_status === 'Complete' ? 'var(--color-minor)' : s.sdv_status === 'In Progress' ? 'var(--color-major)' : 'var(--color-muted)' }}>
                            {s.sdv_status}
                          </span>
                          <button onClick={() => onSelectSubject(s.subject_id)}
                            style={{ fontSize: '11px', padding: '2px 10px', border: '1px solid var(--color-blue)', background: 'white', color: 'var(--color-blue)', borderRadius: '6px', cursor: 'pointer' }}>
                            View Clinical Data →
                          </button>
                        </div>
                        {s.priority_reason && <div style={{ fontSize: '12px', color: 'var(--color-muted)', marginTop: '4px' }}>{s.priority_reason}</div>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {!visit.prep_generated && subjects.length === 0 && (
              <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-muted)', background: 'var(--color-surface)', borderRadius: '8px' }}>
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
              <h4 style={{ margin: 0, color: 'var(--color-text)', fontSize: '14px' }}>Visit Findings ({open_findings.length} open, {resolved_findings.length} resolved)</h4>
              {!isCompleted && (
                <button onClick={() => setShowFindingForm(!showFindingForm)}
                  style={{ padding: '8px 16px', background: 'var(--color-blue)', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '13px' }}>
                  + Log Finding
                </button>
              )}
            </div>

            {/* Log Finding Form */}
            {showFindingForm && (
              <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: '10px', padding: '20px', marginBottom: '20px' }}>
                <h5 style={{ margin: '0 0 16px', color: 'var(--color-text)' }}>Log New Finding</h5>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', color: 'var(--color-muted)', marginBottom: '4px' }}>Subject ID</label>
                    <input value={newFinding.subject_id} onChange={e => setNewFinding({...newFinding, subject_id: e.target.value})}
                      placeholder="e.g. 101-901"
                      style={{ width: '100%', padding: '8px', border: '1px solid var(--color-border)', borderRadius: '6px', fontSize: '13px', boxSizing: 'border-box' }} />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', color: 'var(--color-muted)', marginBottom: '4px' }}>Finding Type</label>
                    <select value={newFinding.finding_type} onChange={e => setNewFinding({...newFinding, finding_type: e.target.value})}
                      style={{ width: '100%', padding: '8px', border: '1px solid var(--color-border)', borderRadius: '6px', fontSize: '13px' }}>
                      {['Protocol Deviation', 'Query', 'SDV Finding', 'Action Item'].map(t => <option key={t}>{t}</option>)}
                    </select>
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', color: 'var(--color-muted)', marginBottom: '4px' }}>Severity</label>
                    <select value={newFinding.severity} onChange={e => setNewFinding({...newFinding, severity: e.target.value})}
                      style={{ width: '100%', padding: '8px', border: '1px solid var(--color-border)', borderRadius: '6px', fontSize: '13px' }}>
                      {['Critical', 'Major', 'Minor'].map(s => <option key={s}>{s}</option>)}
                    </select>
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', color: 'var(--color-muted)', marginBottom: '4px' }}>Assigned To</label>
                    <input value={newFinding.assigned_to} onChange={e => setNewFinding({...newFinding, assigned_to: e.target.value})}
                      placeholder="Site staff name"
                      style={{ width: '100%', padding: '8px', border: '1px solid var(--color-border)', borderRadius: '6px', fontSize: '13px', boxSizing: 'border-box' }} />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', color: 'var(--color-muted)', marginBottom: '4px' }}>Due Date</label>
                    <input type="date" value={newFinding.due_date} onChange={e => setNewFinding({...newFinding, due_date: e.target.value})}
                      style={{ width: '100%', padding: '8px', border: '1px solid var(--color-border)', borderRadius: '6px', fontSize: '13px' }} />
                  </div>
                </div>
                <div style={{ marginBottom: '12px' }}>
                  <label style={{ display: 'block', fontSize: '12px', color: 'var(--color-muted)', marginBottom: '4px' }}>Description</label>
                  <textarea value={newFinding.description} onChange={e => setNewFinding({...newFinding, description: e.target.value})}
                    rows={3} placeholder="Describe the finding in detail..."
                    style={{ width: '100%', padding: '8px', border: '1px solid var(--color-border)', borderRadius: '6px', fontSize: '13px', resize: 'vertical', boxSizing: 'border-box' }} />
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button onClick={() => {
                    doAction(`/api/ctms/monitoring-visits/${visitId}/findings`, 'POST', newFinding)
                      .then(() => { setNewFinding({ subject_id: '', finding_type: 'Query', description: '', severity: 'Major', assigned_to: '', due_date: '' }); setShowFindingForm(false); });
                  }}
                    style={{ padding: '8px 20px', background: 'var(--color-blue)', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 600, fontSize: '13px' }}>
                    Save Finding
                  </button>
                  <button onClick={() => setShowFindingForm(false)}
                    style={{ padding: '8px 16px', background: 'var(--color-surface)', color: 'var(--color-muted)', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px' }}>
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {/* Findings List */}
            {findings.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-muted)', background: 'var(--color-surface)', borderRadius: '8px' }}>
                No findings logged yet. Click "+ Log Finding" to record issues found during the visit.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {findings.map(f => (
                  <div key={f.finding_id} style={{
                    padding: '14px 16px', borderRadius: '8px', border: '1px solid var(--color-border)',
                    borderLeft: `4px solid ${severityColor(f.severity)}`,
                    background: f.status === 'Resolved' ? 'var(--color-surface)' : 'white', opacity: f.status === 'Resolved' ? 0.75 : 1
                  }}>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center', marginBottom: '6px' }}>
                      <span style={{ fontSize: '11px', fontWeight: 700, padding: '2px 8px', borderRadius: '10px',
                        background: severityColor(f.severity) + '20', color: severityColor(f.severity) }}>{f.severity}</span>
                      <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '10px',
                        background: findingTypeColor(f.finding_type) + '15', color: findingTypeColor(f.finding_type) }}>{f.finding_type}</span>
                      {f.subject_id && <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text)' }}>{f.subject_id}</span>}
                      <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '10px',
                        background: f.status === 'Resolved' ? '#d1fae5' : 'var(--color-major-bg)', color: f.status === 'Resolved' ? 'var(--color-minor)' : 'var(--color-major)', marginLeft: 'auto' }}>
                        {f.status}
                      </span>
                    </div>
                    <div style={{ fontSize: '13px', color: 'var(--color-text)', marginBottom: '6px' }}>{f.description}</div>
                    <div style={{ fontSize: '12px', color: 'var(--color-muted)' }}>
                      Assigned to: {f.assigned_to || 'TBD'} · Due: {f.due_date || 'TBD'}
                      {f.resolved_date && ` · Resolved: ${f.resolved_date}`}
                    </div>
                    {f.status === 'Open' && !isCompleted && (
                      <button onClick={() => doAction(`/api/ctms/findings/${f.finding_id}/resolve`)}
                        style={{ marginTop: '8px', padding: '4px 12px', fontSize: '12px', border: '1px solid var(--color-minor)', color: 'var(--color-minor)', background: 'white', borderRadius: '6px', cursor: 'pointer' }}>
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
                <h4 style={{ margin: '0 0 10px', color: 'var(--color-text)', fontSize: '14px' }}>📋 Objectives Checklist</h4>
                <div style={{ background: 'var(--color-surface)', borderRadius: '8px', padding: '14px' }}>
                  {visit.visit_objectives.map((obj, i) => (
                    <div key={i} style={{ display: 'flex', gap: '8px', marginBottom: '6px', fontSize: '13px', color: 'var(--color-text)' }}>
                      <span style={{ color: 'var(--color-muted)' }}>☐</span><span>{obj}</span>
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
                style={{ padding: '10px 20px', background: report?.report_status === 'Finalised' ? 'var(--color-border)' : 'var(--color-blue)', color: report?.report_status === 'Finalised' ? 'var(--color-muted)' : 'white', border: 'none', borderRadius: '8px', cursor: report?.report_status === 'Finalised' ? 'not-allowed' : 'pointer', fontWeight: 600, fontSize: '14px' }}
                title={report?.report_status === 'Finalised' ? 'Report is finalised' : ''}>
                📝 {report ? 'Regenerate Draft' : 'Generate Visit Report'}
              </button>
              {report && report.report_status !== 'CRA Reviewed' && report.report_status !== 'Finalised' && (
                <button onClick={() => doAction(`/api/ctms/monitoring-visits/${visitId}/report-status?status=CRA+Reviewed&cra_notes=${encodeURIComponent(craNotes)}`)}
                  style={{ padding: '10px 20px', background: 'var(--color-major)', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '14px' }}>
                  👁 Mark as CRA Reviewed
                </button>
              )}
              {report && report.report_status === 'CRA Reviewed' && (
                <button onClick={() => doAction(`/api/ctms/monitoring-visits/${visitId}/report-status?status=Finalised&cra_notes=${encodeURIComponent(craNotes)}`)}
                  style={{ padding: '10px 20px', background: 'var(--color-minor)', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '14px' }}>
                  ✅ Finalise Report
                </button>
              )}
              {report && (
                <span style={{ fontSize: '12px', fontWeight: 600, padding: '4px 12px', borderRadius: '12px',
                  background: report.report_status === 'Finalised' ? '#d1fae5' : report.report_status === 'CRA Reviewed' ? 'var(--color-major-bg)' : 'var(--color-surface)',
                  color: report.report_status === 'Finalised' ? 'var(--color-minor)' : report.report_status === 'CRA Reviewed' ? 'var(--color-major)' : 'var(--color-muted)' }}>
                  {report.report_status}
                </span>
              )}
            </div>

            {/* Report content */}
            {report?.draft_content ? (
              <div>
                <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: '10px', padding: '20px', marginBottom: '16px', maxHeight: '500px', overflowY: 'auto' }}>
                  <pre style={{ margin: 0, fontFamily: 'inherit', fontSize: '13px', whiteSpace: 'pre-wrap', color: 'var(--color-text)', lineHeight: '1.6' }}>
                    {report.draft_content}
                  </pre>
                </div>
                {/* CRA Notes */}
                <div style={{ marginBottom: '16px' }}>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--color-text)', marginBottom: '6px' }}>
                    ✏️ CRA Notes {report.report_status === 'Finalised' ? '(locked)' : '(add your comments/edits)'}
                  </label>
                  <textarea value={craNotes} onChange={e => setCraNotes(e.target.value)}
                    disabled={report.report_status === 'Finalised'}
                    rows={4} placeholder="Add any additional notes, corrections, or context here..."
                    style={{ width: '100%', padding: '10px', border: '1px solid var(--color-border)', borderRadius: '8px', fontSize: '13px', resize: 'vertical', background: report.report_status === 'Finalised' ? 'var(--color-surface)' : 'white', boxSizing: 'border-box' }} />
                </div>
                {report.cra_notes && report.report_status === 'Finalised' && (
                  <div style={{ background: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: '8px', padding: '12px', fontSize: '13px', color: 'var(--color-blue-dk)' }}>
                    <strong>CRA Notes (finalised):</strong> {report.cra_notes}
                  </div>
                )}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '60px', color: 'var(--color-muted)', background: 'var(--color-surface)', borderRadius: '8px' }}>
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
// RISK RANKING COMPONENTS
// ============================================================

const RISK_COLORS = {
  CRITICAL: { bg: '#FEF0EE', text: '#C0392B', border: '#F5C6C2', dot: '#C0392B' },
  HIGH:     { bg: '#FFF4E5', text: '#C96A00', border: '#FDDCAA', dot: '#E67E22' },
  ELEVATED: { bg: '#FFFBEA', text: '#92650A', border: '#FAE29C', dot: '#D4AC0D' },
  MODERATE: { bg: '#EBF2FF', text: '#1D4ED8', border: '#BFDBFE', dot: '#2563EB' },
  LOW:      { bg: '#EAF7EF', text: '#1E7E4A', border: '#A7F3D0', dot: '#22C55E' },
  MINIMAL:  { bg: '#F0F2F5', text: '#5B6E8C', border: '#DDE2EA', dot: '#94A3B8' },
};

const TREND_ICONS = {
  DETERIORATING: { icon: '↑', color: '#C0392B', label: 'Deteriorating' },
  STABLE:        { icon: '→', color: '#5B6E8C', label: 'Stable' },
  IMPROVING:     { icon: '↓', color: '#1E7E4A', label: 'Improving' },
};

function RiskBadge({ level, score, size = 'normal' }) {
  const c = RISK_COLORS[level] || RISK_COLORS.MINIMAL;
  const small = size === 'small';
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: small ? 4 : 6,
      background: c.bg, color: c.text, border: `1px solid ${c.border}`,
      borderRadius: 4, padding: small ? '2px 6px' : '3px 8px',
      fontSize: small ? 11 : 12, fontWeight: 700, whiteSpace: 'nowrap',
    }}>
      <span style={{ width: small ? 6 : 8, height: small ? 6 : 8, borderRadius: '50%', background: c.dot, flexShrink: 0 }} />
      {level}{score !== undefined && ` · ${score}`}
    </span>
  );
}

function TrendPill({ trend, delta }) {
  const t = TREND_ICONS[trend] || TREND_ICONS.STABLE;
  return (
    <span style={{ color: t.color, fontWeight: 600, fontSize: 12, whiteSpace: 'nowrap' }}>
      {t.icon} {t.label}{delta !== undefined && delta !== 0 ? ` (${delta > 0 ? '+' : ''}${delta})` : ''}
    </span>
  );
}

// ── Risk Dashboard ────────────────────────────────────────────
function RiskDashboard({ onViewRankings, onViewSite }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  React.useEffect(() => {
    fetch('/api/risk/dashboard')
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading risk dashboard...</div>;
  if (!data) return <div className="loading">No risk data available.</div>;

  const dist = data.distribution || [];
  const maxCount = Math.max(...dist.map(d => d.count), 1);
  const enrollPct = data.total_planned > 0
    ? Math.round((data.total_enrolled / data.total_planned) * 100) : 0;

  const rankLabels = { 1: 'CRITICAL', 2: 'HIGH', 3: 'ELEVATED', 4: 'MODERATE', 5: 'LOW', 6: 'MINIMAL' };
  const rankActions = {
    1: 'Immediate action required',
    2: 'Action within 7 days',
    3: 'Enhanced monitoring',
    4: 'Standard monitoring + watchlist',
    5: 'Routine monitoring',
    6: 'Continue routine oversight',
  };

  return (
    <div className="dashboard">
      <div className="page-header">
        <div>
          <div className="page-title">Site Risk Dashboard</div>
          <div className="page-subtitle">Protocol NVX-1218.22 — Reporting Month: November 2024 · NexaVance Therapeutics</div>
        </div>
        <button
          onClick={onViewRankings}
          style={{ padding: '8px 16px', background: 'var(--color-blue)', color: '#fff', border: 'none', borderRadius: 6, fontWeight: 600, cursor: 'pointer', fontSize: 13 }}
        >
          View Full Rankings
        </button>
      </div>

      {/* KPI Row */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{data.total_sites}</div>
          <div className="stat-label">Active Sites</div>
        </div>
        <div className="stat-card info">
          <div className="stat-value">{data.total_enrolled?.toLocaleString()}</div>
          <div className="stat-label">Subjects Enrolled</div>
        </div>
        <div className="stat-card critical">
          <div className="stat-value">{dist.find(d => d.rank === 1)?.count || 0}</div>
          <div className="stat-label">Critical Sites</div>
        </div>
        <div className="stat-card major">
          <div className="stat-value">{data.trends?.deteriorating || 0}</div>
          <div className="stat-label">Deteriorating</div>
        </div>
        <div className="stat-card minor">
          <div className="stat-value">{data.trends?.improving || 0}</div>
          <div className="stat-label">Improving</div>
        </div>
        <div className="stat-card neutral">
          <div className="stat-value">{enrollPct}%</div>
          <div className="stat-label">Enrollment vs Target</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginTop: 8 }}>
        {/* Risk Distribution */}
        <div style={{ background: '#fff', borderRadius: 8, border: '1px solid var(--color-border)', padding: '20px 24px' }}>
          <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--color-text)', marginBottom: 16 }}>
            Risk Distribution — November 2024
          </div>
          {dist.map(d => {
            const c = RISK_COLORS[d.level] || RISK_COLORS.MINIMAL;
            const barW = Math.round((d.count / maxCount) * 100);
            return (
              <div key={d.rank} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                <div style={{ width: 80, flexShrink: 0 }}>
                  <RiskBadge level={d.level} size="small" />
                </div>
                <div style={{ flex: 1, background: '#F4F6F9', borderRadius: 3, height: 18, overflow: 'hidden' }}>
                  <div style={{ width: `${barW}%`, height: '100%', background: c.dot, borderRadius: 3, transition: 'width 0.6s ease', minWidth: d.count > 0 ? 4 : 0 }} />
                </div>
                <div style={{ width: 24, textAlign: 'right', fontWeight: 700, fontSize: 13, color: c.text, flexShrink: 0 }}>
                  {d.count}
                </div>
                <div style={{ width: 140, fontSize: 11, color: 'var(--color-muted)', flexShrink: 0 }}>
                  {rankActions[d.rank]}
                </div>
              </div>
            );
          })}
        </div>

        {/* Trend Summary */}
        <div style={{ background: '#fff', borderRadius: 8, border: '1px solid var(--color-border)', padding: '20px 24px' }}>
          <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--color-text)', marginBottom: 16 }}>
            Month-over-Month Trend (Oct → Nov)
          </div>
          {[
            { label: 'Deteriorating', count: data.trends?.deteriorating || 0, color: '#C0392B', bg: '#FEF0EE', icon: '↑', desc: 'Risk increased >5 pts' },
            { label: 'Stable',        count: data.trends?.stable        || 0, color: '#5B6E8C', bg: '#F0F2F5', icon: '→', desc: 'Risk within ±5 pts' },
            { label: 'Improving',     count: data.trends?.improving     || 0, color: '#1E7E4A', bg: '#EAF7EF', icon: '↓', desc: 'Risk decreased >5 pts' },
          ].map(t => (
            <div key={t.label} style={{
              display: 'flex', alignItems: 'center', gap: 14,
              padding: '12px 16px', background: t.bg, borderRadius: 6, marginBottom: 10,
              border: `1px solid ${t.color}22`,
            }}>
              <div style={{ fontSize: 22, color: t.color, fontWeight: 700, width: 24, flexShrink: 0 }}>{t.icon}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 700, color: t.color, fontSize: 13 }}>{t.label}</div>
                <div style={{ fontSize: 11, color: 'var(--color-muted)', marginTop: 2 }}>{t.desc}</div>
              </div>
              <div style={{ fontSize: 24, fontWeight: 800, color: t.color }}>{t.count}</div>
              <div style={{ fontSize: 11, color: 'var(--color-muted)' }}>sites</div>
            </div>
          ))}
        </div>
      </div>

      {/* Key Alerts */}
      {data.alerts && data.alerts.length > 0 && (
        <div style={{ marginTop: 20, background: '#fff', borderRadius: 8, border: '1px solid var(--color-border)', padding: '20px 24px' }}>
          <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--color-text)', marginBottom: 16 }}>
            Key Alerts — Immediate Attention Required
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {data.alerts.map(a => {
              const c = RISK_COLORS[a.risk_level] || RISK_COLORS.CRITICAL;
              return (
                <div key={a.site_id} style={{
                  display: 'flex', alignItems: 'flex-start', gap: 16,
                  padding: '14px 18px', background: c.bg, borderRadius: 6,
                  border: `1px solid ${c.border}`, cursor: 'pointer',
                }} onClick={() => onViewSite(a.site_id)}>
                  <div style={{ flexShrink: 0, paddingTop: 2 }}>
                    <RiskBadge level={a.risk_level} score={a.total_risk_score} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 700, color: 'var(--color-text)', fontSize: 13 }}>
                      {a.site_name} · {a.city}, {a.country}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--color-muted)', marginTop: 4 }}>
                      {a.flags.join(' · ')} · Last visit {a.days_since_last_visit}d ago
                    </div>
                    <div style={{ fontSize: 12, color: c.text, marginTop: 6, fontWeight: 600 }}>
                      → {a.recommended_action?.split('.')[0]}
                    </div>
                  </div>
                  <div style={{ flexShrink: 0 }}>
                    <TrendPill trend={a.trend} delta={a.trend_delta} />
                  </div>
                </div>
              );
            })}
          </div>
          <div style={{ marginTop: 14, textAlign: 'right' }}>
            <button onClick={onViewRankings} style={{
              padding: '7px 16px', background: 'var(--color-blue)', color: '#fff',
              border: 'none', borderRadius: 5, fontWeight: 600, cursor: 'pointer', fontSize: 12,
            }}>
              View All Site Rankings →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Site Rankings ─────────────────────────────────────────────
function SiteRankings({ onBack, onViewSite }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ region: '', risk_level: '', trend: '', search: '' });
  const [filterOptions, setFilterOptions] = useState({ regions: [], risk_levels: [], trends: [] });

  React.useEffect(() => {
    Promise.all([
      fetch('/api/risk/rankings').then(r => r.json()),
      fetch('/api/risk/filters').then(r => r.json()),
    ]).then(([rankData, filterData]) => {
      setData(rankData);
      setFilterOptions(filterData);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading rankings...</div>;
  if (!data) return <div className="loading">No ranking data.</div>;

  const sites = (data.sites || []).filter(s => {
    if (filters.region && s.region !== filters.region) return false;
    if (filters.risk_level && s.risk_level !== filters.risk_level) return false;
    if (filters.trend && s.trend !== filters.trend) return false;
    if (filters.search) {
      const q = filters.search.toLowerCase();
      if (!s.site_name.toLowerCase().includes(q) &&
          !s.city.toLowerCase().includes(q) &&
          !s.country.toLowerCase().includes(q) &&
          !s.site_id.toLowerCase().includes(q)) return false;
    }
    return true;
  });

  const setFilter = (k, v) => setFilters(f => ({ ...f, [k]: v }));

  const selStyle = {
    padding: '6px 10px', border: '1px solid var(--color-border)',
    borderRadius: 5, fontSize: 12, background: '#fff', color: 'var(--color-text)',
    cursor: 'pointer',
  };

  return (
    <div className="dashboard">
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button onClick={onBack} style={{ background: 'none', border: '1px solid var(--color-border)', borderRadius: 5, padding: '5px 10px', cursor: 'pointer', fontSize: 12, color: 'var(--color-muted)' }}>
            ← Dashboard
          </button>
          <div>
            <div className="page-title">Site Risk Rankings</div>
            <div className="page-subtitle">
              {sites.length} of {data.total} sites · November 2024
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16, padding: '12px 16px', background: '#fff', borderRadius: 8, border: '1px solid var(--color-border)' }}>
        <input
          placeholder="Search site, city, country..."
          value={filters.search}
          onChange={e => setFilter('search', e.target.value)}
          style={{ ...selStyle, width: 220 }}
        />
        <select value={filters.region} onChange={e => setFilter('region', e.target.value)} style={selStyle}>
          <option value="">All Regions</option>
          {filterOptions.regions.map(r => <option key={r} value={r}>{r}</option>)}
        </select>
        <select value={filters.risk_level} onChange={e => setFilter('risk_level', e.target.value)} style={selStyle}>
          <option value="">All Risk Levels</option>
          {filterOptions.risk_levels.map(r => <option key={r} value={r}>{r}</option>)}
        </select>
        <select value={filters.trend} onChange={e => setFilter('trend', e.target.value)} style={selStyle}>
          <option value="">All Trends</option>
          {filterOptions.trends.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        {(filters.region || filters.risk_level || filters.trend || filters.search) && (
          <button onClick={() => setFilters({ region: '', risk_level: '', trend: '', search: '' })}
            style={{ ...selStyle, color: 'var(--color-critical)', border: '1px solid var(--color-critical)', background: '#FEF0EE' }}>
            Clear
          </button>
        )}
      </div>

      {/* Table */}
      <div style={{ background: '#fff', borderRadius: 8, border: '1px solid var(--color-border)', overflow: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead>
            <tr style={{ background: '#F4F6F9', borderBottom: '2px solid var(--color-border)' }}>
              {['#', 'Site', 'Location', 'Risk Score', 'Components', 'Trend', 'Subjects', 'SAE %', 'Query Rate', 'Days Since Visit', 'Top Flags'].map(h => (
                <th key={h} style={{ padding: '10px 12px', textAlign: 'left', fontWeight: 700, fontSize: 11, color: 'var(--color-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', whiteSpace: 'nowrap' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sites.map((s, i) => {
              const c = RISK_COLORS[s.risk_level] || RISK_COLORS.MINIMAL;
              const topFlags = [];
              if (s.flags?.sdv_backlog) topFlags.push('SDV');
              if (s.flags?.pi_oversight) topFlags.push('PI');
              if (s.flags?.non_enroller) topFlags.push('Non-enroller');
              if (s.flags?.high_sae) topFlags.push('SAE');
              if (s.flags?.critical_deviations) topFlags.push('Devs');
              if (s.flags?.overdue_actions) topFlags.push('Actions');

              // Mini component bars (5 components, max values: 20,20,20,15,10)
              const compBars = [
                { label: 'M', val: s.monitoring_risk_score, max: 20 },
                { label: 'PI', val: s.pi_risk_score, max: 20 },
                { label: 'R', val: s.recruitment_risk_score, max: 20 },
                { label: 'S', val: s.signal_risk_points, max: 15 },
                { label: 'Q', val: s.qa_status_risk_pts, max: 10 },
              ];

              return (
                <tr key={s.site_id}
                  style={{ borderBottom: '1px solid var(--color-border-lt)', cursor: 'pointer', transition: 'background 0.1s' }}
                  onMouseEnter={e => e.currentTarget.style.background = '#F8F9FC'}
                  onMouseLeave={e => e.currentTarget.style.background = ''}
                  onClick={() => onViewSite(s.site_id)}
                >
                  <td style={{ padding: '10px 12px', color: 'var(--color-muted)', fontWeight: 700, width: 32 }}>{i + 1}</td>
                  <td style={{ padding: '10px 12px', whiteSpace: 'nowrap' }}>
                    <div style={{ fontWeight: 700, color: 'var(--color-text)', fontSize: 12 }}>{s.site_id}</div>
                    <div style={{ fontSize: 11, color: 'var(--color-muted)', maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.site_name}</div>
                  </td>
                  <td style={{ padding: '10px 12px', whiteSpace: 'nowrap' }}>
                    <div style={{ fontSize: 12 }}>{s.city}</div>
                    <div style={{ fontSize: 11, color: 'var(--color-muted)' }}>{s.country}</div>
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <RiskBadge level={s.risk_level} score={s.total_risk_score} size="small" />
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <div style={{ display: 'flex', gap: 2, alignItems: 'flex-end', height: 22 }}>
                      {compBars.map(b => (
                        <div key={b.label} title={`${b.label}: ${b.val}/${b.max}`} style={{ width: 10, background: b.val > 0 ? c.dot : '#E2E8F0', borderRadius: 2, height: `${Math.max(3, Math.round((b.val / b.max) * 22))}px`, opacity: 0.8 }} />
                      ))}
                    </div>
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <TrendPill trend={s.trend} delta={s.trend_delta} />
                  </td>
                  <td style={{ padding: '10px 12px', textAlign: 'center', fontWeight: 700 }}>{s.active_subjects}</td>
                  <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                    <span style={{ color: s.sae_rate_pct > 15 ? '#C0392B' : 'inherit', fontWeight: s.sae_rate_pct > 15 ? 700 : 400 }}>
                      {s.sae_rate_pct?.toFixed(1)}%
                    </span>
                  </td>
                  <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                    <span style={{ color: s.data_query_rate_pct > 20 ? '#C0392B' : s.data_query_rate_pct > 10 ? '#C96A00' : 'inherit', fontWeight: s.data_query_rate_pct > 10 ? 700 : 400 }}>
                      {s.data_query_rate_pct?.toFixed(1)}%
                    </span>
                  </td>
                  <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                    <span style={{ color: s.days_since_last_visit > 60 ? '#C0392B' : s.days_since_last_visit > 30 ? '#C96A00' : 'inherit', fontWeight: s.days_since_last_visit > 30 ? 700 : 400 }}>
                      {s.days_since_last_visit}d
                    </span>
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                      {topFlags.slice(0, 3).map(f => (
                        <span key={f} style={{ fontSize: 10, padding: '1px 5px', background: c.bg, color: c.text, border: `1px solid ${c.border}`, borderRadius: 3, fontWeight: 600 }}>{f}</span>
                      ))}
                      {topFlags.length > 3 && <span style={{ fontSize: 10, color: 'var(--color-muted)' }}>+{topFlags.length - 3}</span>}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {sites.length === 0 && (
          <div style={{ padding: '40px 24px', textAlign: 'center', color: 'var(--color-muted)' }}>
            No sites match the current filters.
          </div>
        )}
      </div>
    </div>
  );
}

// ── Site Risk Detail ──────────────────────────────────────────
function SiteRiskDetail({ siteId, onBack, onOpenInMySites }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  React.useEffect(() => {
    setLoading(true);
    fetch(`/api/risk/site/${siteId}`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [siteId]);

  if (loading) return <div className="loading">Loading site risk detail...</div>;
  if (!data) return <div className="loading">No data for site {siteId}.</div>;

  const { site, current, trend_history } = data;
  const c = RISK_COLORS[current.risk_level] || RISK_COLORS.MINIMAL;

  // SVG trend chart
  const chartW = 280, chartH = 80, pad = 16;
  const scores = trend_history.map(t => t.total_risk_score);
  const minS = Math.max(0, Math.min(...scores) - 5);
  const maxS = Math.max(...scores) + 5;
  const pts = trend_history.map((t, i) => {
    const x = pad + (i / Math.max(trend_history.length - 1, 1)) * (chartW - 2 * pad);
    const y = pad + ((maxS - t.total_risk_score) / (maxS - minS)) * (chartH - 2 * pad);
    return `${x},${y}`;
  });

  const MONTH_LABELS = { 202409: 'Sep', 202410: 'Oct', 202411: 'Nov' };

  const compRows = [
    { label: 'Monitoring',  val: current.components.monitoring,  max: 20, tip: 'SDV backlog, CRA turnover, visit frequency' },
    { label: 'PI Oversight',val: current.components.pi,          max: 20, tip: 'PI concerns, consent, staff training' },
    { label: 'Recruitment', val: current.components.recruitment, max: 20, tip: 'Enrollment vs target, screen failure, non-enroller' },
    { label: 'Safety Signal',val: current.components.signal,     max: 15, tip: 'SAE rate, protocol deviations, anomalies' },
    { label: 'QA / Data',   val: current.components.qa,          max: 10, tip: 'Overdue actions, query rate' },
  ];

  return (
    <div className="dashboard">
      {/* Header */}
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button onClick={onBack} style={{ background: 'none', border: '1px solid var(--color-border)', borderRadius: 5, padding: '5px 10px', cursor: 'pointer', fontSize: 12, color: 'var(--color-muted)' }}>
            ← Rankings
          </button>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div className="page-title">{site.site_name}</div>
              <RiskBadge level={current.risk_level} score={current.total_risk_score} />
            </div>
            <div className="page-subtitle">{site.city}, {site.country} · {site.region} · {site.site_type}</div>
          </div>
        </div>
        <button onClick={onOpenInMySites} style={{
          padding: '7px 14px', background: 'none', border: '1px solid var(--color-border)',
          borderRadius: 5, fontWeight: 600, cursor: 'pointer', fontSize: 12, color: 'var(--color-text)',
        }}>
          Open in My Sites →
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        {/* Risk Components */}
        <div style={{ background: '#fff', borderRadius: 8, border: '1px solid var(--color-border)', padding: '20px 24px' }}>
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 16, color: 'var(--color-text)' }}>Risk Breakdown</div>
          {compRows.map(row => (
            <div key={row.label} style={{ marginBottom: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text)' }}>{row.label}</span>
                <span style={{ fontSize: 12, fontWeight: 700, color: row.val > row.max * 0.7 ? c.text : 'var(--color-muted)' }}>
                  {row.val} / {row.max}
                </span>
              </div>
              <div style={{ height: 8, background: '#F0F2F5', borderRadius: 4, overflow: 'hidden' }}>
                <div style={{
                  height: '100%', width: `${(row.val / row.max) * 100}%`,
                  background: row.val > row.max * 0.7 ? c.dot : row.val > row.max * 0.4 ? '#E67E22' : '#22C55E',
                  borderRadius: 4, transition: 'width 0.5s ease',
                }} />
              </div>
              <div style={{ fontSize: 10, color: 'var(--color-muted)', marginTop: 2 }}>{row.tip}</div>
            </div>
          ))}
          <div style={{ marginTop: 16, paddingTop: 12, borderTop: '1px solid var(--color-border-lt)', display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--color-text)' }}>Total Risk Score</span>
            <span style={{ fontSize: 18, fontWeight: 800, color: c.text }}>{current.total_risk_score}</span>
          </div>
        </div>

        {/* Trend Chart */}
        <div style={{ background: '#fff', borderRadius: 8, border: '1px solid var(--color-border)', padding: '20px 24px' }}>
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 4, color: 'var(--color-text)' }}>3-Month Trend</div>
          <div style={{ fontSize: 12, color: 'var(--color-muted)', marginBottom: 16 }}>
            <TrendPill trend={current.trend} delta={current.trend_delta} />
          </div>
          <svg width={chartW} height={chartH} style={{ overflow: 'visible' }}>
            {/* Grid lines */}
            {[0, 0.5, 1].map(f => (
              <line key={f} x1={pad} y1={pad + f * (chartH - 2 * pad)} x2={chartW - pad} y2={pad + f * (chartH - 2 * pad)}
                stroke="#F0F2F5" strokeWidth={1} />
            ))}
            {/* Line */}
            {pts.length >= 2 && (
              <polyline points={pts.join(' ')} fill="none" stroke={c.dot} strokeWidth={2.5} strokeLinejoin="round" />
            )}
            {/* Dots + labels */}
            {trend_history.map((t, i) => {
              const [x, y] = pts[i].split(',').map(Number);
              return (
                <g key={t.month_end}>
                  <circle cx={x} cy={y} r={5} fill={c.dot} stroke="#fff" strokeWidth={2} />
                  <text x={x} y={y - 10} textAnchor="middle" fontSize={10} fill={c.text} fontWeight={700}>{t.total_risk_score}</text>
                  <text x={x} y={chartH - 2} textAnchor="middle" fontSize={10} fill="var(--color-muted)">{MONTH_LABELS[t.month_end]}</text>
                </g>
              );
            })}
          </svg>

          {/* Site metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 12 }}>
            {[
              { label: 'Active Subjects',    val: current.metrics.active_subjects },
              { label: 'Days Since Visit',   val: `${current.metrics.days_since_last_visit}d`, alert: current.metrics.days_since_last_visit > 60 },
              { label: 'SAE Rate',           val: `${current.metrics.sae_rate_pct?.toFixed(1)}%`, alert: current.metrics.sae_rate_pct > 15 },
              { label: 'Query Rate',         val: `${current.metrics.data_query_rate_pct?.toFixed(1)}%`, alert: current.metrics.data_query_rate_pct > 20 },
              { label: 'Major Deviations',   val: current.metrics.major_deviations_count, alert: current.metrics.major_deviations_count > 5 },
              { label: 'Overdue Actions',    val: `${current.metrics.overdue_action_items}/${current.metrics.total_action_items}`, alert: current.metrics.overdue_action_items > 5 },
            ].map(m => (
              <div key={m.label} style={{ padding: '8px 10px', background: m.alert ? c.bg : '#F8F9FC', borderRadius: 5, border: `1px solid ${m.alert ? c.border : 'var(--color-border-lt)'}` }}>
                <div style={{ fontSize: 10, color: 'var(--color-muted)', marginBottom: 2 }}>{m.label}</div>
                <div style={{ fontSize: 15, fontWeight: 700, color: m.alert ? c.text : 'var(--color-text)' }}>{m.val}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Risk Flags */}
        <div style={{ background: '#fff', borderRadius: 8, border: '1px solid var(--color-border)', padding: '20px 24px' }}>
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 14, color: 'var(--color-text)' }}>Active Risk Flags</div>
          {current.active_flags.length === 0 ? (
            <div style={{ color: '#1E7E4A', fontSize: 13 }}>No active risk flags</div>
          ) : (
            current.active_flags.map(f => (
              <div key={f} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', background: c.bg, border: `1px solid ${c.border}`, borderRadius: 5, marginBottom: 8 }}>
                <span style={{ color: c.text, fontWeight: 700, fontSize: 14 }}>!</span>
                <span style={{ fontSize: 12, color: 'var(--color-text)' }}>{f}</span>
              </div>
            ))
          )}
        </div>

        {/* Recommended Actions */}
        <div style={{ background: '#fff', borderRadius: 8, border: '1px solid var(--color-border)', padding: '20px 24px' }}>
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 14, color: 'var(--color-text)' }}>Recommended Actions</div>
          <div style={{ padding: '14px 16px', background: c.bg, border: `1px solid ${c.border}`, borderRadius: 6 }}>
            <div style={{ fontSize: 12, color: c.text, fontWeight: 600, marginBottom: 6 }}>
              {current.risk_level} — Rank {current.risk_rank}
            </div>
            <div style={{ fontSize: 12, color: 'var(--color-text)', lineHeight: 1.6 }}>
              {current.recommended_action}
            </div>
          </div>
          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 12, color: 'var(--color-muted)', marginBottom: 8, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Site Info</div>
            {[
              { label: 'Principal Investigator', val: site.pi_name },
              { label: 'Status', val: site.site_status },
              { label: 'Enrollment', val: `${site.actual_enrollment} / ${site.planned_enrollment} planned` },
              { label: 'CRF Velocity', val: `${current.metrics.avg_daily_crf_submissions?.toFixed(1)} pages/day avg` },
              { label: 'Screen Failure Rate', val: `${current.metrics.screen_failure_rate_pct?.toFixed(1)}%` },
            ].map(r => (
              <div key={r.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', borderBottom: '1px solid var(--color-border-lt)', fontSize: 12 }}>
                <span style={{ color: 'var(--color-muted)' }}>{r.label}</span>
                <span style={{ fontWeight: 600, color: 'var(--color-text)' }}>{r.val}</span>
              </div>
            ))}
          </div>
        </div>
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
        headers: { 'Content-Type': 'application/json' },
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
      const statusColors = { Present: 'var(--color-minor)', Missing: 'var(--color-critical)', Expiring: 'var(--color-major)', Superseded: '#9333ea' };
      const statusBg    = { Present: 'var(--color-minor-bg)', Missing: 'var(--color-critical-bg)', Expiring: 'var(--color-major-bg)', Superseded: '#faf5ff' };
      return (
        <div>
          {msg.text && <p style={{ margin: '0 0 10px', fontSize: '13px', lineHeight: '1.5' }}>{msg.text}</p>}
          <div style={{
            background: doc.status ? statusBg[doc.status] || 'var(--color-surface)' : 'var(--color-surface)',
            border: `1px solid ${doc.status ? statusColors[doc.status] || 'var(--color-border)' : 'var(--color-border)'}`,
            borderRadius: '8px', padding: '12px',
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px' }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: '13px', color: 'var(--color-text)', marginBottom: '4px' }}>
                  📄 {doc.title || doc.document_type || 'Document'}
                </div>
                {doc.version && <div style={{ fontSize: '12px', color: 'var(--color-muted)' }}>Version: {doc.version}</div>}
                {doc.status && (
                  <div style={{ marginTop: '4px' }}>
                    <span style={{
                      background: statusColors[doc.status] || 'var(--color-muted)', color: 'white',
                      fontSize: '11px', padding: '2px 8px', borderRadius: '12px', fontWeight: 600,
                    }}>{doc.status}</span>
                  </div>
                )}
              </div>
              {doc.url && (
                <button
                  onClick={() => window.open(doc.url, '_blank')}
                  style={{
                    background: 'var(--color-blue)', color: 'white', border: 'none',
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
          <div style={{ overflowX: 'auto', borderRadius: '8px', border: '1px solid var(--color-border)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr style={{ background: 'var(--color-text)' }}>
                  {headers.map((h, i) => (
                    <th key={i} style={{ padding: '8px 10px', color: 'white', textAlign: 'left', fontWeight: 600, whiteSpace: 'nowrap' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, ri) => (
                  <tr key={ri} style={{ background: ri % 2 === 0 ? 'white' : 'var(--color-surface)', borderBottom: '1px solid var(--color-surface)' }}>
                    {row.map((cell, ci) => (
                      <td key={ci} style={{ padding: '7px 10px', color: 'var(--color-text)', verticalAlign: 'top' }}>{cell}</td>
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
      <p style={{ margin: 0, fontSize: '13px', lineHeight: '1.6', whiteSpace: 'pre-wrap', color: 'var(--color-navy)' }}>
        {msg.text || ''}
      </p>
    );
  };

  return (
    <div style={{
      width: '400px', flexShrink: 0,
      display: 'flex', flexDirection: 'column',
      background: 'var(--color-surface)', borderLeft: '2px solid var(--color-border)',
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
              <div style={{ fontWeight: 600, color: 'var(--color-text)', fontSize: '14px' }}>Hi, I'm your CRA Copilot!</div>
              <div style={{ color: 'var(--color-muted)', fontSize: '12px', marginTop: '4px' }}>
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
                    background: 'white', border: '1px solid var(--color-border)', borderRadius: '8px',
                    padding: '10px 14px', textAlign: 'left', cursor: 'pointer',
                    fontSize: '13px', color: 'var(--color-text)', fontWeight: 500,
                    transition: 'border-color 0.15s', fontFamily: 'inherit',
                  }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--color-blue)'}
                  onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--color-border)'}
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
              background: msg.role === 'user' ? 'var(--color-blue)' : 'white',
              color: msg.role === 'user' ? 'white' : 'var(--color-navy)',
              borderRadius: msg.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
              padding: '10px 14px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
              border: msg.role === 'user' ? 'none' : '1px solid var(--color-surface)',
              fontSize: '13px',
            }}>
              {msg.role === 'user' ? (
                <p style={{ margin: 0, lineHeight: '1.5' }}>{msg.content}</p>
              ) : (
                renderAssistantContent(msg)
              )}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--color-muted)', marginTop: '3px', paddingLeft: '4px', paddingRight: '4px' }}>
              {msg.role === 'user' ? 'You' : '🤖 Copilot'}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {loading && (
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
            <div style={{
              background: 'white', border: '1px solid var(--color-surface)', borderRadius: '12px 12px 12px 2px',
              padding: '12px 16px', boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
            }}>
              <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                {[0, 1, 2].map(n => (
                  <div key={n} style={{
                    width: '7px', height: '7px', borderRadius: '50%', background: 'var(--color-muted)',
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
        padding: '12px 16px', borderTop: '1px solid var(--color-border)',
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
              flex: 1, padding: '10px 12px', border: '1px solid var(--color-border)', borderRadius: '8px',
              fontSize: '13px', resize: 'none', fontFamily: 'inherit', outline: 'none',
              lineHeight: '1.5', color: 'var(--color-navy)',
            }}
            onFocus={e => e.target.style.borderColor = 'var(--color-blue)'}
            onBlur={e => e.target.style.borderColor = 'var(--color-border)'}
          />
          <button
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
            style={{
              background: loading || !input.trim() ? 'var(--color-muted)' : 'var(--color-blue)',
              color: 'white', border: 'none', borderRadius: '8px',
              padding: '10px 14px', cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
              fontSize: '16px', flexShrink: 0, height: '52px',
              transition: 'background 0.15s',
            }}
          >
            {loading ? '⏳' : '➤'}
          </button>
        </div>
        <div style={{ fontSize: '11px', color: 'var(--color-muted)', marginTop: '6px', textAlign: 'center' }}>
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
