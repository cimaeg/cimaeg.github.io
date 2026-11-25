/* شاشة زمان — الصفحات الإضافية: خمّن الفيلم، حدث في مثل هذا اليوم، اسحب تذكرة، الصنّاع، شبكة النجوم، الأرقام */
{
const Z = window.SZ;
const { ERAS, STYLE, FONT, esc, ar, norm, eraOf, poster, mpo, cnt, score, escore, byRating, md, pname, showPage } = Z;
const $ = id => document.getElementById(id);
const FILMS = () => Z.FILMS;
let WD = { people: {}, films: {} };
const MONTHS = ['يناير','فبراير','مارس','أبريل','مايو','يونيو','يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر'];
const fmtDate = d => { if (!d) return ''; const [y, m, dd] = d.split('-'); return m ? `${ar(+dd)} ${MONTHS[+m - 1]} ${ar(y)}` : ar(y); };
const plink = n => `<a class="pl" href="#p-${encodeURIComponent(n)}">${esc(n)}</a>`;
const reduce = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
const store = { get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} } };

/* ——— الصنّاع: فهرس من بيانات الأفلام ——— */
let PEOPLE = null;
function people() {
  if (PEOPLE) return PEOPLE;
  const m = new Map();
  const add = (n, f, role) => { n = pname(n); if (!n) return; if (!m.has(n)) m.set(n, { name: n, films: [], roles: new Set() }); const p = m.get(n); if (!p.films.includes(f)) p.films.push(f); p.roles.add(role); };
  for (const f of FILMS()) { (f.cast || []).forEach(c => add(c, f, 'ممثل')); add(f.director, f, 'مخرج'); }
  for (const p of m.values()) p.films.sort((a, b) => a.year - b.year);
  PEOPLE = m; return m;
}
const fem = n => !!((WD.people || {})[n] || {}).f;
const roleText = p => [...p.roles].map(r => fem(p.name) ? r + 'ة' : r).join(' و');
const initials = n => esc(n.replace(/^(ال)/, '').trim()[0] || n[0]);
let PX = {};
const photo = n => { const x = PX[n]; return x && /^people\/[\w.-]+\.webp$/.test(x.photo || '') ? { ...x, photo: '/img/' + x.photo } : null; };
function avatar(p, big) {
  const ph = photo(p.name);
  if (ph) return `<span class="av2 ph${big ? ' big' : ''}"><img src="${ph.photo}" alt="${big ? esc(p.name) : ''}" loading="lazy" style="object-position:${esc(ph.focus || '50% 20%')}"></span>`;
  const e = eraOf(p.films[0].year).id, [bg, ink] = STYLE[e];
  return `<span class="av2${big ? ' big' : ''}" style="background:${bg};color:${ink};font-family:${FONT[e]}">${initials(p.name)}</span>`;
}

/* ——— حدث في مثل هذا اليوم ——— */
function events() {
  const out = [];
  for (const [name, d] of Object.entries(WD.people || {})) {
    if (!people().has(name)) continue;
    if (d.born && d.born.length === 10) out.push({ md: d.born.slice(5), y: +d.born.slice(0, 4), kind: 'born', name });
    if (d.died && d.died.length === 10) out.push({ md: d.died.slice(5), y: +d.died.slice(0, 4), kind: 'died', name });
  }
  for (const f of FILMS()) {
    const r = (WD.films || {})[f.id];
    if (r && r.released && r.released.length === 10 && +r.released.slice(0, 4) === f.year) out.push({ md: r.released.slice(5), y: f.year, kind: 'film', f });
  }
  return out;
}
function onThisDay() {
  const ev = events(); if (!ev.length) return null;
  const now = new Date();
  for (let k = 0; k < 366; k++) {
    const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() + k);
    const key = String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    const hits = ev.filter(x => x.md === key).sort((a, b) => a.y - b.y);
    if (hits.length) return { k, date: d, hits };
  }
  return null;
}
function eventLine(x) {
  if (x.kind === 'film') return `عُرض <a href="#film-${esc(x.f.id)}">«${esc(x.f.title)}»</a> لأول مرة عام ${ar(x.y)}`;
  return `ذكرى ${x.kind === 'born' ? 'ميلاد' : 'رحيل'} ${plink(x.name)} (${ar(x.y)})`;
}

/* ——— الردهة في الصفحة الرئيسية ——— */
let lastTicket = null;
function lobby() {
  const el = $('lobby'); if (!el) return;
  const t = onThisDay();
  const dayTxt = !t ? '' : t.k === 0 ? 'اليوم' : t.k === 1 ? 'غدًا' : `بعد ${ar(t.k)} ${t.k <= 10 ? 'أيام' : 'يومًا'}، ${ar(t.date.getDate())} ${MONTHS[t.date.getMonth()]}`;
  const g = gameToday(), gs = store.get('g-' + g.day, null);
  const gTxt = gs && gs.done ? (gs.won ? `حللته في ${ar(gs.guesses.length)} ${gs.guesses.length > 2 ? 'محاولات' : 'محاولة'}. عُد غدًا للغز جديد.` : 'فاتك لغز اليوم. عُد غدًا.') : 'ست تلميحات تتكشّف واحدة بعد الأخرى. كم تحتاج لتعرف الفيلم؟';
  el.innerHTML = `<section class="lobby" aria-label="ردهة السينما">
   <a class="lob lob-game" href="#game"><span class="lk">لغز رقم ${ar(g.no)}</span><b>خمّن فيلم اليوم</b><p>${gTxt}</p><span class="lgo">${gs && gs.done ? 'شاهد النتيجة' : 'ابدأ اللعب'} ←</span></a>
   <div class="lob lob-day"><span class="lk">حدث في مثل هذا اليوم</span>${t ? `<b>${dayTxt === 'اليوم' ? 'اليوم' : esc(dayTxt)}</b><ul>${t.hits.slice(0, 3).map(x => `<li>${eventLine(x)}</li>`).join('')}</ul>` : '<b>قريبًا</b><p>تُجمع التواريخ من ويكي بيانات كل أسبوع.</p>'}</div>
   <div class="lob lob-tix"><span class="lk">شبّاك التذاكر</span><b>لا تعرف ماذا تشاهد؟</b><div class="slot" id="slot"><div class="tk" id="tk" hidden></div></div><button class="btn pull" type="button" id="pull">اسحب تذكرة</button></div>
  </section>`;
  $('pull').addEventListener('click', pullTicket);
}
function pullTicket() {
  const list = FILMS().filter(f => f !== lastTicket), f = list[Math.floor(Math.random() * list.length)]; lastTicket = f;
  const tk = $('tk'), e = eraOf(f.year).id, [bg, ink] = STYLE[e];
  tk.hidden = false; tk.classList.remove('out'); void tk.offsetWidth;
  tk.style.setProperty('--tbg', bg); tk.style.setProperty('--tink', ink);
  tk.innerHTML = `<a href="#film-${esc(f.id)}"><span class="tno">تذكرة رقم ${ar(String(Math.floor(Math.random() * 9000) + 1000))}</span><b style="font-family:${FONT[e]}">${esc(f.title)}</b><span>${ar(f.year)} · إخراج: ${esc(f.director)}</span><em>ادخل القاعة ←</em></a>`;
  if (!reduce()) tk.classList.add('out');
  $('pull').textContent = 'اسحب تذكرة أخرى';
}

/* ——— خمّن الفيلم ——— */
const EPOCH = Date.UTC(2026, 10, 25);
function seeded(n, seed) { const a = [...Array(n).keys()]; let s = seed; for (let i = n - 1; i > 0; i--) { s = (s * 1103515245 + 12345) % 2147483648; const j = s % (i + 1); [a[i], a[j]] = [a[j], a[i]]; } return a; }
function gameToday() {
  const now = new Date(), day = Math.floor((Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()) - EPOCH) / 864e5);
  const list = [...FILMS()].sort((a, b) => a.id < b.id ? -1 : 1), n = list.length;
  const cycle = Math.floor(day / n), order = seeded(n, 7919 + cycle * 31);
  return { day, no: day + 1, f: list[order[((day % n) + n) % n]] };
}
function clues(f) {
  if (Array.isArray(f.clues) && f.clues.length >= 4) return f.clues.slice(0, 6);
  const e = eraOf(f.year), lead = (f.cast || []).map(pname).filter(c => c !== pname(f.director));
  const words = f.title.split(/\s+/).length;
  return [
    `من أفلام ${e.name}، ونوعه ${(f.genre || []).join(' و') || 'غير مصنّف'}`,
    `عُرض عام ${ar(f.year)}`,
    f.based_on ? `مأخوذ عن ${f.based_on}` : f.writer ? `التأليف: ${f.writer}` : `تقييمه على IMDb ${score(f) ? score(f).toFixed(1) : 'غير متاح'}`,
    `إخراج: ${pname(f.director)}`,
    lead.length ? `من أبطاله: ${lead[lead.length > 1 ? 1 : 0]}` : `تقييمه على السينما.كوم ${escore(f) ? escore(f).toFixed(1) : 'غير متاح'}`,
    `يبدأ عنوانه بحرف «${f.title.replace(/^ال/, '')[0]}»، ويتكوّن من ${words === 1 ? 'كلمة واحدة' : words === 2 ? 'كلمتين' : ar(words) + ' كلمات'}`
  ];
}
let G = null;
function renderGame(practice) {
  const el = showPage('e50', 'خمّن الفيلم');
  const t = gameToday();
  const f = practice ? practice : t.f, key = practice ? null : 'g-' + t.day;
  const st = key ? store.get(key, { guesses: [], done: false, won: false }) : { guesses: [], done: false, won: false };
  G = { f, key, st, practice: !!practice, no: t.no, cl: clues(f) };
  el.innerHTML = `<div class="gwrap">
   <a class="back" href="#top">→ العودة إلى آلة الزمن</a>
   <div class="ghead"><span class="lk">${practice ? 'جولة تدريب' : 'لغز رقم ' + ar(t.no)}</span><h1>خمّن الفيلم</h1><p>كل محاولة خاطئة تكشف تلميحًا جديدًا. أمامك ست محاولات.</p></div>
   <ol class="strip6" id="clues"></ol>
   <div class="gin" id="gin"><div class="gbox"><input id="gq" type="text" autocomplete="off" placeholder="اكتب اسم الفيلم…" aria-label="اسم الفيلم" aria-autocomplete="list" aria-controls="gsug"><button type="button" class="btn" id="gskip">تخطَّ</button></div><ul class="gsug" id="gsug" role="listbox" hidden></ul></div>
   <ol class="gtries" id="gtries"></ol>
   <div id="gend"></div>
  </div>`;
  paintGame();
  const q = $('gq'), sug = $('gsug'); let act = 0, opts = [];
  const show = () => {
    const qn = norm(q.value); act = 0;
    opts = qn ? FILMS().filter(x => norm(x.title).includes(qn) && !G.st.guesses.includes(x.id)).slice(0, 6) : [];
    sug.hidden = !opts.length;
    sug.innerHTML = opts.map((x, i) => `<li role="option" id="gs${i}" data-id="${esc(x.id)}" class="${i === act ? 'on' : ''}"><b>${esc(x.title)}</b><small>${ar(x.year)}</small></li>`).join('');
  };
  q.addEventListener('input', show);
  q.addEventListener('keydown', e => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); if (!opts.length) return; act = (act + (e.key === 'ArrowDown' ? 1 : -1) + opts.length) % opts.length; [...sug.children].forEach((li, i) => li.classList.toggle('on', i === act)); }
    else if (e.key === 'Enter' && opts[act]) { e.preventDefault(); guess(opts[act].id); }
  });
  sug.addEventListener('click', e => { const li = e.target.closest('li'); if (li) guess(li.dataset.id); });
  $('gskip').addEventListener('click', () => guess(null));
  if (!G.st.done) q.focus({ preventScroll: true });
}
function guess(id) {
  if (G.st.done) return;
  G.st.guesses.push(id);
  if (id === G.f.id) { G.st.done = true; G.st.won = true; }
  else if (G.st.guesses.length >= 6) { G.st.done = true; }
  if (G.key) { store.set(G.key, G.st); if (G.st.done) saveStats(G.st); }
  const q = $('gq'); q.value = ''; $('gsug').hidden = true;
  paintGame(true);
  if (!G.st.done) q.focus({ preventScroll: true });
}
function saveStats(st) {
  const s = store.get('gstats', { played: 0, won: 0, streak: 0, best: 0, dist: [0, 0, 0, 0, 0, 0], last: null });
  if (s.last === G.key) return;
  s.played++; if (st.won) { s.won++; s.dist[st.guesses.length - 1]++; s.streak = (s.last === 'g-' + (+G.key.slice(2) - 1) ? s.streak : 0) + 1; s.best = Math.max(s.best, s.streak); } else s.streak = 0;
  s.last = G.key; store.set('gstats', s);
}
function paintGame(anim) {
  const { st, cl, f } = G, shown = st.done ? 6 : st.guesses.length + 1;
  $('clues').innerHTML = cl.map((c, i) => i < shown ? `<li class="open${anim && i === shown - 1 && !st.done ? ' new' : ''}"><span class="cn">${ar(i + 1)}</span><p>${esc(c)}</p></li>` : `<li class="shut"><span class="cn">${ar(i + 1)}</span><p>تلميح مغلق</p></li>`).join('');
  $('gtries').innerHTML = st.guesses.map((id, i) => { const x = FILMS().find(y => y.id === id); return `<li class="${id === f.id ? 'ok' : 'no'}"><span>${ar(i + 1)}</span>${x ? esc(x.title) + ` <small>${ar(x.year)}</small>` : '<em>تخطّي</em>'}</li>`; }).join('');
  $('gin').hidden = st.done;
  const end = $('gend');
  if (!st.done) { end.innerHTML = ''; return; }
  const sq = st.guesses.map(id => id === f.id ? '🟩' : '🟥').join('') + '⬜'.repeat(6 - st.guesses.length);
  const share = `شاشة زمان · ${G.practice ? 'جولة تدريب' : 'لغز ' + G.no}\n${sq}\ncimaeg.github.io/#game`;
  const s = store.get('gstats', null);
  end.innerHTML = `<div class="gres ${st.won ? 'won' : 'lost'}">
    <div class="gpo">${poster(f)}</div>
    <div><span class="lk">${st.won ? 'أحسنت!' : 'فاتك هذه المرة'}</span><h2>${esc(f.title)}</h2><p>${ar(f.year)} · إخراج: ${esc(f.director)}</p>
    <div class="sq" aria-label="${st.won ? 'عرفته في المحاولة ' + (st.guesses.length) : 'لم تعرفه'}">${sq}</div>
    <div class="gact"><a class="btn" href="#film-${esc(f.id)}">صفحة الفيلم</a><button type="button" class="btn ghost" id="gshare">انسخ النتيجة</button><button type="button" class="btn ghost" id="gprac">جولة تدريب</button></div>
    ${!G.practice && s ? `<dl class="gst"><div><dt>لعبت</dt><dd>${ar(s.played)}</dd></div><div><dt>فزت</dt><dd>${ar(s.played ? Math.round(s.won / s.played * 100) : 0)}٪</dd></div><div><dt>سلسلة</dt><dd>${ar(s.streak)}</dd></div><div><dt>أفضل سلسلة</dt><dd>${ar(s.best)}</dd></div></dl>` : ''}
    ${!G.practice ? '<p class="note">لغز جديد كل يوم عند منتصف الليل.</p>' : ''}</div></div>`;
  $('gshare').addEventListener('click', async e => { try { await navigator.clipboard.writeText(share); e.target.textContent = 'نُسخت ✓'; } catch { e.target.textContent = 'تعذّر النسخ'; } });
  $('gprac').addEventListener('click', () => { const pool = FILMS().filter(x => x !== f); renderGame(pool[Math.floor(Math.random() * pool.length)]); });
}

/* ——— فهرس الصنّاع ——— */
let pq = '';
function renderPeople() {
  const el = showPage('e60', 'الصنّاع');
  el.innerHTML = `<div class="pwrap"><a class="back" href="#top">→ العودة إلى آلة الزمن</a>
   <div class="ghead"><h1>الصنّاع</h1><p>${(n => n <= 10 ? ar(n) + ' أسماء' : ar(n) + ' اسمًا')(people().size)} من ممثلين ومخرجين في الأرشيف.</p></div>
   <div class="pfind"><input id="pq" type="text" autocomplete="off" placeholder="ابحث عن اسم…" aria-label="ابحث عن اسم" value="${esc(pq)}"></div>
   <div id="plist"></div></div>`;
  const draw = () => {
    const qn = norm(pq), all = [...people().values()].filter(p => !qn || norm(p.name).includes(qn)).sort((a, b) => b.films.length - a.films.length || a.name.localeCompare(b.name, 'ar'));
    const grp = (t, arr) => arr.length ? `<h2 class="pg">${t} <small>${ar(arr.length)}</small></h2><div class="pgrid">${arr.map(p => `<a class="pc" href="#p-${encodeURIComponent(p.name)}">${avatar(p)}<span><b>${esc(p.name)}</b><small>${cnt(p.films.length)} · ${ar(p.films[0].year)}${p.films.length > 1 ? '–' + ar(p.films[p.films.length - 1].year) : ''}</small></span></a>`).join('')}</div>` : '';
    $('plist').innerHTML = grp('مخرجون', all.filter(p => p.roles.has('مخرج'))) + grp('ممثلون', all.filter(p => !p.roles.has('مخرج'))) || '<p class="lnone">لا يوجد اسم يطابق البحث.</p>';
  };
  draw();
  $('pq').addEventListener('input', e => { pq = e.target.value; draw(); });
}

/* ——— صفحة الشخص ——— */
const art = {};
async function personArticle(name) {
  if (name in art) return art[name];
  try { const r = await fetch(`people/${encodeURIComponent(name.replace(/\s+/g, '-'))}.md`, { cache: 'no-cache' }); art[name] = r.ok ? await r.text() : null; } catch { art[name] = null; }
  return art[name];
}
async function renderPerson(name) {
  const p = people().get(name);
  if (!p) { const el = showPage('e60', name); el.innerHTML = `<div class="pwrap"><a class="back" href="#people">→ كل الصنّاع</a><p class="lnone">لا يوجد في الأرشيف اسم «${esc(name)}».</p></div>`; return; }
  const era = eraOf(p.films[Math.floor(p.films.length / 2)].year).id;
  const el = showPage(era, p.name);
  const w = (WD.people || {})[p.name] || {}, f = !!w.f;
  const scored = p.films.filter(score), avg = scored.length ? scored.reduce((s, f) => s + score(f), 0) / scored.length : 0;
  const co = new Map();
  for (const f of p.films) for (const n of [...(f.cast || []), f.director].map(pname)) if (n && n !== p.name) co.set(n, (co.get(n) || 0) + 1);
  const coTop = [...co.entries()].filter(([, c]) => c > 1).sort((a, b) => b[1] - a[1]).slice(0, 8);
  const coOne = coTop.length ? [] : [...co.keys()].slice(0, 8);
  const age = (w.born && w.born.length === 10) ? (() => { const b = new Date(w.born), d = w.died && w.died.length === 10 ? new Date(w.died) : new Date(); let a = d.getFullYear() - b.getFullYear(); if (d < new Date(d.getFullYear(), b.getMonth(), b.getDate())) a--; return a; })() : null;
  const roleIn = f => pname(f.director) === p.name ? ((f.cast || []).map(pname).includes(p.name) ? 'إخراج وتمثيل' : 'إخراج') : 'تمثيل';
  el.innerHTML = `<div class="pwrap"><a class="back" href="#people">→ كل الصنّاع</a>
   <div class="phead">${avatar(p, true)}<div><span class="lk">${esc(roleText(p))}</span><h1>${esc(p.name)}</h1>
    <p class="life">${w.born ? `${f ? 'وُلدت' : 'وُلد'} ${w.born.includes('-') ? 'في' : 'عام'} ${fmtDate(w.born)}` : ''}${w.died ? `، ${f ? 'ورحلت' : 'ورحل'} ${w.died.includes('-') ? 'في' : 'عام'} ${fmtDate(w.died)}` : ''}${age !== null ? ` <small>(${w.died ? 'عن' : 'العمر'} ${ar(age)} عامًا)</small>` : ''}</p>
    </div></div>
   <dl class="pnums"><div><dt>في الأرشيف</dt><dd>${cnt(p.films.length)}</dd></div><div><dt>الفترة</dt><dd>${ar(p.films[0].year)}${p.films.length > 1 ? '–' + ar(p.films[p.films.length - 1].year) : ''}</dd></div>${avg ? `<div><dt>متوسط IMDb</dt><dd>${avg.toFixed(1)}</dd></div>` : ''}</dl>
   <div class="pcols"><div>
    <h2 class="pg">${f ? 'أفلامها' : 'أفلامه'} في الأرشيف</h2>
    <ol class="tline">${p.films.map(f => `<li><span class="ty">${ar(f.year)}</span><a href="#film-${esc(f.id)}">${mpo(f, eraOf(f.year).id)}<span><b>${esc(f.title)}</b><small>${roleIn(f)}${roleIn(f) === 'تمثيل' ? ' · إخراج: ' + esc(pname(f.director)) : ''}${score(f) ? ' · ★ ' + score(f).toFixed(1) : ''}</small></span></a></li>`).join('')}</ol>
    <div class="prose" id="pprose"></div>
   </div><aside class="side">
    ${coTop.length || coOne.length ? `<div class="box"><h4>${coTop.length ? (f ? 'أكثر من عملت معهم' : 'أكثر من عمل معهم') : (f ? 'عملت معهم' : 'عمل معهم')}</h4><ul class="co">${(coTop.length ? coTop : coOne.map(n => [n, 1])).map(([n, c]) => `<li><a href="#p-${encodeURIComponent(n)}">${esc(n)}</a>${c > 1 ? `<small>${cnt(c)}</small>` : ''}</li>`).join('')}</ul></div>` : ''}
    <div class="box"><h4>شبكة النجوم</h4><p class="note">كيف يتصل ${esc(p.name)} بغيره من النجوم؟</p><a class="btn" href="#network">افتح الشبكة</a></div>
   </aside></div></div>`;
  netFrom = p.name;
  const txt = await personArticle(p.name);
  if (txt && location.hash === '#p-' + encodeURIComponent(p.name) || txt && decodeURIComponent(location.hash.slice(3)) === p.name) $('pprose').innerHTML = md(txt);
}

/* ——— شبكة النجوم ——— */
let netFrom = 'فاتن حمامة', netTo = 'أحمد زكي';
function graph() {
  const adj = new Map(), link = (a, b) => { if (!adj.has(a)) adj.set(a, new Set()); adj.get(a).add(b); };
  for (const p of people().values()) for (const f of p.films) { link('p:' + p.name, 'f:' + f.id); link('f:' + f.id, 'p:' + p.name); }
  return adj;
}
function path(a, b) {
  const adj = graph(), s = 'p:' + a, t = 'p:' + b; if (!adj.has(s) || !adj.has(t)) return null;
  const prev = new Map([[s, null]]), q = [s];
  while (q.length) { const x = q.shift(); if (x === t) break; for (const y of adj.get(x) || []) if (!prev.has(y)) { prev.set(y, x); q.push(y); } }
  if (!prev.has(t)) return [];
  const out = []; for (let x = t; x; x = prev.get(x)) out.unshift(x); return out;
}
function pickerHTML(id, val, label) {
  return `<div class="pick"><label for="${id}">${label}</label><input id="${id}" type="text" autocomplete="off" value="${esc(val)}" placeholder="اسم ممثل أو مخرج" aria-controls="${id}-s"><ul class="gsug" id="${id}-s" hidden></ul></div>`;
}
function renderNetwork() {
  if (netTo === netFrom) { const alt = ['فاتن حمامة', 'أحمد زكي', 'يوسف شاهين'].find(n => n !== netFrom && people().has(n)); netTo = alt; }
  const el = showPage('e90', 'شبكة النجوم');
  el.innerHTML = `<div class="pwrap"><a class="back" href="#top">→ العودة إلى آلة الزمن</a>
   <div class="ghead"><h1>شبكة النجوم</h1><p>اختر نجمين، وستعرف كيف يلتقيان عبر الأفلام. كل خطوة فيلم جمع اثنين منهم.</p></div>
   <div class="pickers">${pickerHTML('na', netFrom, 'من')}<button type="button" class="swap" id="nswap" aria-label="بدّل الاسمين">⇄</button>${pickerHTML('nb', netTo, 'إلى')}</div>
   <div id="nres"></div>
   <h2 class="pg">دائرة <span id="egoName"></span></h2><p class="note">الأفلام في الحلقة الداخلية، وشركاء العمل فيها في الحلقة الخارجية. اضغط أي اسم لتنقل الدائرة إليه.</p>
   <div class="ego" id="ego"></div></div>`;
  for (const id of ['na', 'nb']) wirePicker(id);
  $('nswap').addEventListener('click', () => { [netFrom, netTo] = [netTo, netFrom]; $('na').value = netFrom; $('nb').value = netTo; drawNet(); });
  drawNet();
}
function wirePicker(id) {
  const inp = $(id), sug = $(id + '-s'); let opts = [], act = 0;
  const set = n => { inp.value = n; sug.hidden = true; if (id === 'na') netFrom = n; else netTo = n; drawNet(); };
  inp.addEventListener('input', () => { const qn = norm(inp.value); act = 0; opts = qn ? [...people().values()].filter(p => norm(p.name).includes(qn)).sort((a, b) => b.films.length - a.films.length).slice(0, 6) : []; sug.hidden = !opts.length; sug.innerHTML = opts.map((p, i) => `<li data-n="${esc(p.name)}" class="${i === act ? 'on' : ''}"><b>${esc(p.name)}</b><small>${cnt(p.films.length)}</small></li>`).join(''); });
  inp.addEventListener('keydown', e => { if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); if (!opts.length) return; act = (act + (e.key === 'ArrowDown' ? 1 : -1) + opts.length) % opts.length; [...sug.children].forEach((li, i) => li.classList.toggle('on', i === act)); } else if (e.key === 'Enter' && opts[act]) { e.preventDefault(); set(opts[act].name); } });
  sug.addEventListener('click', e => { const li = e.target.closest('li'); if (li) set(li.dataset.n); });
  inp.addEventListener('blur', () => setTimeout(() => sug.hidden = true, 150));
}
function drawNet() {
  const res = $('nres'), P = people();
  if (!P.has(netFrom) || !P.has(netTo)) { res.innerHTML = '<p class="lnone">اختر اسمين من القائمة المقترحة.</p>'; }
  else if (netFrom === netTo) { res.innerHTML = '<p class="lnone">اختر اسمين مختلفين.</p>'; }
  else {
    const pth = path(netFrom, netTo);
    if (!pth || !pth.length) res.innerHTML = `<p class="lnone">لا يوجد طريق بين ${esc(netFrom)} و${esc(netTo)} في الأرشيف حتى الآن. كلما زادت الأفلام زادت الطرق.</p>`;
    else {
      const steps = (pth.length - 1) / 2;
      res.innerHTML = `<div class="chain"><p class="deg">بينهما <b>${steps === 1 ? 'فيلم واحد' : steps === 2 ? 'فيلمان' : ar(steps) + ' أفلام'}</b></p><ol>${pth.map(n => {
        if (n.startsWith('p:')) { const p = P.get(n.slice(2)); return `<li class="cp"><a href="#p-${encodeURIComponent(p.name)}">${avatar(p)}<b>${esc(p.name)}</b></a></li>`; }
        const f = FILMS().find(x => x.id === n.slice(2)); return `<li class="cf"><a href="#film-${esc(f.id)}">${mpo(f, eraOf(f.year).id)}<span><b>${esc(f.title)}</b><small>${ar(f.year)}</small></span></a></li>`;
      }).join('')}</ol></div>`;
    }
  }
  drawEgo(P.has(netFrom) ? netFrom : 'فاتن حمامة');
}
function drawEgo(name) {
  const P = people(), p = P.get(name), box = $('ego'); if (!p || !box) return;
  $('egoName').textContent = p.name;
  const films = p.films, W = 640, H = 640, cx = W / 2, cy = H / 2, R1 = 150, R2 = 270;
  const fa = films.map((f, i) => -Math.PI / 2 + i * 2 * Math.PI / films.length);
  const co = new Map();
  films.forEach((f, i) => { for (const n of [...(f.cast || []), f.director].map(pname)) if (n && n !== p.name) { if (!co.has(n)) co.set(n, []); co.get(n).push(i); } });
  let cos = [...co.entries()].map(([n, idx]) => ({ n, idx, a: Math.atan2(idx.reduce((s, i) => s + Math.sin(fa[i]), 0), idx.reduce((s, i) => s + Math.cos(fa[i]), 0)) }));
  cos.sort((x, y) => x.a - y.a);
  const maxN = 28; if (cos.length > maxN) cos = cos.sort((x, y) => y.idx.length - x.idx.length).slice(0, maxN).sort((x, y) => x.a - y.a);
  // spread outer names evenly while keeping their order
  cos.forEach((c, i) => { c.b = cos.length > 1 ? c.a * 0 + (-Math.PI + (i + .5) * 2 * Math.PI / cos.length) : c.a; });
  const rot = cos.length ? cos.reduce((s, c) => s + Math.atan2(Math.sin(c.a - c.b), Math.cos(c.a - c.b)), 0) / cos.length : 0;
  cos.forEach(c => c.b += rot);
  const e = eraOf(films[0].year).id;
  const pt = (r, a) => [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  let lines = '', nodes = '';
  cos.forEach(c => { const [x2, y2] = pt(R2 - 14, c.b); c.idx.forEach(i => { const [x1, y1] = pt(R1, fa[i]); lines += `<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" class="el"/>`; }); });
  films.forEach((f, i) => { const [x, y] = pt(R1, fa[i]); lines += `<line x1="${cx}" y1="${cy}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}" class="ec"/>`; });
  films.forEach((f, i) => { const [x, y] = pt(R1, fa[i]), [bg, ink] = STYLE[eraOf(f.year).id]; nodes += `<a href="#film-${esc(f.id)}" class="nf"><rect x="${(x - 46).toFixed(1)}" y="${(y - 17).toFixed(1)}" width="92" height="34" rx="5" fill="${bg}"/><text x="${x.toFixed(1)}" y="${(y + 5).toFixed(1)}" fill="${ink}">${esc(f.title.length > 12 ? f.title.slice(0, 11) + '…' : f.title)}</text></a>`; });
  cos.forEach(c => { const [x, y] = pt(R2, c.b), cosA = Math.cos(c.b), anchor = Math.abs(cosA) < .25 ? 'middle' : cosA > 0 ? 'start' : 'end'; nodes += `<a href="#network" class="np" data-n="${esc(c.n)}"><circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${5 + Math.min(4, c.idx.length) * 1.5}"/><text x="${(x + (anchor === 'start' ? 10 : anchor === 'end' ? -10 : 0)).toFixed(1)}" y="${(y + (anchor === 'middle' ? (Math.sin(c.b) > 0 ? 20 : -12) : 5)).toFixed(1)}" text-anchor="${anchor}">${esc(c.n)}</text></a>`; });
  const [bg, ink] = STYLE[e];
  box.innerHTML = `<svg direction="ltr" viewBox="-150 -10 ${W + 300} ${H + 20}" role="img" aria-label="دائرة ${esc(p.name)}: ${cnt(films.length)} و${ar(cos.length)} شريكًا">${lines}${nodes}${photo(p.name) ? `<defs><clipPath id="egoc"><circle cx="${cx}" cy="${cy}" r="62"/></clipPath></defs><circle cx="${cx}" cy="${cy}" r="66" fill="${bg}"/><image href="${photo(p.name).photo}" x="${cx - 62}" y="${cy - 62}" width="124" height="124" preserveAspectRatio="xMidYMin slice" clip-path="url(#egoc)"/><text x="${cx}" y="${cy + 92}" class="nc">${esc(p.name)}</text>` : `<circle cx="${cx}" cy="${cy}" r="62" fill="${bg}"/><text x="${cx}" y="${cy + 7}" class="nc" fill="${ink}" style="font-family:${FONT[e]}">${esc(p.name.length > 12 ? p.name.split(' ')[0] : p.name)}</text>`}</svg>`;
  box.querySelectorAll('.np').forEach(a => a.addEventListener('click', ev => { ev.preventDefault(); netFrom = a.dataset.n; $('na').value = netFrom; drawNet(); }));
}

/* ——— أرقام الزمن الجميل ——— */
function bars(rows, fmt, max, unit) {
  const m = max || Math.max(...rows.map(r => r.v), 1);
  return `<div class="bars">${rows.map(r => `<div class="br" title="${esc(r.k)}: ${esc(fmt(r.v))}${unit || ''}"><span class="bk">${r.href ? `<a href="${r.href}">${esc(r.k)}</a>` : esc(r.k)}</span><span class="bt"><span class="bf" style="width:${(r.v / m * 100).toFixed(1)}%"></span></span><span class="bv">${fmt(r.v)}</span></div>`).join('')}</div>`;
}
function renderStats() {
  const el = showPage('e40', 'أرقام الزمن الجميل'), F = FILMS(), P = people();
  const avg = a => a.length ? a.reduce((s, x) => s + x, 0) / a.length : 0;
  const perEra = ERAS.map(e => ({ e, fs: F.filter(f => eraOf(f.year) === e) }));
  const dirs = [...P.values()].filter(p => p.roles.has('مخرج')).map(p => ({ k: p.name, v: p.films.filter(f => pname(f.director) === p.name).length, href: '#p-' + encodeURIComponent(p.name) })).sort((a, b) => b.v - a.v).slice(0, 8);
  const acts = [...P.values()].map(p => ({ k: p.name, v: p.films.filter(f => (f.cast || []).map(pname).includes(p.name)).length, href: '#p-' + encodeURIComponent(p.name) })).filter(r => r.v).sort((a, b) => b.v - a.v).slice(0, 8);
  const gm = new Map(); F.forEach(f => (f.genre || []).forEach(g => gm.set(g, (gm.get(g) || 0) + 1)));
  const gen = [...gm.entries()].map(([k, v]) => ({ k, v })).sort((a, b) => b.v - a.v);
  const both = F.filter(f => score(f) && escore(f));
  const gap = both.map(f => ({ f, d: escore(f) - score(f) })).sort((a, b) => Math.abs(b.d) - Math.abs(a.d)).slice(0, 8);
  const top = [...F].sort(byRating)[0];
  const lo = 5, hi = 10, pos = v => ((v - lo) / (hi - lo) * 100).toFixed(1);
  el.innerHTML = `<div class="pwrap swrap"><a class="back" href="#top">→ العودة إلى آلة الزمن</a>
   <div class="ghead"><h1>أرقام الزمن الجميل</h1><p>الأرشيف بالأرقام، وتتحدّث وحدها كلما أُضيف فيلم أو تغيّر تقييم.</p></div>
   <dl class="hero-n"><div><dt>فيلم</dt><dd>${ar(F.length)}</dd></div><div><dt>اسم من الصنّاع</dt><dd>${ar(P.size)}</dd></div><div><dt>متوسط IMDb</dt><dd>${avg(F.filter(score).map(score)).toFixed(1)}</dd></div><div><dt>متوسط السينما.كوم</dt><dd>${avg(F.filter(escore).map(escore)).toFixed(1)}</dd></div></dl>
   <p class="finding">الأعلى تقييمًا في الأرشيف: <a href="#film-${esc(top.id)}">«${esc(top.title)}»</a> (${ar(top.year)}) بتقييم ${score(top).toFixed(1)} على IMDb.</p>
   <div class="sgrid">
    <section class="sc"><h2>عدد الأفلام في كل عقد</h2>${bars(perEra.map(x => ({ k: x.e.name, v: x.fs.length, href: '#list-' + x.e.id })), v => ar(v))}</section>
    <section class="sc"><h2>متوسط تقييم IMDb لكل عقد</h2>${bars(perEra.filter(x => x.fs.some(score)).map(x => ({ k: x.e.name, v: avg(x.fs.filter(score).map(score)), href: '#list-' + x.e.id })), v => v.toFixed(1), 10)}<p class="note">المقياس من ٠ إلى ١٠.</p></section>
    <section class="sc"><h2>أكثر المخرجين حضورًا</h2>${bars(dirs, v => ar(v))}</section>
    <section class="sc"><h2>أكثر الممثلين حضورًا</h2>${bars(acts, v => ar(v))}</section>
    <section class="sc"><h2>الأنواع</h2>${bars(gen, v => ar(v))}<p class="note">الفيلم الواحد قد يحمل أكثر من نوع.</p></section>
    <section class="sc wide"><h2>حيث يختلف الجمهوران</h2><p class="note">أكبر الفروق بين تقييم السينما.كوم وتقييم IMDb للفيلم نفسه.</p>
     <div class="legend"><span><i class="d1"></i>IMDb</span><span><i class="d2"></i>السينما.كوم</span></div>
     <div class="dumb">${gap.map(({ f }) => { const a = score(f), b = escore(f), l = Math.min(a, b), r = Math.max(a, b); return `<div class="dr" title="${esc(f.title)}: IMDb ${a.toFixed(1)} · السينما.كوم ${b.toFixed(1)}"><a class="dk" href="#film-${esc(f.id)}">${esc(f.title)}</a><span class="dt"><span class="dl" style="right:${pos(l)}%;width:${(pos(r) - pos(l)).toFixed(1)}%"></span><i class="d1" style="right:${pos(a)}%"></i><i class="d2" style="right:${pos(b)}%"></i></span><span class="dv">${(b - a > 0 ? '+' : '') + (b - a).toFixed(1)}</span></div>`; }).join('')}</div>
     <div class="axis"><span>٥</span><span>٦</span><span>٧</span><span>٨</span><span>٩</span><span>١٠</span></div></section>
   </div></div>`;
}

/* ——— المسارات ——— */
window.SZX = {
  route(h) {
    if (h === 'game') renderGame();
    else if (h === 'people') renderPeople();
    else if (h === 'network') renderNetwork();
    else if (h === 'stats') renderStats();
    else if (h.startsWith('p-')) renderPerson(h.slice(2));
  }
};
const getj = u => fetch(u, { cache: 'no-cache' }).then(r => r.ok ? r.json() : {}).catch(() => ({}));
Promise.all([getj('data/wikidata.json'), getj('data/people.json')]).then(([d, px]) => {
  WD = { people: {}, films: {}, ...d }; PX = px || {};
  lobby();
  const h = decodeURIComponent(location.hash.slice(1));
  if (/^(game|people|network|stats|p-)/.test(h)) SZX.route(h);
});
}
