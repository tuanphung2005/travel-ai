"""Debug UI HTML template."""


def get_debug_ui_html() -> str:
    """Return the debug UI HTML page."""
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Travel API Debug UI</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; max-width: 1100px; }
    h1 { margin-bottom: 8px; }
    .row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }
    .card { border: 1px solid #ccc; border-radius: 8px; padding: 12px; }
    label { display: block; font-weight: 600; margin-bottom: 4px; }
    input, select, textarea, button { font-size: 14px; padding: 8px; }
    input, select, textarea { width: 100%; box-sizing: border-box; }
    textarea { min-height: 140px; font-family: monospace; }
    .w-1 { flex: 1; min-width: 220px; }
    .w-2 { flex: 2; min-width: 320px; }
    pre { background: #f7f7f7; padding: 12px; border-radius: 8px; overflow: auto; max-height: 420px; }
    .muted { color: #555; font-size: 13px; }
  </style>
</head>
<body>
  <h1>Travel API Debug UI</h1>
  <p class="muted">Interactive request/response tester for quick I/O debugging.</p>

  <div class="card">
    <div class="row">
      <div class="w-1">
        <label for="preset">Preset</label>
        <select id="preset">
          <option value="health">Health</option>
          <option value="places">Places (limit 5)</option>
          <option value="journeys">Journeys (limit 10)</option>
          <option value="journey">Get Journey</option>
          <option value="createRelated">Create Journey (Related Places)</option>
          <option value="aiplan">AI Plan</option>
          <option value="aiexplain">AI Explain</option>
        </select>
      </div>
      <div class="w-1">
        <label for="journeyId">Journey ID</label>
        <input id="journeyId" placeholder="Auto-filled from latest journey" />
      </div>
      <div class="w-1" style="align-self: end;">
        <button id="fetchJourneyBtn">Fetch Latest Journey ID</button>
      </div>
      <div class="w-1">
        <label for="seedPlaceId">Seed Place ID</label>
        <input id="seedPlaceId" placeholder="Optional; auto-filled from latest place" />
      </div>
      <div class="w-1" style="align-self: end;">
        <button id="fetchPlaceBtn">Fetch Latest Place ID</button>
      </div>
    </div>

    <div class="row">
      <div class="w-1">
        <label for="method">Method</label>
        <input id="method" />
      </div>
      <div class="w-2">
        <label for="path">Path</label>
        <input id="path" />
      </div>
    </div>

    <div>
      <label for="body">JSON Body (for POST/PUT/PATCH)</label>
      <textarea id="body"></textarea>
    </div>

    <div style="margin-top: 12px;">
      <button id="sendBtn">Send Request</button>
    </div>
  </div>

  <div class="row" style="margin-top: 16px;">
    <div class="card w-1">
      <label>Response Status</label>
      <pre id="status">-</pre>
    </div>
    <div class="card w-2">
      <label>Response Body</label>
      <pre id="output">-</pre>
    </div>
  </div>

  <script>
    const presetEl = document.getElementById('preset');
    const journeyIdEl = document.getElementById('journeyId');
    const seedPlaceIdEl = document.getElementById('seedPlaceId');
    const methodEl = document.getElementById('method');
    const pathEl = document.getElementById('path');
    const bodyEl = document.getElementById('body');
    const statusEl = document.getElementById('status');
    const outputEl = document.getElementById('output');

    function pretty(value) {
      try {
        return JSON.stringify(typeof value === 'string' ? JSON.parse(value) : value, null, 2);
      } catch {
        return String(value);
      }
    }

    function getJourneyId() {
      return (journeyIdEl.value || '').trim();
    }

    function applyPreset() {
      const id = getJourneyId();
      const preset = presetEl.value;

      if (preset === 'health') {
        methodEl.value = 'GET';
        pathEl.value = '/health';
        bodyEl.value = '';
        return;
      }
      if (preset === 'places') {
        methodEl.value = 'GET';
        pathEl.value = '/api/v1/places?limit=5';
        bodyEl.value = '';
        return;
      }
      if (preset === 'journeys') {
        methodEl.value = 'GET';
        pathEl.value = '/api/v1/journeys?limit=10';
        bodyEl.value = '';
        return;
      }
      if (preset === 'journey') {
        methodEl.value = 'GET';
        pathEl.value = `/api/v1/journeys/${id || '<journey_id>'}`;
        bodyEl.value = '';
        return;
      }
      if (preset === 'createRelated') {
        methodEl.value = 'POST';
        pathEl.value = '/api/v1/journeys/auto-create-related';
        bodyEl.value = JSON.stringify({
          name: 'Auto Journey from Related Places',
          owner_id: 'debug-user',
          start_date: '2026-03-01T00:00:00Z',
          end_date: '2026-03-03T00:00:00Z',
          seed_place_id: (seedPlaceIdEl.value || '').trim() || null,
          max_places: 10,
          hours_per_day: 8,
          travel_style: 'balanced',
          auto_plan: true,
          members: []
        }, null, 2);
        return;
      }
      if (preset === 'aiplan') {
        methodEl.value = 'POST';
        pathEl.value = `/api/v1/journeys/${id || '<journey_id>'}/ai-plan`;
        bodyEl.value = JSON.stringify({ hours_per_day: 8, travel_style: 'balanced' }, null, 2);
        return;
      }
      if (preset === 'aiexplain') {
        methodEl.value = 'GET';
        pathEl.value = `/api/v1/journeys/${id || '<journey_id>'}/ai-explain`;
        bodyEl.value = '';
      }
    }

    async function fetchLatestJourneyId() {
      try {
        const res = await fetch('/api/v1/journeys?limit=1');
        const data = await res.json();
        const latest = data?.journeys?.[0]?._id;
        if (latest) {
          journeyIdEl.value = latest;
          applyPreset();
          statusEl.textContent = 'Auto-fetched latest journey ID';
        } else {
          statusEl.textContent = 'No journeys found';
        }
      } catch (err) {
        statusEl.textContent = 'Failed to fetch latest journey ID';
        outputEl.textContent = String(err);
      }
    }

    async function fetchLatestPlaceId() {
      try {
        const res = await fetch('/api/v1/places?limit=1');
        const data = await res.json();
        const latest = data?.places?.[0]?._id;
        if (latest) {
          seedPlaceIdEl.value = latest;
          applyPreset();
          statusEl.textContent = 'Auto-fetched latest place ID';
        } else {
          statusEl.textContent = 'No places found';
        }
      } catch (err) {
        statusEl.textContent = 'Failed to fetch latest place ID';
        outputEl.textContent = String(err);
      }
    }

    async function sendRequest() {
      const method = (methodEl.value || 'GET').toUpperCase();
      const path = pathEl.value.trim();

      if (!path.startsWith('/')) {
        statusEl.textContent = 'Path must start with /';
        return;
      }

      const options = { method, headers: {} };
      const bodyText = bodyEl.value.trim();

      if (['POST', 'PUT', 'PATCH'].includes(method) && bodyText) {
        options.headers['Content-Type'] = 'application/json';
        options.body = bodyText;
      }

      try {
        const res = await fetch(path, options);
        const text = await res.text();
        statusEl.textContent = `${res.status} ${res.statusText}`;
        outputEl.textContent = pretty(text);
      } catch (err) {
        statusEl.textContent = 'Request failed';
        outputEl.textContent = String(err);
      }
    }

    document.getElementById('fetchJourneyBtn').addEventListener('click', fetchLatestJourneyId);
    document.getElementById('fetchPlaceBtn').addEventListener('click', fetchLatestPlaceId);
    document.getElementById('sendBtn').addEventListener('click', sendRequest);
    presetEl.addEventListener('change', applyPreset);
    journeyIdEl.addEventListener('change', applyPreset);
    seedPlaceIdEl.addEventListener('change', applyPreset);

    applyPreset();
    fetchLatestJourneyId();
    fetchLatestPlaceId();
  </script>
</body>
</html>
"""
