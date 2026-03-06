"""Debug Dashboard — Journeys Tab component."""


def get_journeys_tab_js() -> str:
    return """\
/* ======================== */
/* TAB: JOURNEYS            */
/* ======================== */
function JourneysTab() {
  const [journeys, setJourneys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);
  const [journeyDetail, setJourneyDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const fetchJourneys = async () => {
    setLoading(true);
    const res = await api('/api/v1/journeys?limit=50');
    if (res.ok) setJourneys(res.data.journeys || []);
    setLoading(false);
  };

  useEffect(() => {
    fetchJourneys();
  }, []);

  const expand = async (id) => {
    if (expanded === id) { setExpanded(null); return; }
    setExpanded(id);
    setDetailLoading(true);
    const res = await api(`/api/v1/journeys/${id}`);
    if (res.ok) setJourneyDetail(res.data);
    setDetailLoading(false);
  };

  const deleteJourney = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('Delete this journey completely? This cannot be undone.')) return;
    setDeleting(id);
    const res = await api(`/api/v1/journeys/${id}`, { method: 'DELETE' });
    if (res.ok) {
      if (expanded === id) setExpanded(null);
      await fetchJourneys();
    } else {
      alert('Failed to delete: ' + (typeof res.data === 'object' ? JSON.stringify(res.data) : res.data));
    }
    setDeleting(false);
  };

  if (loading) return <Loading text="Fetching journeys..." />;
  if (journeys.length === 0) return <Empty text="No journeys found" />;

  return <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
    {journeys.map(j => <Card key={j._id} style={{ cursor: 'pointer' }}>
      <div onClick={() => expand(j._id)} style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '24px', fontFamily: 'var(--mono)', color: 'var(--accent)' }}>[J]</span>
          <div>
            <div style={{ fontWeight: 600, fontSize: '14px' }}>{j.name || 'Unnamed'}</div>
            <div style={{ fontSize: '12px', color: 'var(--muted)', display: 'flex', gap: '12px', marginTop: '4px' }}>
              <span>{j.days_count} day{j.days_count !== 1 ? 's' : ''}</span>
              <span>Owner: {j.owner_id}</span>
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Copyable text={j._id}>{j._id.slice(0,8)}...</Copyable>
          <button onClick={(e) => deleteJourney(j._id, e)} disabled={deleting === j._id} style={{
            background: 'transparent', border: 'none', color: 'var(--red)', cursor: 'pointer',
            padding: '4px', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center',
            opacity: deleting === j._id ? 0.5 : 0.8,
          }} onMouseEnter={e => e.currentTarget.style.background = 'var(--red-bg)'} onMouseLeave={e => e.currentTarget.style.background = 'transparent'} title="Delete journey">
            {deleting === j._id ? 'Deleting...' : 'Delete'}
          </button>
          <span style={{ color: 'var(--muted)', transform: expanded === j._id ? 'rotate(180deg)' : 'none', padding: '0 4px' }}>▼</span>
        </div>
      </div>

      {expanded === j._id && <div style={{ borderTop: '1px solid var(--border)', padding: '20px' }}>
        {detailLoading ? <Loading text="Loading journey details..." /> :
         journeyDetail ? <JourneyDayView journeyId={j._id} days={journeyDetail.days || []} onRefresh={() => expand(j._id)} /> :
         <Empty text="Failed to load" />}
      </div>}
    </Card>)}
  </div>;
}

function JourneyDayView({ journeyId, days, onRefresh }) {
  const goToOptimizer = (dayNum) => {
    window.__targetOptimizeJourneyId = journeyId;
    window.__targetOptimizeDayNumber = String(dayNum);
    if (window.navigateTab) window.navigateTab('optimizer');
  };

  if (!days || days.length === 0) return <Empty text="No days planned yet" />;
  return <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
    {days.map((day, di) => <div key={di}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Badge color="accent">Day {day.day_number}</Badge>
          <span style={{ fontSize: '12px', color: 'var(--muted)' }}>{day.date ? new Date(day.date).toLocaleDateString() : ''}</span>
          <span style={{ fontSize: '12px', color: 'var(--muted)' }}>{(day.stops || []).length} stops</span>
        </div>
        {(day.stops || []).length > 1 && (
          <Btn small onClick={() => goToOptimizer(day.day_number)}>
            Optimize Route
          </Btn>
        )}
      </div>
      {(day.stops || []).length === 0
        ? <div style={{ padding: '12px 16px', color: 'var(--muted)', fontSize: '13px', fontStyle: 'italic' }}>No stops</div>
        : <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', paddingLeft: '12px', borderLeft: '2px solid var(--accent-glow)' }}>
          {day.stops.sort((a,b) => a.order - b.order).map((stop, si) => <StopCard key={si} stop={stop} index={si} />)}
        </div>}
    </div>)}
  </div>;
}

function StopCard({ stop, index }) {
  return <div style={{
    padding: '12px 16px', background: 'rgba(0,0,0,0.15)', borderRadius: 'var(--radius-sm)',
    display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px',
  }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: 0 }}>
      <span style={{
        width: '28px', height: '28px', borderRadius: '50%', background: 'var(--accent-glow)',
        color: 'var(--accent2)', display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '12px', fontWeight: 700, flexShrink: 0,
      }}>{stop.order || index + 1}</span>
      <div style={{ minWidth: 0 }}>
        <div style={{ fontWeight: 600, fontSize: '13px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{stop.place_name || 'Unknown'}</div>
        <div style={{ fontSize: '11px', color: 'var(--muted)', display: 'flex', gap: '8px', marginTop: '2px', flexWrap: 'wrap' }}>
          {stop.category && <Badge color="blue">{stop.category}</Badge>}
          <span>{stop.estimated_duration_minutes || 0}min</span>
          {stop.distance_from_previous_km > 0 && <span>Dist: {stop.distance_from_previous_km}km</span>}
          {stop.travel_time_from_previous_minutes > 0 && <span>Travel: {stop.travel_time_from_previous_minutes}min</span>}
        </div>
      </div>
    </div>
    <Copyable text={stop.place_id}>{(stop.place_id || '').slice(0,6)}...</Copyable>
  </div>;
}
"""
