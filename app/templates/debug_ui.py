"""Smart Debug Dashboard — React-via-CDN modular UI.

This is the main shell that composes all tab modules into a single HTML page.
Individual tab components are in separate template files for maintainability.
"""
from app.templates.debug_places import get_places_tab_js
from app.templates.debug_journeys import get_journeys_tab_js
from app.templates.debug_planner import get_planner_tab_js
from app.templates.debug_optimizer import get_optimizer_tab_js
from app.templates.debug_explorer import get_explorer_tab_js


_HTML_SHELL = """\
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Travel AI — Debug Dashboard</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
  <script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #09090b; --surface: rgba(20, 20, 24, 0.85); --surface2: #1a1a1f;
      --border: rgba(255,255,255,0.08); --border-hover: rgba(255,255,255,0.15);
      --text: #fafafa; --text2: #d4d4d8; --muted: #71717a;
      --accent: #8b5cf6; --accent2: #a78bfa; --accent-glow: rgba(139,92,246,0.25);
      --green: #10b981; --green-bg: rgba(16,185,129,0.1); --green-border: rgba(16,185,129,0.25);
      --red: #ef4444; --red-bg: rgba(239,68,68,0.1);
      --orange: #f59e0b; --orange-bg: rgba(245,158,11,0.1);
      --blue: #3b82f6; --blue-bg: rgba(59,130,246,0.1);
      --cyan: #06b6d4; --pink: #ec4899;
      --mono: 'Fira Code', monospace; --sans: 'Inter', system-ui, sans-serif;
      --radius: 12px; --radius-sm: 8px;
    }
    html, body, #root { min-height: 100vh; }
    body {
      font-family: var(--sans); background: var(--bg); color: var(--text);
      background-image:
        radial-gradient(at 0% 0%, rgba(139,92,246,0.06) 0px, transparent 50%),
        radial-gradient(at 100% 50%, rgba(16,185,129,0.04) 0px, transparent 50%);
      background-attachment: fixed;
    }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
  </style>
</head>
<body>
<div id="root"></div>
<script type="text/babel">
const { useState, useEffect, useCallback, useRef, useMemo } = React;

/* ─── API helper ─── */
async function api(path, opts = {}) {
  const t0 = performance.now();
  const res = await fetch(path, {
    ...opts,
    headers: { 'Content-Type': 'application/json', ...opts.headers },
  });
  const ms = Math.round(performance.now() - t0);
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = text; }
  return { status: res.status, ok: res.ok, data, ms };
}

/* ─── Shared Components ─── */
function Badge({ children, color = 'accent', className = '' }) {
  const colors = {
    accent: 'background: var(--accent-glow); color: var(--accent2); border: 1px solid rgba(139,92,246,0.3)',
    green: 'background: var(--green-bg); color: var(--green); border: 1px solid var(--green-border)',
    red: 'background: var(--red-bg); color: var(--red); border: 1px solid rgba(239,68,68,0.2)',
    orange: 'background: var(--orange-bg); color: var(--orange); border: 1px solid rgba(245,158,11,0.2)',
    blue: 'background: var(--blue-bg); color: var(--blue); border: 1px solid rgba(59,130,246,0.2)',
    muted: 'background: rgba(255,255,255,0.05); color: var(--muted); border: 1px solid var(--border)',
  };
  return <span className={className} style={{
    ...Object.fromEntries(colors[color].split(';').map(s => { const [k,v] = s.split(':'); return [k.trim().replace(/-([a-z])/g, (_, c) => c.toUpperCase()), v?.trim()]; })),
    padding: '3px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: 600, fontFamily: 'var(--mono)',
    display: 'inline-flex', alignItems: 'center', gap: '5px', whiteSpace: 'nowrap',
  }}>{children}</span>;
}

function Card({ children, style, className = '' }) {
  return <div className={className} style={{
    background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)',
    backdropFilter: 'blur(16px)', boxShadow: '0 4px 24px rgba(0,0,0,0.15)', overflow: 'hidden', ...style,
  }}>{children}</div>;
}

function Btn({ children, primary, small, onClick, disabled, style }) {
  return <button disabled={disabled} onClick={onClick} style={{
    padding: small ? '6px 14px' : '10px 20px', borderRadius: 'var(--radius-sm)',
    border: primary ? 'none' : '1px solid var(--border)',
    background: primary ? 'var(--accent)' : 'rgba(255,255,255,0.04)',
    color: primary ? '#fff' : 'var(--text2)', fontSize: small ? '12px' : '13px',
    fontWeight: 600, fontFamily: 'var(--sans)', cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.5 : 1, display: 'inline-flex', alignItems: 'center', gap: '8px',
    boxShadow: primary ? '0 4px 14px var(--accent-glow)' : 'none', ...style,
  }}>{children}</button>;
}

function Input({ label, value, onChange, placeholder, type = 'text', style, mono }) {
  return <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', ...style }}>
    {label && <label style={{ fontSize: '11px', fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{label}</label>}
    <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
      style={{ padding: '9px 13px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
        color: 'var(--text)', fontSize: '13px', fontFamily: mono ? 'var(--mono)' : 'var(--sans)', outline: 'none', width: '100%' }}
      onFocus={e => e.target.style.borderColor = 'var(--accent)'}
      onBlur={e => e.target.style.borderColor = 'var(--border)'} />
  </div>;
}

function Select({ label, value, onChange, options, style }) {
  return <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', ...style }}>
    {label && <label style={{ fontSize: '11px', fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{label}</label>}
    <select value={value} onChange={e => onChange(e.target.value)} style={{
      padding: '9px 13px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
      color: 'var(--text)', fontSize: '13px', fontFamily: 'var(--sans)', outline: 'none', cursor: 'pointer', appearance: 'none',
      backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2371717a'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
      backgroundRepeat: 'no-repeat', backgroundPosition: 'right 10px center', backgroundSize: '14px', paddingRight: '32px',
    }}>{options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}</select>
  </div>;
}

function Copyable({ text, children }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1500); };
  return <span onClick={handleCopy} title="Click to copy" style={{
    cursor: 'pointer', fontFamily: 'var(--mono)', fontSize: '11px', color: copied ? 'var(--green)' : 'var(--accent2)',
    background: copied ? 'var(--green-bg)' : 'var(--accent-glow)', padding: '2px 8px', borderRadius: '4px',
    display: 'inline-flex', alignItems: 'center', gap: '4px',
  }}>{copied ? '✓ Copied' : (children || text)}</span>;
}

function Loading({ text = 'Loading...' }) {
  return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px', padding: '40px', color: 'var(--muted)' }}>
    <span>{text}</span>
  </div>;
}

function Empty({ icon = '📭', text = 'No data' }) {
  return <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '12px', padding: '60px 20px', color: 'var(--muted)' }}>
    <span style={{ fontSize: '36px' }}>{icon}</span><span style={{ fontSize: '14px' }}>{text}</span>
  </div>;
}

function Stars({ rating }) {
  const full = Math.floor(rating || 0);
  const half = (rating || 0) - full >= 0.5;
  return <span style={{ color: '#fbbf24', fontSize: '12px', letterSpacing: '1px' }}>
    {'★'.repeat(full)}{half ? '½' : ''}{'☆'.repeat(Math.max(0, 5 - full - (half ? 1 : 0)))}
    <span style={{ color: 'var(--muted)', marginLeft: '4px', fontSize: '11px' }}>{(rating || 0).toFixed(1)}</span>
  </span>;
}

function StatusBadge({ status }) {
  const color = status < 300 ? 'green' : status < 500 ? 'orange' : 'red';
  return <Badge color={color}>{status}</Badge>;
}

/* ─── Tab Components (from modules) ─── */
__PLACES_TAB__
__JOURNEYS_TAB__
__PLANNER_TAB__
__OPTIMIZER_TAB__
__EXPLORER_TAB__

/* ======================== */
/* MAIN APP                 */
/* ======================== */
const TABS = [
  { id: 'places', label: '📍 Places', icon: '📍' },
  { id: 'journeys', label: '📋 Journeys', icon: '📋' },
  { id: 'planner', label: '🤖 AI Planner', icon: '🤖' },
  { id: 'optimizer', label: '🔄 Route Optimizer', icon: '🔄' },
  { id: 'explorer', label: '⚡ API Explorer', icon: '⚡' },
];

function App() {
  const [tab, setTab] = useState('places');

  return <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
    {/* Header */}
    <header style={{
      padding: '16px 32px', borderBottom: '1px solid var(--border)',
      background: 'rgba(9,9,11,0.7)', backdropFilter: 'blur(16px)',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      position: 'sticky', top: 0, zIndex: 50,
    }}>
      <h1 style={{ fontSize: '18px', fontWeight: 800, letterSpacing: '-0.5px', display: 'flex', alignItems: 'center', gap: '10px',
        background: 'linear-gradient(135deg, #fff 0%, #a1a1aa 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
        <span style={{ WebkitTextFillColor: 'initial' }}>🧭</span> Travel AI Debug
      </h1>
      <div style={{ display: 'flex', gap: '4px', background: 'rgba(0,0,0,0.3)', padding: '4px', borderRadius: '10px', border: '1px solid var(--border)' }}>
        {TABS.map(t => <button key={t.id} onClick={() => setTab(t.id)} style={{
          padding: '7px 16px', borderRadius: '7px', border: 'none', cursor: 'pointer',
          fontSize: '12px', fontWeight: 600, fontFamily: 'var(--sans)',
          background: tab === t.id ? 'var(--surface2)' : 'transparent',
          color: tab === t.id ? 'var(--text)' : 'var(--muted)',
          boxShadow: tab === t.id ? '0 2px 8px rgba(0,0,0,0.3)' : 'none',
        }}>{t.label}</button>)}
      </div>
    </header>

    {/* Content — natural scroll, no fixed height */}
    <main style={{ flex: 1, padding: '24px 32px', paddingBottom: '60px' }}>
      {tab === 'places' && <PlacesTab />}
      {tab === 'journeys' && <JourneysTab />}
      {tab === 'planner' && <AIPlannerTab />}
      {tab === 'optimizer' && <RouteOptimizerTab />}
      {tab === 'explorer' && <ApiExplorerTab />}
    </main>
  </div>;
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
</script>
</body>
</html>"""


def get_debug_ui_html() -> str:
    """Return the debug dashboard as a self-contained HTML page."""
    html = _HTML_SHELL
    html = html.replace("__PLACES_TAB__", get_places_tab_js())
    html = html.replace("__JOURNEYS_TAB__", get_journeys_tab_js())
    html = html.replace("__PLANNER_TAB__", get_planner_tab_js())
    html = html.replace("__OPTIMIZER_TAB__", get_optimizer_tab_js())
    html = html.replace("__EXPLORER_TAB__", get_explorer_tab_js())
    return html
