"""Debug Dashboard — Route Optimizer Tab component."""


def get_optimizer_tab_js() -> str:
    return """\
/* ======================== */
/* TAB: ROUTE OPTIMIZER     */
/* ======================== */
function RouteOptimizerTab() {
  const [journeyId, setJourneyId] = useState('');
  const [dayNumber, setDayNumber] = useState('1');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [journey, setJourney] = useState(null);
  const [latestMs, setLatestMs] = useState(null);

  useEffect(() => {
    if (window.__targetOptimizeJourneyId) {
       setJourneyId(window.__targetOptimizeJourneyId);
       setDayNumber(window.__targetOptimizeDayNumber || '1');
       window.__targetOptimizeJourneyId = null;
       window.__targetOptimizeDayNumber = null;
    } else {
       api('/api/v1/journeys?limit=1').then(r => {
         if (r.ok && r.data.journeys?.[0]) setJourneyId(r.data.journeys[0]._id);
       });
    }
  }, []);

  const fetchJourney = async () => {
    if (!journeyId) return;
    const res = await api(`/api/v1/journeys/${journeyId}`);
    if (res.ok) setJourney(res.data);
  };

  useEffect(() => { if (journeyId) fetchJourney(); }, [journeyId]);

  const run = async () => {
    if (!journeyId) return;
    setLoading(true); setError(null); setResult(null);
    const res = await api(`/api/v1/journeys/${journeyId}/days/${dayNumber}/improve-route-order`, { method: 'POST' });
    setLatestMs(res.ms);
    if (res.ok) {
      setResult(res.data);
      fetchJourney();
    } else {
      setError(typeof res.data === 'object' ? JSON.stringify(res.data) : String(res.data));
    }
    setLoading(false);
  };

  const selectedDay = journey?.days?.find(d => d.day_number === parseInt(dayNumber));

  return <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
    <Card>
      <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <Input label="Journey ID" value={journeyId} onChange={setJourneyId} placeholder="ObjectId..." mono style={{ flex: 2, minWidth: '260px' }} />
          <Select label="Day" value={dayNumber} onChange={setDayNumber}
            options={(journey?.days || [{ day_number: 1 }]).map(d => ({ value: String(d.day_number), label: `Day ${d.day_number}` }))}
            style={{ minWidth: '100px' }} />
          <Btn primary onClick={run} disabled={loading}>
            {loading ? 'Optimizing...' : 'Optimize Route'}
          </Btn>
          {latestMs !== null && <Badge color="muted">{latestMs}ms</Badge>}
        </div>
      </div>
    </Card>

    {error && <Card style={{ borderColor: 'rgba(239,68,68,0.3)' }}>
      <div style={{ padding: '16px 20px', color: 'var(--red)', fontSize: '13px', fontFamily: 'var(--mono)', whiteSpace: 'pre-wrap' }}>Error: {error}</div>
    </Card>}

    {result && <Card>
      <div style={{ padding: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
          <span style={{ fontSize: '32px' }}>{result.optimized ? '[OK]' : '[SKIP]'}</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: '16px' }}>{result.message}</div>
            <div style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '4px' }}>
              {result.optimized ? 'Route has been reordered for shorter total distance' : 'The stops were already in the most efficient order'}
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '20px', alignItems: 'center', justifyContent: 'center', padding: '20px', background: 'rgba(0,0,0,0.15)', borderRadius: 'var(--radius)' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase', fontWeight: 600, marginBottom: '6px' }}>Before</div>
            <div style={{ fontSize: '28px', fontWeight: 800, fontFamily: 'var(--mono)', color: result.optimized ? 'var(--red)' : 'var(--text2)' }}>{result.distance_before_km} <span style={{ fontSize: '14px', fontWeight: 400, color: 'var(--muted)' }}>km</span></div>
          </div>
          <span style={{ fontSize: '28px', color: result.optimized ? 'var(--green)' : 'var(--muted)' }}>→</span>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase', fontWeight: 600, marginBottom: '6px' }}>After</div>
            <div style={{ fontSize: '28px', fontWeight: 800, fontFamily: 'var(--mono)', color: result.optimized ? 'var(--green)' : 'var(--text2)' }}>{result.distance_after_km} <span style={{ fontSize: '14px', fontWeight: 400, color: 'var(--muted)' }}>km</span></div>
          </div>
          {result.optimized && <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase', fontWeight: 600, marginBottom: '6px' }}>Saved</div>
            <div style={{ fontSize: '28px', fontWeight: 800, fontFamily: 'var(--mono)', color: 'var(--green)' }}>{(result.distance_before_km - result.distance_after_km).toFixed(2)} <span style={{ fontSize: '14px', fontWeight: 400, color: 'var(--muted)' }}>km</span></div>
          </div>}
        </div>
      </div>
    </Card>}

    {selectedDay && <Card>
      <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border)', background: 'rgba(0,0,0,0.1)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Badge color="accent">Day {selectedDay.day_number} — Current Stops</Badge>
          <Badge color="muted">{(selectedDay.stops || []).length} stops</Badge>
        </div>
      </div>
      <div style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {(selectedDay.stops || []).sort((a,b) => a.order - b.order).map((s, i) => <StopCard key={i} stop={s} index={i} />)}
        {(selectedDay.stops || []).length === 0 && <Empty text="No stops on this day" />}
      </div>
    </Card>}
  </div>;
}
"""
