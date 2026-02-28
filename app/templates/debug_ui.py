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
  <script src="https://cdn.jsdelivr.net/npm/renderjson@1.4.0/renderjson.min.js"></script>
  <style>
    *, *::before, *::after { box-sizing: border-box; }
    :root {
      --bg: #0f1117; --surface: #1a1d27; --surface2: #252830;
      --border: #2e3140; --text: #e1e4ed; --muted: #8b8fa3;
      --accent: #6c72ff; --green: #3dd68c; --red: #ff6b6b; --orange: #ffb347;
      --mono: 'Menlo','Fira Code',monospace;
    }
    body { font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); padding: 24px; }
    h1 { font-size: 20px; margin-bottom: 16px; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 16px; margin-bottom: 16px; }
    label { display: block; font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--muted); margin-bottom: 4px; }
    input, select, textarea {
      width: 100%; font-size: 13px; padding: 8px 10px; background: var(--surface2);
      color: var(--text); border: 1px solid var(--border); border-radius: 6px; font-family: var(--mono);
    }
    input:focus, select:focus, textarea:focus { outline: none; border-color: var(--accent); }
    textarea { min-height: 100px; resize: vertical; }
    .row { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 10px; }
    .row > * { flex: 1; min-width: 160px; }
    button {
      font-size: 13px; font-weight: 600; padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer;
    }
    .btn-primary { background: var(--accent); color: #fff; }
    .btn-primary:hover { filter: brightness(1.15); }
    .btn-sm { padding: 5px 10px; font-size: 11px; background: var(--surface2); color: var(--muted); border: 1px solid var(--border); }
    #statusBadge {
      display: inline-block; font-family: var(--mono); font-size: 13px; font-weight: 600;
      padding: 4px 12px; border-radius: 20px; background: var(--surface2); border: 1px solid var(--border);
    }
    .s2xx { color: var(--green); border-color: rgba(61,214,140,.3); }
    .s4xx { color: var(--orange); border-color: rgba(255,179,71,.3); }
    .s5xx { color: var(--red); border-color: rgba(255,107,107,.3); }
    #timing { color: var(--muted); font-size: 12px; margin-left: 12px; }
    .response-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
    .toggle-group { margin-left: auto; display: flex; border-radius: 6px; overflow: hidden; border: 1px solid var(--border); }
    .toggle-group button { background: var(--surface2); color: var(--muted); border: none; padding: 5px 14px; font-size: 11px; font-weight: 600; cursor: pointer; }
    .toggle-group button.active { background: var(--accent); color: #fff; }
    #jsonOutput { max-height: 600px; overflow: auto; }
    #rawOutput { display: none; max-height: 600px; overflow: auto; background: var(--surface2); border-radius: 8px; padding: 14px;
      font-family: var(--mono); font-size: 12px; white-space: pre-wrap; word-break: break-all; }

    /* renderjson overrides for dark theme */
    .renderjson a { text-decoration: none !important; }
    .renderjson { font-family: var(--mono); font-size: 12px; line-height: 1.6; }
  </style>
</head>
<body>
  <h1>Travel API &middot; Debug UI</h1>

  <div class="card">
    <div class="row">
      <div style="max-width:180px"><label>Preset</label><select id="preset">
        <option value="health">Health</option>
        <option value="places">Places (limit 5)</option>
        <option value="journeys">Journeys (limit 10)</option>
        <option value="journey">Get Journey</option>
        <option value="createRelated">Create Journey (Related)</option>
        <option value="aiplan">AI Plan</option>
        <option value="aiexplain">AI Explain</option>
        <option value="improveRoute">Improve Route Order</option>
      </select></div>
      <div><label>Journey ID</label><div style="display:flex;gap:6px"><input id="journeyId" placeholder="Auto-filled" /><button class="btn-sm" id="fetchJourneyBtn">&circlearrowright;</button></div></div>
      <div><label>Seed Place ID</label><div style="display:flex;gap:6px"><input id="seedPlaceId" placeholder="Optional" /><button class="btn-sm" id="fetchPlaceBtn">&circlearrowright;</button></div></div>
      <div style="max-width:140px"><label>Day Number</label><input id="dayNumber" type="number" min="1" value="1" /></div>
    </div>
    <div class="row">
      <div style="max-width:90px"><label>Method</label><input id="method" /></div>
      <div><label>Path</label><input id="path" /></div>
    </div>
    <div><label>JSON Body</label><textarea id="body"></textarea></div>
    <div style="margin-top:12px;display:flex;align-items:center">
      <button class="btn-primary" id="sendBtn">&#9654; Send</button>
      <span id="timing"></span>
    </div>
  </div>

  <div class="card">
    <div class="response-header">
      <span style="font-weight:600;font-size:13px;color:var(--muted)">RESPONSE</span>
      <span id="statusBadge">&mdash;</span>
      <div class="toggle-group">
        <button id="btnSmart" class="active" onclick="setView('smart')">Smart</button>
        <button id="btnRaw" onclick="setView('raw')">Raw</button>
      </div>
    </div>
    <div id="jsonOutput"></div>
    <pre id="rawOutput">Send a request to see the response.</pre>
  </div>

  <script>
    // Configure renderjson
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
      $('method').value = m; $('path').value = path; $('body').value = body;
    }

    async function fetchLatest(endpoint, field, inputId) {
      try {
        const data = await (await fetch(endpoint)).json();
        const val = data?.[field]?.[0]?._id;
        if (val) { $(inputId).value = val; applyPreset(); }
      } catch {}
    }

    async function sendRequest() {
      const method = ($('method').value || 'GET').toUpperCase();
      const path = $('path').value.trim();
      if (!path.startsWith('/')) return;

      const opts = { method, headers: {} };
      const bodyText = $('body').value.trim();
      if (['POST','PUT','PATCH'].includes(method) && bodyText) {
        opts.headers['Content-Type'] = 'application/json';
        opts.body = bodyText;
      }

      $('statusBadge').textContent = '...';
      $('statusBadge').className = '';
      $('timing').textContent = '';
      const t0 = performance.now();

      try {
        const res = await fetch(path, opts);
        const ms = Math.round(performance.now() - t0);
        $('timing').textContent = ms + ' ms';
        $('statusBadge').textContent = res.status + ' ' + res.statusText;
        $('statusBadge').className = res.status < 300 ? 's2xx' : res.status < 500 ? 's4xx' : 's5xx';

        const text = await res.text();
        try {
          const json = JSON.parse(text);
          $('rawOutput').textContent = JSON.stringify(json, null, 2);
          $('jsonOutput').innerHTML = '';
          $('jsonOutput').appendChild(renderjson(json));
        } catch {
          $('rawOutput').textContent = text;
          $('jsonOutput').textContent = text;
        }
      } catch (err) {
        $('statusBadge').textContent = 'Error';
        $('statusBadge').className = 's5xx';
        $('rawOutput').textContent = String(err);
        $('jsonOutput').textContent = String(err);
      }
    }

    $('fetchJourneyBtn').addEventListener('click', () => fetchLatest('/api/v1/journeys?limit=1','journeys','journeyId'));
    $('fetchPlaceBtn').addEventListener('click', () => fetchLatest('/api/v1/places?limit=1','places','seedPlaceId'));
    $('sendBtn').addEventListener('click', sendRequest);
    $('preset').addEventListener('change', applyPreset);
    $('journeyId').addEventListener('change', applyPreset);
    $('seedPlaceId').addEventListener('change', applyPreset);
    $('dayNumber').addEventListener('change', applyPreset);

    applyPreset();
    fetchLatest('/api/v1/journeys?limit=1','journeys','journeyId');
    fetchLatest('/api/v1/places?limit=1','places','seedPlaceId');
  </script>
</body>
</html>"""
