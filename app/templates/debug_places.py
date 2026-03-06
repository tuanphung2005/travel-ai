"""Debug Dashboard — Places Tab component."""


def get_places_tab_js() -> str:
    return """\
/* ======================== */
/* TAB: PLACES              */
/* ======================== */
function PlacesTab() {
  const [places, setPlaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [catFilter, setCatFilter] = useState('ALL');
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      const res = await api('/api/v1/places?limit=200');
      if (res.ok) setPlaces(res.data.places || []);
      setLoading(false);
    })();
  }, []);

  const categories = useMemo(() => {
    const cats = new Set(places.map(p => p.category));
    return ['ALL', ...Array.from(cats).sort()];
  }, [places]);

  const filtered = useMemo(() => {
    return places.filter(p => {
      if (catFilter !== 'ALL' && p.category !== catFilter) return false;
      if (search && !p.name?.toLowerCase().includes(search.toLowerCase()) && !p._id?.includes(search)) return false;
      return true;
    });
  }, [places, search, catFilter]);

  if (loading) return <Loading text="Fetching places..." />;

  return <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
    <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
      <Input label="Search" value={search} onChange={setSearch} placeholder="Name or ID..." style={{ flex: 1, minWidth: '200px' }} />
      <Select label="Category" value={catFilter} onChange={setCatFilter}
        options={categories.map(c => ({ value: c, label: c }))} style={{ minWidth: '160px' }} />
      <Badge color="muted" style={{ marginBottom: '2px' }}>{filtered.length} / {places.length}</Badge>
    </div>

    <div style={{ borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)', background: 'rgba(0,0,0,0.2)' }}>
            {['Name', 'Category', 'Rating', 'Cost (VND)', 'Duration', 'ID'].map(h =>
              <th key={h} style={{ padding: '10px 14px', textAlign: 'left', fontSize: '11px', fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px', position: 'sticky', top: 0, background: 'var(--surface2)', zIndex: 1 }}>{h}</th>
            )}
          </tr>
        </thead>
        <tbody>
          {filtered.map((p, i) => <React.Fragment key={p._id}>
            <tr onClick={() => setExpanded(expanded === p._id ? null : p._id)}
              style={{ borderBottom: '1px solid var(--border)', cursor: 'pointer', background: expanded === p._id ? 'rgba(139,92,246,0.05)' : 'transparent' }}
              onMouseEnter={e => { if (expanded !== p._id) e.currentTarget.style.background = 'rgba(255,255,255,0.02)'; }}
              onMouseLeave={e => { if (expanded !== p._id) e.currentTarget.style.background = 'transparent'; }}>
              <td style={{ padding: '10px 14px', fontWeight: 500 }}>{p.name}</td>
              <td style={{ padding: '10px 14px' }}><Badge color="blue">{p.category}</Badge></td>
              <td style={{ padding: '10px 14px' }}><Stars rating={p.rating} /></td>
              <td style={{ padding: '10px 14px', fontFamily: 'var(--mono)', fontSize: '12px' }}>{(p.estimated_cost_vnd || 0).toLocaleString()}</td>
              <td style={{ padding: '10px 14px', fontFamily: 'var(--mono)', fontSize: '12px' }}>{p.avg_visit_duration_min || 75}m</td>
              <td style={{ padding: '10px 14px' }}><Copyable text={p._id}>{p._id.slice(0,8)}...</Copyable></td>
            </tr>
            {expanded === p._id && <tr><td colSpan={6} style={{ padding: '0' }}>
              <div style={{ padding: '16px 20px', background: 'rgba(0,0,0,0.15)', borderBottom: '1px solid var(--border)' }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '12px', fontSize: '12px' }}>
                  <div><span style={{ color: 'var(--muted)' }}>Full ID: </span><Copyable text={p._id} /></div>
                  <div><span style={{ color: 'var(--muted)' }}>Google ID: </span>{p.google_id ? <Copyable text={p.google_id} /> : '—'}</div>
                  <div><span style={{ color: 'var(--muted)' }}>Address: </span>{p.address || '—'}</div>
                  <div><span style={{ color: 'var(--muted)' }}>Coords: </span><span style={{ fontFamily: 'var(--mono)' }}>{p.location?.coordinates?.[1]?.toFixed(5)}, {p.location?.coordinates?.[0]?.toFixed(5)}</span></div>
                  <div><span style={{ color: 'var(--muted)' }}>Reviews: </span>{p.reviewCount || 0}</div>
                  <div><span style={{ color: 'var(--muted)' }}>Price Level: </span>{p.priceLevel ?? '—'}</div>
                  <div><span style={{ color: 'var(--muted)' }}>Healing: </span>{p.healing_score ?? '—'}/5</div>
                  <div><span style={{ color: 'var(--muted)' }}>Crowd: </span>{p.crowd_level ?? '—'}/5</div>
                  <div style={{ gridColumn: '1 / -1' }}><span style={{ color: 'var(--muted)' }}>Tags: </span>{(p.tags || []).join(', ') || '—'}</div>
                  {p.description && <div style={{ gridColumn: '1 / -1' }}><span style={{ color: 'var(--muted)' }}>Desc: </span>{p.description}</div>}
                  {p.image_url && <div style={{ gridColumn: '1 / -1' }}><span style={{ color: 'var(--muted)' }}>Image: </span><a href={p.image_url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent2)', textDecoration: 'none' }}>view image ↗</a></div>}
                </div>
              </div>
            </td></tr>}
          </React.Fragment>)}
          {filtered.length === 0 && <tr><td colSpan={6}><Empty text="No places match your filters" icon="🔍" /></td></tr>}
        </tbody>
      </table>
    </div>
  </div>;
}
"""
