"""Debug Dashboard — API Explorer Tab component."""


def get_explorer_tab_js() -> str:
    return """\
/* ======================== */
/* TAB: API EXPLORER        */
/* ======================== */
function ApiExplorerTab() {
  const [method, setMethod] = useState('GET');
  const [path, setPath] = useState('/health');
  const [body, setBody] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [latestMs, setLatestMs] = useState(null);

  const send = async () => {
    if (!path.startsWith('/')) return;
    setLoading(true); setResult(null);
    const opts = { method };
    if (['POST', 'PUT', 'PATCH'].includes(method) && body.trim()) {
      opts.body = body;
    }
    const res = await api(path, opts);
    setLatestMs(res.ms);
    setResult(res);
    setLoading(false);
  };

  return <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
    <Card>
      <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
          <Select label="Method" value={method} onChange={setMethod}
            options={['GET','POST','PUT','PATCH','DELETE'].map(m => ({ value: m, label: m }))}
            style={{ minWidth: '100px' }} />
          <Input label="Path" value={path} onChange={setPath} placeholder="/api/v1/..." mono style={{ flex: 1 }} />
          <Btn primary onClick={send} disabled={loading}>
            {loading ? 'Sending...' : 'Send'}
          </Btn>
          {latestMs !== null && <Badge color="muted">{latestMs}ms</Badge>}
        </div>
        {['POST', 'PUT', 'PATCH'].includes(method) && <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <label style={{ fontSize: '11px', fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Request Body (JSON)</label>
          <textarea value={body} onChange={e => setBody(e.target.value)}
            rows={10} spellCheck={false}
            style={{ width: '100%', padding: '12px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border)',
              borderRadius: 'var(--radius-sm)', color: 'var(--text)', fontSize: '13px', fontFamily: 'var(--mono)',
              resize: 'vertical', lineHeight: 1.5, outline: 'none' }}
            onFocus={e => e.target.style.borderColor = 'var(--accent)'}
            onBlur={e => e.target.style.borderColor = 'var(--border)'}
            placeholder="{}" />
        </div>}
      </div>
    </Card>

    {result && <Card>
      <div style={{ padding: '12px 18px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(0,0,0,0.1)' }}>
        <StatusBadge status={result.status} />
        <Badge color="muted">{result.ms}ms</Badge>
      </div>
      <div style={{ padding: '16px' }}>
        <pre style={{ fontFamily: 'var(--mono)', fontSize: '12px', lineHeight: 1.6, whiteSpace: 'pre-wrap', wordBreak: 'break-all', color: 'var(--text2)', margin: 0 }}>
          {typeof result.data === 'object' ? JSON.stringify(result.data, null, 2) : result.data}
        </pre>
      </div>
    </Card>}
  </div>;
}
"""
