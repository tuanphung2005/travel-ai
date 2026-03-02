"""Debug UI HTML template using renderjson for smart JSON viewing."""

def get_debug_ui_html() -> str:
    """Return the debug UI HTML page with renderjson-powered response viewer."""
    return """\
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Travel API Debug UI</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/renderjson@1.4.0/renderjson.min.js"></script>
  <style>
    *, *::before, *::after { box-sizing: border-box; }
    :root {
      --bg: #09090b; 
      --surface: rgba(24, 24, 27, 0.7); 
      --surface-hover: rgba(39, 39, 42, 0.8);
      --surface2: #18181b;
      --border: rgba(255, 255, 255, 0.1); 
      --text: #fafafa; 
      --muted: #a1a1aa;
      --accent: #8b5cf6; 
      --accent-hover: #7c3aed;
      --accent-glow: rgba(139, 92, 246, 0.4);
      --green: #10b981; --green-glow: rgba(16, 185, 129, 0.2);
      --red: #ef4444; --red-glow: rgba(239, 68, 68, 0.2);
      --orange: #f59e0b; --orange-glow: rgba(245, 158, 11, 0.2);
      --mono: 'Fira Code', monospace;
      --sans: 'Inter', system-ui, sans-serif;
    }
    body { 
      font-family: var(--sans); 
      background-color: var(--bg); 
      background-image: 
        radial-gradient(at 0% 0%, rgba(139, 92, 246, 0.08) 0px, transparent 40%),
        radial-gradient(at 100% 100%, rgba(16, 185, 129, 0.05) 0px, transparent 40%);
      background-attachment: fixed;
      color: var(--text); 
      margin: 0;
      padding: 0;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    
    .header {
      padding: 20px 40px;
      border-bottom: 1px solid var(--border);
      background: rgba(9, 9, 11, 0.6);
      backdrop-filter: blur(12px);
      position: sticky;
      top: 0;
      z-index: 10;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    
    .header h1 {
      font-size: 20px;
      font-weight: 700;
      margin: 0;
      display: flex;
      align-items: center;
      gap: 12px;
      background: linear-gradient(135deg, #fff 0%, #a1a1aa 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      letter-spacing: -0.5px;
    }

    .header h1 svg {
      color: var(--accent);
    }
    
    .content {
      display: grid;
      grid-template-columns: 420px 1fr;
      gap: 24px;
      padding: 32px 40px;
      flex: 1;
      max-width: 1800px;
      margin: 0 auto;
      width: 100%;
      height: calc(100vh - 73px);
    }
    
    .card { 
      background: var(--surface); 
      backdrop-filter: blur(16px);
      border: 1px solid var(--border); 
      border-radius: 16px; 
      display: flex;
      flex-direction: column;
      box-shadow: 0 8px 32px rgba(0,0,0,0.2);
      overflow: hidden;
    }
    
    .card-header {
      padding: 16px 24px;
      border-bottom: 1px solid var(--border);
      background: rgba(255,255,255,0.02);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .card-body {
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 20px;
      overflow-y: auto;
      flex: 1;
    }
    
    .card-title {
      font-size: 13px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--muted);
      margin: 0;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .card-title::before {
      content: '';
      display: block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent);
      box-shadow: 0 0 10px var(--accent-glow);
    }

    .response-card-title::before {
      background: var(--green);
      box-shadow: 0 0 10px var(--green-glow);
    }
    
    label { 
      display: block; 
      font-size: 12px; 
      font-weight: 500; 
      color: var(--muted); 
      margin-bottom: 8px; 
      transition: color 0.2s;
    }
    
    .input-wrapper:focus-within label {
      color: var(--text);
    }
    
    input, select, textarea {
      width: 100%; 
      font-size: 13px; 
      padding: 10px 14px; 
      background: rgba(0,0,0,0.3);
      color: var(--text); 
      border: 1px solid var(--border); 
      border-radius: 8px; 
      font-family: var(--mono);
      transition: all 0.2s ease;
    }
    
    input::placeholder, textarea::placeholder {
      color: rgba(255,255,255,0.2);
    }
    
    input:focus, select:focus, textarea:focus { 
      outline: none; 
      border-color: var(--accent); 
      box-shadow: 0 0 0 2px var(--accent-glow);
      background: rgba(0,0,0,0.5);
    }
    
    select {
      appearance: none;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23a1a1aa'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 12px center;
      background-size: 16px;
      padding-right: 36px;
      font-family: var(--sans);
      cursor: pointer;
    }
    
    textarea { 
      min-height: 240px;
      resize: vertical; 
      line-height: 1.5;
    }
    
    .row { 
      display: flex; 
      gap: 16px; 
    }
    .row > * { flex: 1; min-width: 0; }
    
    .flex-group {
      display: flex;
      gap: 8px;
    }
    
    button {
      font-family: var(--sans);
      font-size: 13px; 
      font-weight: 600; 
      padding: 10px 20px; 
      border: none; 
      border-radius: 8px; 
      cursor: pointer;
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }
    
    .btn-primary { 
      background: var(--accent); 
      color: #fff; 
      box-shadow: 0 4px 14px var(--accent-glow);
      width: 100%;
      padding: 12px;
      font-size: 14px;
      margin-top: 8px;
    }
    
    .btn-primary:hover { 
      background: var(--accent-hover); 
      transform: translateY(-1px);
      box-shadow: 0 6px 20px var(--accent-glow);
    }
    
    .btn-primary:active {
      transform: translateY(1px);
    }
    
    .btn-icon {
      padding: 10px;
      background: rgba(255,255,255,0.05);
      border: 1px solid var(--border);
      color: var(--text);
      flex-shrink: 0;
    }
    
    .btn-icon:hover {
      background: rgba(255,255,255,0.1);
      border-color: rgba(255,255,255,0.2);
    }

    .btn-icon svg {
      width: 16px;
      height: 16px;
    }
    
    .status-badge {
      font-family: var(--mono); 
      font-size: 12px; 
      font-weight: 600;
      padding: 4px 12px; 
      border-radius: 20px; 
      background: rgba(0,0,0,0.3); 
      border: 1px solid transparent;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      opacity: 0;
      transition: opacity 0.3s ease;
    }
    
    .status-badge.visible {
      opacity: 1;
    }

    .status-badge::before {
      content: '';
      display: block;
      width: 6px;
      height: 6px;
      border-radius: 50%;
    }
    
    .s2xx { color: var(--green); border-color: var(--green-glow); background: rgba(16, 185, 129, 0.1); }
    .s2xx::before { background: var(--green); box-shadow: 0 0 8px var(--green); }
    
    .s4xx { color: var(--orange); border-color: var(--orange-glow); background: rgba(245, 158, 11, 0.1); }
    .s4xx::before { background: var(--orange); box-shadow: 0 0 8px var(--orange); }
    
    .s5xx { color: var(--red); border-color: var(--red-glow); background: rgba(239, 68, 68, 0.1); }
    .s5xx::before { background: var(--red); box-shadow: 0 0 8px var(--red); }
    
    #timing { 
      color: var(--muted); 
      font-size: 12px; 
      font-family: var(--mono);
      background: rgba(0,0,0,0.3);
      padding: 4px 12px;
      border-radius: 20px;
      border: 1px solid var(--border);
      opacity: 0;
      transition: opacity 0.3s ease;
    }

    #timing.visible {
      opacity: 1;
    }
    
    .toggle-group {  
      display: flex; 
      background: rgba(0,0,0,0.3);
      border-radius: 8px; 
      padding: 4px;
      border: 1px solid var(--border); 
    }
    
    .toggle-group button { 
      background: transparent; 
      color: var(--muted); 
      padding: 6px 14px; 
      font-size: 12px; 
      border-radius: 6px;
    }
    
    .toggle-group button:hover {
      color: var(--text);
    }
    
    .toggle-group button.active { 
      background: var(--surface2); 
      color: var(--text); 
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    
    .response-area {
      flex: 1;
      overflow: auto;
      background: rgba(0,0,0,0.3);
      border-radius: 12px;
      border: 1px solid var(--border);
      padding: 20px;
      position: relative;
    }

    #jsonOutput, #rawOutput { 
      height: 100%;
    }
    
    #rawOutput { 
      display: none; 
      font-family: var(--mono); 
      font-size: 13px; 
      line-height: 1.6;
      white-space: pre-wrap; 
      word-break: break-all;
      margin: 0;
    }

    .renderjson { 
      font-family: var(--mono); 
      font-size: 13px; 
      line-height: 1.7; 
    }
    .renderjson a { text-decoration: none; display: inline-block; padding: 0 4px; border-radius: 4px; }
    .renderjson a:hover { background: rgba(255,255,255,0.1); }
    .renderjson .disclosure { color: var(--muted); font-size: 14px; }
    .renderjson .syntax { color: var(--muted); }
    .renderjson .string { color: #a5d6ff; }
    .renderjson .number { color: #79c0ff; }
    .renderjson .boolean { color: #ff7b72; font-weight: 600; }
    .renderjson .key    { color: #d2a8ff; font-weight: 500; }
    .renderjson .keyword { color: #ff7b72; }
    .renderjson .object.syntax { color: #8b949e; }
    .renderjson .array.syntax  { color: #8b949e; }
    
    .empty-state {
      position: absolute;
      inset: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      color: var(--muted);
      gap: 16px;
      transition: opacity 0.3s;
    }

    .empty-state.hidden {
      opacity: 0;
      pointer-events: none;
    }
    
    .empty-state svg {
      width: 48px;
      height: 48px;
      opacity: 0.3;
      color: var(--accent);
    }

    @media (max-width: 1024px) {
      .content { grid-template-columns: 1fr; height: auto; }
      .response-card { min-height: 600px; }
    }
    
    .spinner {
      width: 16px;
      height: 16px;
      border: 2px solid rgba(255,255,255,0.3);
      border-radius: 50%;
      border-top-color: #fff;
      animation: spin 0.8s linear infinite;
      display: none;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .loading .spinner { display: inline-block; }
    .loading .send-icon { display: none; }
  </style>
</head>
<body>
  <header class="header">
    <h1>
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m8 3 4 8 5-5 5 15H2L8 3z"/></svg>
      Travel API Explorer
    </h1>
    <div style="display: flex; gap: 8px;">
      <span class="status-badge s2xx visible" id="statusBadge">READY</span>
      <span id="timing"></span>
    </div>
  </header>

  <main class="content">
    <div class="card request-card">
      <div class="card-header">
        <h2 class="card-title">Request Configuration</h2>
        <div class="toggle-group" style="padding: 2px">
            <select id="preset" style="border: none; background: transparent; padding: 4px 28px 4px 8px; font-size: 12px; height: auto; box-shadow: none;">
                <option value="health">✅ Health Check</option>
                <option value="places">📍 Places List (limit 5)</option>
                <option value="journeys">🗺️ Journeys List (limit 10)</option>
                <option value="journey">🔍 Get Journey</option>
                <option value="createRelated">✨ Create Journey (Auto)</option>
                <option value="aiplan">🤖 AI Plan</option>
                <option value="aiexplain">💬 AI Explain</option>
                <option value="improveRoute">🔄 Improve Route Order</option>
            </select>
        </div>
      </div>
      
      <div class="card-body">
        <div class="row">
          <div class="input-wrapper">
            <label>Method</label>
            <select id="method">
              <option value="GET">GET</option>
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
              <option value="PATCH">PATCH</option>
              <option value="DELETE">DELETE</option>
            </select>
          </div>
          <div class="input-wrapper" style="flex: 2;">
            <label>Path</label>
            <input id="path" placeholder="/api/v1/..." spellcheck="false" />
          </div>
        </div>

        <div class="row">
          <div class="input-wrapper">
            <label>Journey ID <span style="font-weight: normal; opacity: 0.6;">(Auto-filled)</span></label>
            <div class="flex-group">
              <input id="journeyId" placeholder="ID..." />
              <button class="btn-icon" id="fetchJourneyBtn" title="Fetch latest Journey">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 2v6h-6"/><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 2v6h6"/></svg>
              </button>
            </div>
          </div>
          <div class="input-wrapper">
            <label>Seed Place ID</label>
            <div class="flex-group">
              <input id="seedPlaceId" placeholder="Optional" />
              <button class="btn-icon" id="fetchPlaceBtn" title="Fetch latest Place">
                 <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 2v6h-6"/><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 2v6h6"/></svg>
              </button>
            </div>
          </div>
        </div>
        
        <div class="input-wrapper" style="width: 50%;">
            <label>Day Number</label>
            <input id="dayNumber" type="number" min="1" value="1" />
        </div>

        <div class="input-wrapper" style="flex: 1; display: flex; flex-direction: column;">
          <label>Request Body (JSON)</label>
          <textarea id="body" spellcheck="false" placeholder="{}"></textarea>
        </div>

        <button class="btn-primary" id="sendBtn">
          <svg class="send-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
          <div class="spinner"></div>
          <span id="sendBtnText">Send Request</span>
        </button>
      </div>
    </div>

    <div class="card response-card">
      <div class="card-header">
        <h2 class="card-title response-card-title">Response View</h2>
        <div class="toggle-group">
          <button id="btnSmart" class="active" onclick="setView('smart')">Smart</button>
          <button id="btnRaw" onclick="setView('raw')">Raw</button>
        </div>
      </div>
      
      <div class="card-body" style="padding: 16px;">
        <div class="response-area">
          <div id="emptyState" class="empty-state">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m10 14 4-4"/><path d="m14 14-4-4"/><path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/></svg>
            <p style="margin: 0; font-size: 14px;">Awaiting request...</p>
          </div>
          <div id="jsonOutput"></div>
          <pre id="rawOutput"></pre>
        </div>
      </div>
    </div>
  </main>

  <script>
    renderjson.set_show_to_level(2);
    renderjson.set_icons('+', '-');
    renderjson.set_sort_objects(false);
    renderjson.set_max_string_length(120);

    const $ = id => document.getElementById(id);
    let currentView = 'smart';

    function setView(mode) {
      currentView = mode;
      $('btnSmart').classList.toggle('active', mode === 'smart');
      $('btnRaw').classList.toggle('active', mode === 'raw');
      $('jsonOutput').style.display = mode === 'smart' ? '' : 'none';
      $('rawOutput').style.display  = mode === 'raw'   ? '' : 'none';
    }

    function applyPreset() {
      const id = $('journeyId').value.trim();
      const seed = $('seedPlaceId').value.trim();
      const dayNumber = Math.max(1, Number($('dayNumber').value || 1));
      const p = $('preset').value;

      const defaultAiPlanBody = {
        total_budget_vnd: 3000000,
        daily_budget_vnd: 1000000,
        mode: 'solo',
        mood: 'NATURE_EXPLORE',
        mood_distribution: null,
        start_location: null,
        max_places_per_day: 5,
        must_include_categories: [],
        exclude_categories: [],
        hours_per_day: 8,
        travel_style: 'balanced',
        place_ids: null,
      };

      const defaultCreateRelatedBody = {
        name: 'Auto Journey',
        owner_id: 'debug-user',
        start_date: '2026-03-01T00:00:00Z',
        end_date: '2026-03-03T00:00:00Z',
        seed_place_id: seed || null,
        max_places: 10,
        hours_per_day: 8,
        travel_style: 'balanced',
        total_budget_vnd: 3000000,
        daily_budget_vnd: 1000000,
        mode: 'solo',
        mood: 'NATURE_EXPLORE',
        auto_plan: true,
        members: [],
      };

      const presets = {
        health:        ['GET', '/health', ''],
        places:        ['GET', '/api/v1/places?limit=5', ''],
        journeys:      ['GET', '/api/v1/journeys?limit=10', ''],
        journey:       ['GET', `/api/v1/journeys/${id||'<id>'}`, ''],
        aiplan:        ['POST', `/api/v1/journeys/${id||'<id>'}/ai-plan`, JSON.stringify(defaultAiPlanBody, null, 2)],
        aiexplain:     ['GET', `/api/v1/journeys/${id||'<id>'}/ai-explain`, ''],
        createRelated: ['POST', '/api/v1/journeys/auto-create-related', JSON.stringify(defaultCreateRelatedBody, null, 2)],
        improveRoute:  ['POST', `/api/v1/journeys/${id||'<id>'}/days/${dayNumber}/improve-route-order`, ''],
      };
      
      const [m, path, body] = presets[p] || presets.health;
      $('method').value = m; 
      $('path').value = path; 
      $('body').value = body;
    }

    async function fetchLatest(endpoint, field, inputId) {
      const btn = $(inputId === 'journeyId' ? 'fetchJourneyBtn' : 'fetchPlaceBtn');
      const icon = btn.innerHTML;
      btn.innerHTML = '<div class="spinner" style="display:inline-block; width:12px; height:12px; border-width:2px; border-top-color:var(--accent);"></div>';
      
      try {
        const data = await (await fetch(endpoint)).json();
        const val = data?.[field]?.[0]?._id;
        if (val) { 
          $(inputId).value = val; 
          applyPreset(); 
        }
      } catch (e) {
        console.error('Failed to fetch:', e);
      } finally {
        btn.innerHTML = icon;
      }
    }

    async function sendRequest() {
      const method = $('method').value.toUpperCase();
      const path = $('path').value.trim();
      if (!path.startsWith('/')) {
        alert("Path must start with /");
        return;
      }

      const opts = { method, headers: {} };
      const bodyText = $('body').value.trim();
      if (['POST','PUT','PATCH'].includes(method) && bodyText) {
        opts.headers['Content-Type'] = 'application/json';
        opts.body = bodyText;
      }

      $('sendBtn').classList.add('loading');
      $('sendBtnText').textContent = 'Sending...';
      $('emptyState').classList.add('hidden');
      $('statusBadge').classList.remove('visible', 's2xx', 's4xx', 's5xx');
      $('timing').classList.remove('visible');
      
      const t0 = performance.now();

      try {
        const res = await fetch(path, opts);
        const ms = Math.round(performance.now() - t0);
        
        $('timing').textContent = ms + 'ms';
        $('timing').classList.add('visible');
        
        $('statusBadge').textContent = `${res.status} ${res.statusText || ''}`.trim();
        $('statusBadge').className = `status-badge visible ${res.status < 300 ? 's2xx' : res.status < 500 ? 's4xx' : 's5xx'}`;

        const text = await res.text();
        try {
          const json = JSON.parse(text);
          $('rawOutput').textContent = JSON.stringify(json, null, 2);
          $('jsonOutput').innerHTML = '';
          $('jsonOutput').appendChild(renderjson(json));
          setView(currentView);
        } catch {
          $('rawOutput').textContent = text;
          $('jsonOutput').textContent = text;
          setView('raw');
        }
      } catch (err) {
        $('statusBadge').textContent = 'FETCH ERROR';
        $('statusBadge').className = 'status-badge visible s5xx';
        $('rawOutput').textContent = String(err);
        $('jsonOutput').textContent = String(err);
        setView('raw');
      } finally {
        $('sendBtn').classList.remove('loading');
        $('sendBtnText').textContent = 'Send Request';
      }
    }

    $('fetchJourneyBtn').addEventListener('click', () => fetchLatest('/api/v1/journeys?limit=1','journeys','journeyId'));
    $('fetchPlaceBtn').addEventListener('click', () => fetchLatest('/api/v1/places?limit=1','places','seedPlaceId'));
    $('sendBtn').addEventListener('click', sendRequest);
    $('preset').addEventListener('change', applyPreset);
    $('journeyId').addEventListener('change', applyPreset);
    $('seedPlaceId').addEventListener('change', applyPreset);
    $('dayNumber').addEventListener('change', applyPreset);

    // Initial setup
    applyPreset();
    fetchLatest('/api/v1/journeys?limit=1','journeys','journeyId').then(() => {
      fetchLatest('/api/v1/places?limit=1','places','seedPlaceId');
    });
  </script>
</body>
</html>"""
