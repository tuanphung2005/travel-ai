"""Debug Dashboard — AI Explainer Tab component."""


def get_explainer_tab_js() -> str:
    return """\
/* ======================== */
/* TAB: AI EXPLAINER        */
/* ======================== */
function ExplainerTab() {
  const [journeyId, setJourneyId] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [latestMs, setLatestMs] = useState(null);

  useEffect(() => {
    api('/api/v1/journeys?limit=1').then(r => {
      if (r.ok && r.data.journeys?.[0]) setJourneyId(r.data.journeys[0]._id);
    });
  }, []);

  const run = async () => {
    if (!journeyId) return;
    setLoading(true); setError(null); setResult(null);
    const res = await api(`/api/v1/journeys/${journeyId}/ai-explain`);
    setLatestMs(res.ms);
    if (res.ok) {
      setResult(res.data);
    } else {
      setError(typeof res.data === 'object' ? JSON.stringify(res.data) : String(res.data));
    }
    setLoading(false);
  };

  return <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
    <Card>
      <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <Input label="Journey ID" value={journeyId} onChange={setJourneyId} placeholder="ObjectId..." mono style={{ flex: 2, minWidth: '260px' }} />
          <Btn primary onClick={run} disabled={loading}>
            {loading ? 'Fetching...' : 'Fetch Explanation'}
          </Btn>
          {latestMs !== null && <Badge color="muted">{latestMs}ms</Badge>}
        </div>
      </div>
    </Card>

    {error && <Card style={{ borderColor: 'rgba(239,68,68,0.3)' }}>
      <div style={{ padding: '16px 20px', color: 'var(--red)', fontSize: '13px', fontFamily: 'var(--mono)', whiteSpace: 'pre-wrap' }}>Error: {error}</div>
    </Card>}

    {result && <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <Card>
        <div style={{ padding: '20px' }}>
          <div style={{ fontSize: '16px', fontWeight: 700, marginBottom: '8px' }}>Algorithm Description</div>
          <div style={{ fontSize: '14px', color: 'var(--text2)', lineHeight: '1.5' }}>{result.algorithm_description}</div>
        </div>
      </Card>

      <Card>
        <div style={{ padding: '20px' }}>
          <div style={{ fontSize: '16px', fontWeight: 700, marginBottom: '8px' }}>Distance Calculation</div>
          <div style={{ fontSize: '14px', color: 'var(--text2)', lineHeight: '1.5' }}>{result.distance_calculation}</div>
        </div>
      </Card>

      <Card>
        <div style={{ padding: '20px' }}>
          <div style={{ fontSize: '16px', fontWeight: 700, marginBottom: '8px' }}>Grouping & Planning Strategy</div>
          <div style={{ fontSize: '14px', color: 'var(--text2)', lineHeight: '1.5' }}>{result.grouping_strategy}</div>
        </div>
      </Card>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
        <Card>
          <div style={{ padding: '20px' }}>
            <div style={{ fontSize: '14px', fontWeight: 700, marginBottom: '12px', color: 'var(--accent2)' }}>Constraints Applied</div>
            <ul style={{ paddingLeft: '20px', fontSize: '13px', color: 'var(--text2)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {result.constraints_applied.map((c, i) => <li key={i}>{c}</li>)}
            </ul>
          </div>
        </Card>
        <Card>
          <div style={{ padding: '20px' }}>
            <div style={{ fontSize: '14px', fontWeight: 700, marginBottom: '12px', color: 'var(--accent2)' }}>Selection Criteria</div>
            <ul style={{ paddingLeft: '20px', fontSize: '13px', color: 'var(--text2)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {result.place_selection_criteria.map((c, i) => <li key={i}>{c}</li>)}
            </ul>
          </div>
        </Card>
      </div>

      <Card>
        <div style={{ padding: '20px' }}>
          <div style={{ fontSize: '16px', fontWeight: 700, marginBottom: '16px' }}>Travel Style Adjustments</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '12px' }}>
            {Object.entries(result.style_adjustments).map(([styleKey, styleData]) => (
              <div key={styleKey} style={{ background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: 'var(--radius)', border: '1px solid rgba(255,255,255,0.05)' }}>
                <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase', marginBottom: '8px' }}>{styleKey}</div>
                <div style={{ fontSize: '13px', color: 'var(--text)', marginBottom: '10px' }}>{styleData.description}</div>
                <div style={{ fontSize: '12px', color: 'var(--muted)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <div>Base duration: {styleData.base_duration}</div>
                  <div>Max stops/day: {styleData.max_stops}</div>
                  <div>Buffer time: {styleData.buffer_time}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>}
  </div>;
}
"""
