"""Debug Dashboard — AI Planner Tab component."""


def get_planner_tab_js() -> str:
    return """\
/* ======================== */
/* TAB: AI PLANNER          */
/* ======================== */
function AIPlannerTab() {
  const [journeyId, setJourneyId] = useState('');
  const [mood, setMood] = useState('NATURE_EXPLORE');
  const [style, setStyle] = useState('balanced');
  const [mode, setMode] = useState('solo');
  const [budget, setBudget] = useState('3000000');
  const [dailyBudget, setDailyBudget] = useState('1000000');
  const [maxPerDay, setMaxPerDay] = useState('5');
  const [hoursPerDay, setHoursPerDay] = useState('8');
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
    if (!journeyId) { setError('Enter a journey ID'); return; }
    setLoading(true); setError(null); setResult(null);
    const body = {
      total_budget_vnd: parseInt(budget) || 0,
      daily_budget_vnd: parseInt(dailyBudget) || 0,
      mode, mood: mode === 'solo' ? mood : undefined,
      mood_distribution: mode === 'group' ? { NATURE_EXPLORE: 0.4, CHILL_CAFE: 0.3, FOOD_LOCAL: 0.2, RESET_HEALING: 0.1 } : undefined,
      start_location: null, max_places_per_day: parseInt(maxPerDay) || 5,
      must_include_categories: [], exclude_categories: [],
      hours_per_day: parseFloat(hoursPerDay) || 8, travel_style: style, place_ids: null,
    };
    const res = await api(`/api/v1/journeys/${journeyId}/ai-plan`, { method: 'POST', body: JSON.stringify(body) });
    setLatestMs(res.ms);
    if (res.ok) { setResult(res.data); } else { setError(typeof res.data === 'object' ? JSON.stringify(res.data, null, 2) : String(res.data)); }
    setLoading(false);
  };

  return <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
    <Card>
      <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <Input label="Journey ID" value={journeyId} onChange={setJourneyId} placeholder="ObjectId..." mono style={{ flex: 2, minWidth: '260px' }} />
          <Select label="Mode" value={mode} onChange={setMode} options={[{ value: 'solo', label: 'Solo' }, { value: 'group', label: 'Group' }]} style={{ minWidth: '100px' }} />
          {mode === 'solo' && <Select label="Mood" value={mood} onChange={setMood} options={[
            { value: 'NATURE_EXPLORE', label: '🌿 Nature Explore' },
            { value: 'CHILL_CAFE', label: '☕ Chill Cafe' },
            { value: 'FOOD_LOCAL', label: '🍜 Food Local' },
            { value: 'RESET_HEALING', label: '🧘 Reset Healing' },
          ]} style={{ minWidth: '160px' }} />}
          <Select label="Style" value={style} onChange={setStyle} options={[
            { value: 'balanced', label: '⚖️ Balanced' },
            { value: 'sightseeing', label: '📸 Sightseeing' },
            { value: 'relaxing', label: '🧘 Relaxing' },
          ]} style={{ minWidth: '140px' }} />
        </div>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <Input label="Total Budget (VND)" value={budget} onChange={setBudget} type="number" mono style={{ flex: 1, minWidth: '140px' }} />
          <Input label="Daily Budget (VND)" value={dailyBudget} onChange={setDailyBudget} type="number" mono style={{ flex: 1, minWidth: '140px' }} />
          <Input label="Max/Day" value={maxPerDay} onChange={setMaxPerDay} type="number" mono style={{ flex: 0.5, minWidth: '80px' }} />
          <Input label="Hours/Day" value={hoursPerDay} onChange={setHoursPerDay} type="number" mono style={{ flex: 0.5, minWidth: '80px' }} />
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <Btn primary onClick={run} disabled={loading} style={{ flex: 1 }}>
            {loading ? 'Generating...' : '🤖 Generate AI Plan (Read-Only)'}
          </Btn>
          {latestMs !== null && <Badge color="muted">{latestMs}ms</Badge>}
        </div>
      </div>
    </Card>

    {error && <Card style={{ borderColor: 'rgba(239,68,68,0.3)' }}>
      <div style={{ padding: '16px 20px', color: 'var(--red)', fontSize: '13px', fontFamily: 'var(--mono)', whiteSpace: 'pre-wrap' }}>❌ {error}</div>
    </Card>}

    {result && <AIPlanResult data={result} />}
  </div>;
}

function AIPlanResult({ data }) {
  return <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
    {/* Summary bar */}
    <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
      <Badge color="green">✓ Generated</Badge>
      <Badge color="muted">{data.total_days} day{data.total_days !== 1 ? 's' : ''}</Badge>
      <Badge color="muted">Pool: {data.candidate_pool_size}</Badge>
      <Badge color="muted">⏱ {data.generation_time_ms}ms</Badge>
      <Badge color="accent">{data.mood_used || 'group'}</Badge>
      <Badge color="muted">v{data.algorithm_version}</Badge>
    </div>

    {/* Planning notes */}
    {data.planning_notes?.length > 0 && <Card>
      <div style={{ padding: '14px 18px' }}>
        <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: '8px' }}>Planning Notes</div>
        {data.planning_notes.map((n, i) => <div key={i} style={{ fontSize: '12px', color: 'var(--text2)', padding: '3px 0', fontFamily: 'var(--mono)' }}>• {n}</div>)}
      </div>
    </Card>}

    {/* Candidate pool */}
    {data.candidate_pool?.length > 0 && <Card>
      <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.1)' }}>
        <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text)' }}>Candidate Pool ({data.candidate_pool.length})</div>
        <Badge color="muted">Top scored places evaluated for this plan</Badge>
      </div>
      <div style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {data.candidate_pool.map((c, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: c.selected ? 'rgba(16,185,129,0.1)' : 'rgba(0,0,0,0.15)', border: c.selected ? '1px solid rgba(16,185,129,0.3)' : '1px solid transparent', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '16px' }}>{c.selected ? '✅' : '❌'}</span>
              <div>
                <div style={{ fontWeight: 600, fontSize: '13px', color: c.selected ? 'var(--green)' : 'var(--text)' }}>{c.place_name}</div>
                <div style={{ fontSize: '11px', color: 'var(--muted)', display: 'flex', gap: '6px', marginTop: '3px' }}>
                  <Badge color="blue">{c.category}</Badge>
                  <Stars rating={c.rating} />
                  <span>💰{c.estimated_cost_vnd.toLocaleString()}₫</span>
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
               <Badge color={c.selected ? 'green' : 'muted'}>Score: {c.final_score.toFixed(1)}</Badge>
               <Copyable text={c.place_id}>{c.place_id.slice(0,6)}</Copyable>
            </div>
          </div>
        ))}
      </div>
    </Card>}

    {/* Day cards */}
    {(data.days || []).map(day => <Card key={day.day_number}>
      <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.1)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Badge color="accent">Day {day.day_number}</Badge>
          <span style={{ fontSize: '12px', color: 'var(--muted)' }}>{day.date ? new Date(day.date).toLocaleDateString() : ''}</span>
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <Badge color="muted">{day.stops?.length || 0} stops</Badge>
          <Badge color="muted">🕐 {day.total_duration_minutes}min</Badge>
          <Badge color="muted">🚗 {day.total_travel_time_minutes}min</Badge>
          <Badge color="muted">📍 {day.total_distance_km?.toFixed(1)}km</Badge>
          <Badge color="green">💰 {(day.spent_today || 0).toLocaleString()}₫</Badge>
        </div>
      </div>
      {day.summary && <div style={{ padding: '10px 18px', fontSize: '12px', color: 'var(--text2)', borderBottom: '1px solid var(--border)', background: 'rgba(0,0,0,0.05)', fontStyle: 'italic' }}>{day.summary}</div>}
      <div style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {(day.stops || []).map((stop, i) => <AIPlanStop key={i} stop={stop} index={i} />)}
      </div>
      {day.explanations?.length > 0 && <div style={{ padding: '10px 18px', borderTop: '1px solid var(--border)', fontSize: '11px', color: 'var(--muted)', fontFamily: 'var(--mono)' }}>
        {day.explanations.map((e, i) => <div key={i}>💡 {e}</div>)}
      </div>}
    </Card>)}
  </div>;
}

function AIPlanStop({ stop, index }) {
  const [showBreakdown, setShowBreakdown] = useState(false);
  const breakdown = stop.mood_score_breakdown || {};
  const maxScore = Math.max(1, ...Object.values(breakdown));

  return <div style={{ background: 'rgba(0,0,0,0.12)', borderRadius: 'var(--radius-sm)', overflow: 'hidden' }}>
    <div style={{ padding: '12px 14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px', cursor: 'pointer' }}
      onClick={() => setShowBreakdown(!showBreakdown)}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1, minWidth: 0 }}>
        <span style={{
          width: '26px', height: '26px', borderRadius: '50%', background: 'var(--accent-glow)',
          color: 'var(--accent2)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '11px', fontWeight: 700, flexShrink: 0,
        }}>{stop.order}</span>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontWeight: 600, fontSize: '13px' }}>{stop.place_name}</div>
          <div style={{ fontSize: '11px', color: 'var(--muted)', display: 'flex', gap: '6px', marginTop: '3px', flexWrap: 'wrap' }}>
            <Badge color="blue">{stop.category}</Badge>
            <Stars rating={stop.rating} />
            <span>{stop.estimated_duration_minutes}min</span>
            {stop.distance_from_previous_km > 0 && <span>📍{stop.distance_from_previous_km.toFixed(1)}km</span>}
            {stop.travel_time_from_previous_minutes > 0 && <span>🚗{stop.travel_time_from_previous_minutes}min</span>}
          </div>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
        <Badge color="green">💰 {(stop.estimated_cost_vnd || 0).toLocaleString()}₫</Badge>
        <Badge color="accent">Score: {(stop.final_score || 0).toFixed(1)}</Badge>
        <Copyable text={stop.place_id}>{stop.place_id.slice(0,6)}</Copyable>
      </div>
    </div>

    {showBreakdown && Object.keys(breakdown).length > 0 && <div style={{ padding: '10px 14px', borderTop: '1px solid var(--border)', background: 'rgba(0,0,0,0.08)' }}>
      <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--muted)', marginBottom: '8px' }}>Mood Score Breakdown</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {Object.entries(breakdown).map(([mood, score]) => <div key={mood} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ width: '120px', fontSize: '11px', fontFamily: 'var(--mono)', color: 'var(--text2)' }}>{mood}</span>
          <div style={{ flex: 1, height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ width: `${(score / maxScore) * 100}%`, height: '100%', background: 'var(--accent)', borderRadius: '3px' }} />
          </div>
          <span style={{ width: '40px', fontSize: '11px', fontFamily: 'var(--mono)', color: 'var(--accent2)', textAlign: 'right' }}>{score.toFixed(1)}</span>
        </div>)}
      </div>
      {stop.reason && <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--muted)', fontStyle: 'italic' }}>📝 {stop.reason}</div>}
    </div>}
  </div>;
}
"""
