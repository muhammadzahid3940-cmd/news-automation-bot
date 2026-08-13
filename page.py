PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>News Automation Bot &mdash; Night Desk</title>
<meta name="description" content="AI sports-desk: run a dispatch for any sport and read today's edition plus live scores.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='14' fill='%230B1E15'/%3E%3Cpath d='M50 78V34M50 34c0-8 8-14 16-16M50 34c0-8-8-14-16-16M18 78h64' stroke='%23FF6A2A' stroke-width='7' fill='none' stroke-linecap='round'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">

  <style>
  :root{
    --pitch:#0B1E15; --pitch-2:#0D241A; --panel:#123025; --panel-2:#17392B;
    --chalk:#F2EFE3; --soft:#C2CFC3; --muted:#82A08E; --faint:#4E6B5B;
    --line:#264636; --line-strong:#3A5F48;
    --accent:#FF6A2A; --accent-soft:#FFA36B; --accent-ink:#1C0E04;
    --live:#FFC94A; --ok:#7FD6A0; --err:#FF8C80;
    --f-display:'Oswald','Arial Narrow','Arial Black',sans-serif;
    --f-body:'Inter','Segoe UI',system-ui,sans-serif;
    --f-mono:'JetBrains Mono','Cascadia Mono','Consolas',monospace;
    --ease:cubic-bezier(.22,.61,.36,1);
  }
  *{box-sizing:border-box}
  html{scroll-behavior:smooth}
  html,body{margin:0}
  body{
    background:
      radial-gradient(1000px 480px at 16% -140px,rgba(255,106,42,.13),transparent 62%),
      radial-gradient(900px 440px at 100% -120px,rgba(255,201,74,.06),transparent 60%),
      repeating-linear-gradient(90deg,var(--pitch) 0,var(--pitch) 150px,var(--pitch-2) 150px,var(--pitch-2) 300px);
    color:var(--chalk);
    font-family:var(--f-body);font-size:16px;line-height:1.6;
    -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;
  }
  ::selection{background:rgba(255,106,42,.45);color:#fff}
  a{color:inherit}
  .wrap{max-width:940px;margin:0 auto;padding:26px 20px 72px}

  /* Stadium masthead */
  .stadium{
    position:sticky;top:0;z-index:50;
    display:flex;align-items:center;justify-content:space-between;gap:16px;
    background:rgba(11,30,21,.88);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);
    border:1px solid var(--line);border-top:3px solid var(--accent);
    padding:10px 16px;margin-bottom:22px;
  }
  .brand{display:flex;align-items:center;gap:12px;min-width:0}
  .mark{
    width:36px;height:36px;flex:none;display:grid;place-items:center;
    border:1px solid var(--line-strong);border-radius:4px;color:var(--accent);
  }
  .mark svg{width:20px;height:20px}
  .brand h1{font-family:var(--f-display);font-weight:600;font-size:1.12rem;letter-spacing:.04em;text-transform:uppercase;margin:0;line-height:1.05;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .brand h1 em{font-style:normal;color:var(--accent)}
  .brand small{display:block;font-family:var(--f-mono);font-size:.54rem;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);margin-top:3px;font-weight:500}
  .board{display:flex;align-items:center;gap:10px;flex:none}
  .lcd{
    font-family:var(--f-mono);font-weight:700;font-size:.82rem;letter-spacing:.06em;
    background:var(--panel);border:1px solid var(--line-strong);border-radius:4px;
    padding:7px 12px;color:var(--accent-soft);white-space:nowrap;
  }
  .lcd::before{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--accent);margin-right:8px;vertical-align:1px;box-shadow:0 0 10px var(--accent)}
  .lcd.running{border-color:rgba(255,201,74,.55);color:var(--live)}
  .lcd.running::before{background:var(--live);box-shadow:0 0 10px var(--live);animation:blink 1s steps(2) infinite}
  .status-chip{
    font-family:var(--f-mono);font-weight:700;font-size:.56rem;letter-spacing:.16em;text-transform:uppercase;
    padding:6px 11px;border:1px solid var(--line-strong);border-radius:2px;background:var(--panel);color:var(--muted);white-space:nowrap;
    transition:background .2s var(--ease),color .2s var(--ease),border-color .2s var(--ease);
  }
  .status-chip.running{color:var(--live);border-color:rgba(255,201,74,.5);background:rgba(255,201,74,.08)}
  .status-chip.running::before{content:"";display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--live);margin-right:7px;animation:blink 1s steps(2) infinite}
  .status-chip.done{color:var(--ok);border-color:rgba(127,214,160,.45);background:rgba(127,214,160,.07)}
  .status-chip.error{color:var(--err);border-color:rgba(255,140,128,.5);background:rgba(255,140,128,.07)}
  @keyframes blink{50%{opacity:.25}}

  /* Dispatch desk */
  .desk{
    background:linear-gradient(180deg,var(--panel),var(--pitch-2));
    border:1px solid var(--line);border-top:3px solid var(--accent);
    padding:18px;margin-bottom:22px;
  }
  .desk-label{
    font-family:var(--f-mono);font-size:.58rem;font-weight:700;letter-spacing:.22em;text-transform:uppercase;
    color:var(--muted);margin:0 0 12px;display:flex;align-items:center;gap:9px;
  }
  .desk-label::before{content:"\25C6";color:var(--accent);font-size:.6rem}
  .run-row{display:flex;gap:10px}
  .topic-input{
    flex:1;min-width:0;font-family:var(--f-body);font-size:.95rem;color:var(--chalk);
    background:var(--pitch);border:1px solid var(--line-strong);border-radius:4px;padding:13px 16px;outline:none;
    transition:border-color .15s var(--ease),box-shadow .15s var(--ease);
  }
  .topic-input::placeholder{color:var(--faint)}
  .topic-input:hover{border-color:var(--line-strong)}
  .topic-input:focus-visible{border-color:var(--accent);box-shadow:0 0 0 3px rgba(255,106,42,.22)}
  .topic-input:disabled{opacity:.55}
  .run-btn{
    font-family:var(--f-display);font-weight:600;font-size:.94rem;letter-spacing:.16em;text-transform:uppercase;
    background:var(--accent);color:var(--accent-ink);
    border:none;border-radius:4px;padding:0 30px;cursor:pointer;white-space:nowrap;
    transition:transform .12s var(--ease),box-shadow .2s var(--ease),filter .15s var(--ease);
  }
  .run-btn:hover:not(:disabled){transform:translateY(-1px);box-shadow:0 12px 26px -12px rgba(255,106,42,.8);filter:brightness(1.05)}
  .run-btn:active:not(:disabled){transform:translateY(0)}
  .run-btn:disabled{background:var(--line-strong);color:var(--faint);cursor:not-allowed;box-shadow:none}
  .run-btn:focus-visible,.topic-input:focus-visible{outline:2px solid var(--accent-soft);outline-offset:2px}
  .progress{position:relative;height:4px;margin:14px 0 0;border-radius:2px;background:var(--line);overflow:hidden}
  .progress[hidden]{display:none}
  .progress-bar{position:absolute;inset:0;width:38%;background:linear-gradient(90deg,var(--accent),var(--live));animation:slide 1.1s var(--ease) infinite}
  @keyframes slide{0%{transform:translateX(-120%)}100%{transform:translateX(320%)}}
  .status-line{min-height:1.3em;font-family:var(--f-mono);font-size:.62rem;letter-spacing:.05em;color:var(--accent-soft);margin:12px 0 0;line-height:1.5}
  .status-line.error{color:var(--err)}

  /* Scoreboard */
  .live-panel{
    margin:0 0 26px;border:1px solid rgba(255,201,74,.22);
    background:linear-gradient(180deg,rgba(255,201,74,.05),rgba(255,201,74,.01) 70%);
    padding:16px 18px;
  }
  .live-head{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
  .live-title{display:flex;align-items:center;gap:10px;font-family:var(--f-display);font-weight:600;font-size:1rem;letter-spacing:.1em;text-transform:uppercase}
  .live-pill{font-family:var(--f-mono);font-size:.52rem;font-weight:700;letter-spacing:.18em;background:var(--live);color:#241C02;border-radius:2px;padding:3px 8px;animation:blink 1.6s steps(2) infinite}
  .live-stamp{font-family:var(--f-mono);font-size:.54rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);white-space:nowrap}
  .score-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(248px,1fr));gap:12px;margin-top:14px}
  .score-card{
    display:flex;flex-direction:column;
    background:linear-gradient(180deg,var(--panel),var(--pitch-2));
    border:1px solid var(--line);border-left:3px solid var(--accent);
    padding:13px 15px;text-decoration:none;color:inherit;
    transition:transform .18s var(--ease),border-color .18s var(--ease),box-shadow .22s var(--ease);
  }
  .score-card:hover{transform:translateY(-2px);border-color:var(--line-strong);box-shadow:0 14px 30px -20px rgba(0,0,0,.95)}
  .score-card.hidden{display:none}
  .sc-head{display:flex;justify-content:space-between;align-items:baseline;gap:8px;margin-bottom:11px}
  .sc-label{font-family:var(--f-mono);font-size:.52rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--faint);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .sc-team{display:flex;align-items:center;gap:9px;padding:5px 0}
  .sc-flag{width:25px;height:25px;border-radius:50%;flex:0 0 auto;background:var(--fc,#3A5F48);color:var(--pitch);font-family:var(--f-mono);font-weight:700;font-size:.56rem;display:flex;align-items:center;justify-content:center;letter-spacing:.02em}
  .sc-name{flex:1;min-width:0;font-size:.87rem;font-weight:500;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;transition:color .15s var(--ease)}
  .sc-team.winner .sc-name{color:var(--chalk)}
  .sc-score{font-family:var(--f-mono);font-weight:700;font-size:.88rem;color:var(--muted);white-space:nowrap;margin-left:2px}
  .sc-team.winner .sc-score{color:var(--live)}
  .sc-overs{font-weight:400;font-size:.6rem;color:var(--faint);margin-right:3px}
  .sc-result{font-size:.75rem;line-height:1.5;color:var(--muted);font-weight:500;margin:10px 0 12px;min-height:1.1em}
  .sc-result.live{color:var(--live)}
  .sc-result.upcoming{color:var(--soft)}
  .sc-foot{display:flex;justify-content:space-between;align-items:center;border-top:1px solid var(--line);padding-top:9px;margin-top:auto;font-family:var(--f-mono);font-size:.52rem;letter-spacing:.16em;text-transform:uppercase;color:var(--accent-soft)}
  .sc-foot .arrow{transition:transform .15s var(--ease)}
  .score-card:hover .sc-foot .arrow{transform:translateX(3px)}
  .live-note{margin-top:13px;font-family:var(--f-mono);font-size:.6rem;color:var(--muted);display:flex;align-items:center;gap:8px}
  .live-note .dot{width:7px;height:7px;border-radius:50%;background:var(--live);box-shadow:0 0 10px var(--live);flex:none}

  /* Edition programme */
  .digest-head{display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap;margin:0 0 14px}
  .digest-head h2{font-family:var(--f-display);font-weight:600;font-size:1.5rem;letter-spacing:.08em;text-transform:uppercase;margin:0;line-height:1}
  .digest-head h2::after{content:"";display:inline-block;width:34px;height:6px;background:var(--accent);margin-left:12px;vertical-align:4px}
  .digest-meta{font-family:var(--f-mono);font-size:.54rem;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);white-space:nowrap}
  .story-list{display:flex;flex-direction:column;border-top:2px solid var(--line-strong)}
  .story-item{
    display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 18px;
    padding:15px 6px;border-bottom:1px solid var(--line);
    transition:background .15s var(--ease);
  }
  .story-item:hover{background:rgba(242,239,227,.03)}
  .story-time{font-family:var(--f-mono);font-weight:700;font-size:.62rem;letter-spacing:.1em;text-transform:uppercase;color:var(--accent-soft);white-space:nowrap;flex:none;min-width:120px}
  .story-title{flex:1;min-width:240px;font-family:var(--f-display);font-weight:500;font-size:1.06rem;line-height:1.3;letter-spacing:.015em;color:var(--chalk);text-decoration:none}
  .story-title:hover{color:var(--accent)}
  .story-source{flex:none;font-family:var(--f-mono);font-size:.5rem;letter-spacing:.16em;text-transform:uppercase;color:var(--live)}
  .story-summary{flex-basis:100%;margin:3px 0 0;font-size:.84rem;line-height:1.6;color:var(--soft)}
  .story-link{font-family:var(--f-mono);font-size:.52rem;letter-spacing:.14em;text-transform:uppercase;color:var(--accent-soft);text-decoration:none;white-space:nowrap;display:inline-flex;align-items:center;gap:6px}
  .story-link:hover{color:var(--live)}
  .story-empty{padding:26px 2px 10px;font-style:italic;color:var(--muted)}

  /* Load-in */
  .reveal{opacity:0;transform:translateY(10px)}
  .r-topbar{animation:rise .4s var(--ease) .02s forwards}
  .r-deck{animation:rise .4s var(--ease) .10s forwards}
  .r-live{animation:rise .4s var(--ease) .16s forwards}
  .r-digest{animation:rise .4s var(--ease) .24s forwards}
  @keyframes rise{to{opacity:1;transform:translateY(0)}}

  @media(max-width:640px){
    .wrap{padding:16px 14px 52px}
    .stadium{flex-wrap:wrap}
    .brand h1{font-size:1rem}
    .board{width:100%;justify-content:space-between}
    .run-row{flex-direction:column}
    .run-btn{padding:14px 0;width:100%}
    .digest-head h2{font-size:1.2rem}
  }
  @media(prefers-reduced-motion:reduce){
    html{scroll-behavior:auto}
    .reveal,.r-topbar,.r-deck,.r-live,.r-digest{animation:none;opacity:1;transform:none}
    .progress-bar,.lcd.running::before,.status-chip.running::before,.live-pill{animation:none}
  }
</style>
</head>
<body>
<div class="wrap">

  <header class="stadium reveal r-topbar">
    <div class="brand">
      <span class="mark" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/><path d="M18 14h-8"/><path d="M15 18h-5"/><path d="M10 6h8v4h-8V6Z"/></svg>
      </span>
      <div>
        <h1>News Automation <em>Bot</em></h1>
        <small>Sports desk &middot; live edition</small>
      </div>
    </div>
    <div class="board">
      <span class="lcd clock" id="mastheadTime">--:--:--</span>
      <span class="status-chip idle" id="statusChip">Idle</span>
    </div>
  </header>

  <section class="desk reveal r-deck">
    <p class="desk-label">Run a search</p>
    <div class="run-row">
      <input class="topic-input" type="text" id="topic" placeholder="Search any Sports" spellcheck="false" autocomplete="off" onkeydown="if(event.key==='Enter'){event.preventDefault();runPipeline();}">
      <button class="run-btn" id="runBtn" onclick="runPipeline()">Search</button>
    </div>
    <div class="progress" id="runProgress" hidden><div class="progress-bar"></div></div>
    <p class="status-line" id="runStatus"></p>
  </section>

  <section class="live-panel reveal r-live" id="liveCard">
    <div class="live-head">
      <span class="live-title"><span class="live-pill">LIVE</span>Scoreboard</span>
      <span class="live-stamp" id="liveStamp"></span>
    </div>
    <div class="live-body" id="liveBody"><div class="story-empty">Connecting to the live wire \u2026</div></div>
  </section>

  <section class="digest reveal r-digest" id="digestCard">
    <div class="digest-head">
      <h2>Today's edition</h2>
      <span class="digest-meta" id="digestMeta"></span>
    </div>
    <div class="story-list" id="digest"></div>
  </section>
</div>

<script>
  var $ = function(id){ return document.getElementById(id); };
  var running = false;
  var currentTopic = '';
  function isCricketTopic(t){ return /cricket/i.test(t || ''); }

  function setChip(text, cls){
    var st = $('statusChip');
    if (st){ st.textContent = text; st.className = 'status-chip ' + cls; }
  }
  function setRunState(on){
    var mt = $('mastheadTime');
    var btn = $('runBtn');
    var pr = $('runProgress');
    if (mt) mt.classList.toggle('running', on);
    if (btn) btn.textContent = on ? 'Searching\u2026' : 'Search';
    if (pr) pr.hidden = !on;
    if (on) setChip('Running', 'running');
  }

  function esc(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  var DAYS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  var MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  function fmtStamp(d){
    if (!d || isNaN(d.getTime())) return '';
    var p = function(n){ return String(n).padStart(2,'0'); };
    return DAYS[d.getDay()] + ' ' + d.getDate() + ' ' + MONTHS[d.getMonth()] + ' ' + d.getFullYear()
      + ' \u00b7 ' + p(d.getHours()) + ':' + p(d.getMinutes()) + ':' + p(d.getSeconds());
  }
  function tickClock(){
    var el = $('mastheadTime');
    if (el) el.textContent = fmtStamp(new Date());
  }
  setInterval(tickClock, 1000);
  tickClock();
  function fmtUTC(iso){
    var d = new Date(iso);
    if (isNaN(d)) return '';
    var p = function(n){ return String(n).padStart(2,'0'); };
    return 'Updated ' + p(d.getUTCHours()) + ':' + p(d.getUTCMinutes()) + ' UTC';
  }
  function fmtDate(d){
    if (!d || isNaN(d.getTime())) return '';
    var p = function(n){ return String(n).padStart(2,'0'); };
    return DAYS[d.getDay()] + ' ' + d.getDate() + ' ' + MONTHS[d.getMonth()] + ' ' + d.getFullYear()
      + ' \u00b7 ' + p(d.getHours()) + ':' + p(d.getMinutes());
  }

  var FLAG_COLORS = ['#7F6DF0','#2DD4BF','#5B8DEF','#E5A158','#7FB58F','#C085C0','#D98B8B','#B7A2E8'];
  var PRI = { live: 0, upcoming: 1, finished: 2 };

  function codeOf(name){
    var words = name.replace(/[^A-Za-z ]/g, ' ').trim().split(/\\s+/).filter(Boolean);
    if (words.length >= 2) return words.slice(0, 2).map(function(w){ return w[0].toUpperCase(); }).join('');
    return ((words[0] || '?').slice(0, 3).toUpperCase());
  }
  function cleanTeam(s){
    var t = s.trim();
    t = t.replace(/^[A-Za-z\u00c0-\u017f]{1,6}\\s+\\d{1,3}\\/\\d{1,2}(?:\\s*\\([^)]*\\))?\\s*/, '');
    t = t.split(/\\s+[-\\u2013]\\s+/)[0].trim();
    t = t.replace(/^['"]|['"]$/g, '').trim();
    return t || s.trim();
  }
  function parseTeams(title){
    var t = title || '';
    t = t.split(',')[0];
    t = t.replace(/\\s+at\\s+.+$/i, '');
    t = t.replace(/\\([^)]*\\)/g, '');
    var parts = t.split(/\\s+(?:v\\.?|vs\\.?)\\s+/i).filter(Boolean);
    var names = [];
    if (parts.length >= 2) names = [cleanTeam(parts[0]), cleanTeam(parts[1])];
    else if (parts.length === 1){
      var dash = t.split(/\\s+[-|\\u2013]\\s+/).filter(Boolean);
      names = dash.length >= 2 ? [cleanTeam(dash[0]), cleanTeam(dash[1])] : [cleanTeam(t)];
    }
    if (!names.length) names = [title.replace(/\\s*\\|.*$/, '') || 'Match'];
    return names.map(function(n){ return { name: n, code: codeOf(n) }; });
  }
  function matchLabel(title, teams){
    var t = title || '';
    var comma = t.indexOf(',');
    if (comma > 0){
      var rest = t.slice(comma + 1).replace(/\\s+at\\s+.+$/i, '').trim();
      return rest || 'Match';
    }
    var par = t.match(/\\(([^)]*)\\)/);
    return par ? par[1].trim() : 'Match';
  }
  function parseScores(score, teams){
    var out = teams.map(function(t){ return { runs: '', wkts: '', overs: '' }; });
    if (!score) return out;
    String(score).split('|').forEach(function(p){
      var m = p.trim().match(/^([A-Za-z\u00c0-\u017f]{1,8})?\\s*:?\\s*(\\d{1,3})\\/(\\d{1,2})\\s*(?:\\(([^)]*)\\))?/);
      if (!m) return;
      var code = (m[1] || '').toUpperCase();
      var idx = -1;
      if (code){
        for (var i = 0; i < teams.length; i++){
          if (teams[i].code === code || teams[i].name.toUpperCase().indexOf(code) === 0 || code.indexOf(teams[i].code) === 0){ idx = i; break; }
        }
      }
      if (idx === -1 && teams.length === 1) idx = 0;
      if (idx >= 0){
        out[idx].runs = m[2]; out[idx].wkts = m[3];
        out[idx].overs = (m[4] || '').replace(/overs?|ov\\.?/i, '').trim();
      }
    });
    return out;
  }
  function containsName(s, name){
    var code = codeOf(name);
    if (new RegExp('\\\\b' + code + '\\\\b', 'i').test(s)) return true;
    return s.toLowerCase().indexOf(name.toLowerCase()) >= 0;
  }
  function categorize(status, scores){
    var s = (status || '').toLowerCase();
    if (/won the toss|yet to bat|scheduled|upcoming|starts? at|not started|to begin/i.test(s)) return 'upcoming';
    if (/tied|no result|abandon|drawn|draw\\b/i.test(s)) return 'finished';
    if (/won|beat|win by|defeat|winner|match result/i.test(s)) return 'finished';
    if (/live|in progress|need \\d|require|chasing|batting/i.test(s)) return 'live';
    var withRuns = scores.filter(function(x){ return x.runs; }).length;
    if (withRuns >= 2) return 'finished';
    if (withRuns === 1) return 'live';
    return 'upcoming';
  }
  function parseResult(status, teams, cat){
    var s = status || '';
    var winner = -1;
    for (var i = 0; i < teams.length; i++){
      if (containsName(s, teams[i].name) && /won|beat|win by|defeat|winner/i.test(s)){ winner = i; break; }
    }
    if (!s) return { text: cat === 'live' ? 'Match in progress' : cat === 'upcoming' ? 'Match not started' : 'Match complete', winner: winner };
    return { text: s, winner: winner };
  }
  function parseMatch(m){
    var title = m.title || '';
    var teams = parseTeams(title);
    var scores = parseScores(m.score || '', teams);
    var cat = categorize(m.status || '', scores);
    var res = parseResult(m.status || '', teams, cat);
    return {
      title: title, label: matchLabel(title, teams), teams: teams, scores: scores,
      result: res.text, cat: cat, winner: res.winner, pri: PRI[cat],
      link: m.link || ''
    };
  }
  function flagColor(code){
    var n = 0;
    for (var i = 0; i < code.length; i++) n = (n + code.charCodeAt(i)) % FLAG_COLORS.length;
    return FLAG_COLORS[n];
  }
  function cardHtml(m){
    var resultText = m.result;
    if (!resultText) resultText = m.cat === 'live' ? 'Match in progress' : 'Match not started';
    if (resultText.length > 130) resultText = resultText.slice(0, 130).replace(/\\s+\\S*$/, '') + '\u2026';
    var footText = m.cat === 'live' ? 'Live match' : 'Upcoming';
    var teams = '';
    m.teams.forEach(function(t, i){
      var sc = m.scores[i] || {};
      teams += '<div class="sc-team' + (m.winner === i ? ' winner' : '') + '">'
        + '<span class="sc-flag" style="--fc:' + flagColor(t.code) + '">' + esc(t.code) + '</span>'
        + '<span class="sc-name">' + esc(t.name) + '</span>'
        + (sc.runs
            ? '<span class="sc-score">' + sc.runs + '/' + sc.wkts + ' <span class="sc-overs">(' + esc(sc.overs || '') + ')</span></span>'
            : '')
        + '</div>';
    });
    return '<a class="score-card"'
      + (m.link ? ' href="' + esc(m.link) + '" target="_blank" rel="noopener"' : '')
      + '>'
      + '<div class="sc-head"><span class="sc-label">' + esc(m.label) + '</span></div>'
      + teams
      + '<p class="sc-result ' + m.cat + '">' + esc(resultText) + '</p>'
      + '<div class="sc-foot"><span>' + footText + '</span><span class="arrow">\u2192</span></div>'
      + '</a>';
  }
  function renderLive(d){
    var card = $('liveCard');
    if (!isCricketTopic((d && d.topic) || currentTopic)){ card.hidden = true; return; }
    var lc = (d && d.live_cricket) || {};
    var parsed = (lc.matches || []).map(parseMatch);
    var live = parsed.filter(function(m){ return m.cat === 'live'; });
    var matches = live.length ? live : parsed.filter(function(m){ return m.cat === 'upcoming'; });
    if (!matches.length){ card.hidden = true; return; }
    var ts = '';
    if (lc.generated_at){
      var g = new Date(lc.generated_at);
      if (!isNaN(g)) ts = fmtUTC(lc.generated_at);
    }
    var body = '<div class="score-grid">' + matches.map(cardHtml).join('') + '</div>';
    $('liveBody').innerHTML = body
      + (lc.source ? '<div class="live-note"><span class="dot"></span>via ' + esc(lc.source) + (ts ? ' \u00b7 ' + ts : '') + '</div>' : '');
    $('liveStamp').textContent = ts;
    card.hidden = false;
  }

  var livePoller = null;
  function startLivePolling(){
    if (!livePoller){
      livePoller = setInterval(function(){
        fetch('/api/live-cricket').then(function(r){ return r.json(); }).then(function(d){
          renderLive(d);
        }).catch(function(){ /* keep last render */ });
      }, 20000);
    }
  }

  function renderDigest(d){
    if (!d || !d.digest){
      $('digest').innerHTML = '';
      var em = $('digestMeta'); if (em) em.textContent = '';
      return;
    }
    var stories = (d.articles && d.articles.length) ? d.articles : [];
    if (!stories.length){
      var lines = d.digest.split(/\\r?\\n/);
      var cur = null;
      lines.forEach(function(raw){
        var line = raw.replace(/\\s+$/, '');
        var sM = line.match(/^-\\s+\\*\\*(.+?)\\*\\*\\s*(?:\\(([^)]*)\\))?\\s*(?:\\[link\\]\\(([^)]+)\\))?\\s*$/);
        if (sM){ cur = {headline: sM[1], source: sM[2] || '', url: sM[3] || '', summary: '', date: ''}; stories.push(cur); return; }
        if (cur && /^\\s{2}\\S/.test(line)){ cur.summary += (cur.summary ? ' ' : '') + line.trim(); }
      });
    }
    var rows = '';
    stories.forEach(function(s,i){
      var hd = s.url
        ? '<a class="story-title" href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(s.headline) + '</a>'
        : '<span class="story-title">' + esc(s.headline) + '</span>';
      var src = s.source ? '<span class="story-source">' + esc(s.source) + '</span>' : '';
      var sum = s.summary ? '<p class="story-summary">' + esc(s.summary) + '</p>' : '';
      var lnk = s.url ? '<a class="story-link" href="' + esc(s.url) + '" target="_blank" rel="noopener">Read <span>\u2192</span></a>' : '';
      var stamp = s.date ? fmtDate(new Date(s.date)) : '';
      var time = '<span class="story-time">' + esc(stamp) + '</span>';
      rows += '<article class="story-item">'
        + time
        + hd + src
        + sum + lnk
        + '</article>';
    });
    $('digest').innerHTML = stories.length
      ? rows
      : '<div class="story-empty">No stories yet. Use Search to file the first edition.</div>';
    var meta = $('digestMeta');
    if (meta){
      var bits = [];
      if (d.article_count || stories.length) bits.push((d.article_count || stories.length) + ' stories');
      if (d.generated_at) bits.push(fmtUTC(d.generated_at));
      meta.textContent = bits.join(' \u00b7 ');
    }
  }

  function distText(d){
    if (!d || !d.distribution) return '';
    var out = [];
    ['live_cricket','slack','google_sheets'].forEach(function(k){
      var v = d.distribution[k];
      if (!v || /not configured/i.test(v)) return;
      out.push(v);
    });
    return out.join(' \u00b7 ');
  }

  async function runPipeline(){
    var topic = $('topic').value.trim() || 'sports and game cricket';
    $('runBtn').disabled = true; $('topic').disabled = true;
    running = true;
    setRunState(true);
    $('runStatus').textContent = 'Fetching ' + topic + ' \u2026';
    try {
      var res = await fetch('/api/run', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ topic: topic })
      });
      if (!res.ok && res.status !== 409) $('runStatus').textContent = 'Run rejected \u2014 ' + (await res.text());
    } catch (e) {
      $('runStatus').textContent = 'Could not reach the pipeline \u2014 ' + e;
    }
    pollStatus();
  }

  async function pollStatus(){
    try {
      var res = await fetch('/api/status');
      var data = await res.json();
      if (data.running){
        running = true;
        setRunState(true);
        setTimeout(pollStatus, 3000);
      } else {
        running = false;
        $('runBtn').disabled = false; $('topic').disabled = false;
        var d = await (await fetch('/api/digest')).json();
        if (data.last_error){
          $('runStatus').textContent = data.last_error;
          $('runStatus').className = 'status-line error';
          setChip('Error', 'error');
          setRunState(false);
          setTimeout(function(){ setChip('Idle', 'idle'); }, 6000);
        } else {
          currentTopic = d.topic || currentTopic;
          renderDigest(d);
          renderLive(d);
          $('runStatus').textContent = '';
          $('runStatus').className = 'status-line';
          setChip('Done', 'done');
          setRunState(false);
          setTimeout(function(){ setChip('Idle', 'idle'); }, 4000);
        }
      }
    } catch (e) {
      setTimeout(pollStatus, 5000);
    }
  }

  (async function init(){
    var res = await fetch('/api/status');
    var data = await res.json();
    var d = await (await fetch('/api/digest')).json();
    currentTopic = d.topic || '';
    if (data.running){ running = true; setRunState(true); startLivePolling(); pollStatus(); return; }
    renderDigest(d);
    renderLive(d);
    startLivePolling();
  })();
</script>
</body>
</html>
"""
