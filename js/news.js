/* شاشة زمان — «الجريدة»: مقالات وتحقيقات وأخبار، بروابط إلى الأفلام والصنّاع وقصاصات في صفحاتهم */
{
const Z = window.SZ;
const { esc, ar, eraOf, mpo, md, showPage } = Z;
const $ = id => document.getElementById(id);
const FILMS = () => Z.FILMS;
const MONTHS = ['يناير','فبراير','مارس','أبريل','مايو','يونيو','يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر'];
const fmt = d => { if (!d) return ''; const [y, m, dd] = d.split('-'); return m ? (dd ? ar(+dd) + ' ' : '') + MONTHS[+m - 1] + ' ' + ar(y) : ar(y); };
const KINDS = { 'خبر': 'k-news', 'مقال': 'k-essay', 'تحقيق': 'k-probe', 'حوار': 'k-talk' };
const getj = u => fetch(u, { cache: 'no-cache' }).then(r => r.ok ? r.json() : null).catch(() => null);
let LIST = null, PX = {};
const load = () => LIST ? Promise.resolve(LIST) : Promise.all([getj('data/articles.json'), getj('data/people.json')]).then(([a, p]) => {
  PX = p || {};
  LIST = (a || []).filter(x => x && x.id && x.title).sort((x, y) => String(y.date).localeCompare(String(x.date)));
  return LIST;
});
const body = {};
const text = id => id in body ? Promise.resolve(body[id]) : fetch(`articles/${encodeURIComponent(id)}.md`, { cache: 'no-cache' }).then(r => r.ok ? r.text() : null).catch(() => null).then(t => (body[id] = t));
const film = id => FILMS().find(f => f.id === id);
const face = n => { const x = PX[n]; return x && /^people\/[\w.-]+\.webp$/.test(x.photo || '') ? x : null; };
const stamp = k => `<span class="nstamp ${KINDS[k] || 'k-essay'}">${esc(k || 'مقال')}</span>`;
const issueNo = d => { const t = Date.parse(d || ''); return isNaN(t) ? '' : ar(Math.floor((t - Date.UTC(1927, 10, 16)) / 864e5)); }; // من عرض «ليلى» 16 نوفمبر 1927

/* ——— الصفحة الأولى ——— */
let kind = '';
async function renderIndex() {
  const el = showPage('e40', 'الجريدة');
  el.innerHTML = `<div class="nwrap"><p class="lnone">…</p></div>`;
  const all = await load();
  if (decodeURIComponent(location.hash.slice(1)) !== 'news') return;
  const today = new Date().toISOString().slice(0, 10);
  const kinds = [...new Set(all.map(x => x.kind || 'مقال'))];
  const sel = all.filter(x => !kind || (x.kind || 'مقال') === kind);
  const card = (x, lead) => {
    const fs = (x.films || []).map(film).filter(Boolean), ph = (x.people || []).map(face).find(Boolean);
    const pic = fs[0] ? mpo(fs[0], eraOf(fs[0].year).id) : ph ? `<span class="nface"><img src="/img/${esc(ph.photo)}" alt="" loading="lazy" style="object-position:${esc(ph.focus || '50% 25%')}"></span>` : '';
    return `<a class="nclip${lead ? ' lead' : ''}" href="#a-${encodeURIComponent(x.id)}">${stamp(x.kind)}
      ${lead && pic ? `<span class="npic">${pic}</span>` : ''}
      <span class="ntxt"><b>${esc(x.title)}</b>${x.dek ? `<em>${esc(x.dek)}</em>` : ''}
      <small>${x.author ? esc(x.author) + ' · ' : ''}${fmt(x.date)}${x.source && (x.source.name || x.source.url) ? ' · عن ' + esc(x.source.name || host(x.source.url)) : ''}</small></span></a>`;
  };
  el.innerHTML = `<div class="nwrap"><a class="back" href="#top">→ العودة إلى آلة الزمن</a>
   <header class="mast"><div class="mtop"><span>العدد ${issueNo(today)}</span><span>${fmt(today)}</span></div>
    <h1>الجريدة</h1><p>مقالات وتحقيقات وأخبار عن السينما المصرية، تقودك أسماؤها إلى أفلامها وصنّاعها في الأرشيف</p></header>
   ${kinds.length > 1 ? `<div class="nkinds" role="group" aria-label="نوع الموضوع"><button type="button" data-k="" aria-pressed="${!kind}">الكل</button>${kinds.map(k => `<button type="button" data-k="${esc(k)}" aria-pressed="${kind === k}">${esc(k)}</button>`).join('')}</div>` : ''}
   ${sel.length ? `<div class="nfront">${card(sel[0], true)}<div class="ncols">${sel.slice(1).map(x => card(x)).join('')}</div></div>`
     : `<div class="nempty"><b>المطبعة تنتظر</b><p>لم يُنشر في الجريدة شيء بعد.</p></div>`}
  </div>`;
  el.querySelectorAll('[data-k]').forEach(b => b.addEventListener('click', () => { kind = b.dataset.k; renderIndex(); }));
}

/* ——— المصدر: يُذكر دائمًا مع رابطه حفظًا للحقوق ——— */
const host = u => { try { return new URL(u).hostname.replace(/^www\./, ''); } catch { return ''; } };
function srcBox(x) {
  const s = x.source || {};
  if (!s.name && !s.url) return `<footer class="nsrc own"><b>المصدر</b><span>${x.author ? esc(x.author) + ' · ' : ''}خاص بشاشة زمان</span></footer>`;
  const name = esc(s.name || host(s.url));
  return `<footer class="nsrc"><b>المصدر</b>
   <span>${s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener">${name}</a>` : name}${s.author ? ' · بقلم ' + esc(s.author) : ''}${s.date ? ' · نُشر في ' + fmt(s.date) : ''}</span>
   ${s.url ? `<a class="nsrc-go" href="${esc(s.url)}" target="_blank" rel="noopener">اقرأ النص في مصدره الأصلي ←</a>` : ''}
   <small>${x.mode === 'summary' ? 'هذا عرض بصياغة شاشة زمان، والنص الأصلي وحقوقه لمصدره.' : 'جميع الحقوق محفوظة للمصدر.'}</small></footer>`;
}


/* ——— ضبط السطور بالكشيدة: يُمدّ الحرف بدل توسيع الفراغات، كالصحف المطبوعة ——— */
const DUAL = /[بتثجحخسشصضطظعغفقكلمنهيئـ]/;          // حروف تتصل بما بعدها
const ARL = /[ء-ي]/;
const PRI = /[سشصضطظكلفق]/;                           // مدّها أجمل
const toAr = t => t.replace(/[0-9]/g, d => '٠١٢٣٤٥٦٧٨٩'[d]);
function wrapWords(root) {
  const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT), nodes = [];
  while (tw.nextNode()) nodes.push(tw.currentNode);
  for (const n of nodes) {
    const parts = toAr(n.nodeValue).split(/(\s+)/), fr = document.createDocumentFragment();
    for (const w of parts) {
      if (!w) continue;
      if (/^\s+$/.test(w)) fr.appendChild(document.createTextNode(w));
      else { const sp = document.createElement('span'); sp.className = 'kw'; sp.textContent = w; fr.appendChild(sp); }
    }
    n.replaceWith(fr);
  }
}
function slots(w) {                                    // مواضع صالحة للمدّ داخل الكلمة، الأفضل أولًا
  const out = [];
  for (let i = 0; i < w.length - 1; i++) {
    const a = w[i], b = w[i + 1];
    if (!DUAL.test(a) || !ARL.test(b)) continue;
    if (a === 'ل' && /[اأإآ]/.test(b)) continue;       // لا نكسر «لا»
    if (/[ً-ْ]/.test(b)) continue;
    out.push({ i: i + 1, p: (PRI.test(a) ? 2 : 0) + (i + 2 === w.length ? 1 : 0) + i / 100 });
  }
  return out.sort((x, y) => y.p - x.p).map(x => x.i);
}
function justify(box) {
  box.querySelectorAll('p').forEach(p => {
    const words = [...p.querySelectorAll('.kw')];
    if (words.length < 4) return;
    p.style.textAlign = 'start';
    const probe = document.createElement('span'); probe.textContent = 'ـــــــــــــــــــ'; probe.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap';
    p.appendChild(probe); const tw = probe.getBoundingClientRect().width / 10; probe.remove();
    if (!tw) { p.style.textAlign = ''; return; }
    const W = p.clientWidth, lines = [];
    for (const w of words) { const r = w.getBoundingClientRect(), L = lines[lines.length - 1]; if (L && Math.abs(L.top - r.top) < r.height / 2) L.ws.push(w); else lines.push({ top: r.top, ws: [w] }); }
    const pr = p.getBoundingClientRect();
    lines.slice(0, -1).forEach(L => {
      const rs = L.ws.map(w => w.getBoundingClientRect());
      const used = Math.max(...rs.map(r => r.right)) - Math.min(...rs.map(r => r.left));
      let need = Math.floor((W - used) / tw);
      if (need <= 0) return;
      const cand = L.ws.map(w => ({ w, t: w.textContent, s: slots(w.textContent) })).filter(c => c.s.length);
      if (!cand.length) return;
      const plan = [];                                  // تسلسل الإضافات بالتناوب بين الكلمات، بحد ٤ لكل كلمة
      for (let r = 0; r < 4 && plan.length < need + 2; r++) for (const c of cand) if (r < c.s.length * 2) plan.push([c, c.s[r % c.s.length]]);
      const apply = k => {
        const add = new Map(cand.map(c => [c, {}]));
        plan.slice(0, k).forEach(([c, at]) => { const m = add.get(c); m[at] = (m[at] || 0) + 1; });
        for (const c of cand) { const m = add.get(c); let o = ''; for (let i = 0; i < c.t.length; i++) o += 'ـ'.repeat(m[i] || 0) + c.t[i]; c.w.textContent = o; }
      };
      const first = L.ws[0], last = L.ws[L.ws.length - 1];
      const ok = () => Math.abs(last.getBoundingClientRect().top - first.getBoundingClientRect().top) < 2;
      let k = Math.min(need, plan.length); apply(k);
      while (k > 0 && !ok()) apply(--k);
    });
    p.style.textAlign = '';
  });
}
let kSrc = null;
function typeset() {
  const b = $('nbody'); if (!b || kSrc == null) return;
  b.innerHTML = kSrc;
  b.querySelectorAll('a[href^="#film-"],a[href^="#p-"]').forEach(a => a.classList.add('xref'));
  wrapWords(b);
  (document.fonts ? document.fonts.ready : Promise.resolve()).then(() => justify(b));
}
let rz; addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(() => { if ($('nbody') && !$('nbody').closest('[hidden]')) typeset(); }, 200); });

/* ——— صفحة المقالة ——— */
async function renderArticle(id) {
  const all = await load(), x = all.find(a => a.id === id);
  const fs = x ? (x.films || []).map(film).filter(Boolean) : [];
  const el = showPage(fs.length ? eraOf(fs[0].year).id : 'e40', x ? x.title : 'الجريدة');
  if (!x) { el.innerHTML = `<div class="nwrap"><a class="back" href="#news">→ الجريدة</a><p class="lnone">لا يوجد هذا الموضوع.</p></div>`; return; }
  const ppl = (x.people || []).filter(n => Z.FILMS.some(f => (f.cast || []).map(Z.pname).includes(n) || Z.pname(f.director) === n));
  const who = n => { const p = face(n); return `<a class="nwho" href="#p-${encodeURIComponent(n)}">${p ? `<span class="nface"><img src="/img/${esc(p.photo)}" alt="" loading="lazy" style="object-position:${esc(p.focus || '50% 25%')}"></span>` : `<span class="nface ini">${esc(n.replace(/^ال/, '')[0] || n[0])}</span>`}<b>${esc(n)}</b></a>`; };
  el.innerHTML = `<div class="nwrap"><a class="back" href="#news">→ الجريدة</a>
   <article class="npaper">
    <div class="nline">${stamp(x.kind)}<span>${fmt(x.date)}</span>${x.source && x.source.name ? `<span>عن ${x.source.url ? `<a href="${esc(x.source.url)}" target="_blank" rel="noopener">${esc(x.source.name)}</a>` : esc(x.source.name)}</span>` : ''}</div>
    <h1>${esc(x.title)}</h1>${x.dek ? `<p class="ndek">${esc(x.dek)}</p>` : ''}
    ${x.author ? `<p class="nby">بقلم ${esc(x.author)}</p>` : ''}
    <div class="nbody" id="nbody"></div>
    ${srcBox(x)}
   </article>
   ${fs.length || ppl.length ? `<section class="ncast" aria-label="ورد في هذا الموضوع"><h2>ورد في هذا الموضوع</h2>
    ${fs.length ? `<div class="nreel">${fs.map(f => `<a href="#film-${esc(f.id)}">${mpo(f, eraOf(f.year).id)}<span><b>${esc(f.title)}</b><small>${ar(f.year)}</small></span></a>`).join('')}</div>` : ''}
    ${ppl.length ? `<div class="npeople">${ppl.map(who).join('')}</div>` : ''}</section>` : ''}
   ${(() => { const more = all.filter(a => a !== x && ((a.films || []).some(f => (x.films || []).includes(f)) || (a.people || []).some(p => (x.people || []).includes(p)))).slice(0, 3); return more.length ? `<section class="nmore"><h2>في الموضوع نفسه</h2><div class="ncols">${more.map(a => `<a class="nclip" href="#a-${encodeURIComponent(a.id)}">${stamp(a.kind)}<span class="ntxt"><b>${esc(a.title)}</b><small>${fmt(a.date)}</small></span></a>`).join('')}</div></section>` : ''; })()}
  </div>`;
  const t = await text(id);
  if (decodeURIComponent(location.hash.slice(3)) !== id) return;
  kSrc = t ? md(t) : '<p class="lnone">النص غير متاح.</p>';
  typeset();
}

/* ——— بطاقة معاينة عند المرور على اسم مرتبط ——— */
let tip;
function preview(a) {
  const h = decodeURIComponent(a.getAttribute('href').slice(1));
  let inner = '';
  if (h.startsWith('film-')) { const f = film(h.slice(5)); if (!f) return; inner = `${mpo(f, eraOf(f.year).id)}<span><b>${esc(f.title)}</b><small>${ar(f.year)}${f.director ? ' · إخراج ' + esc(f.director) : ''}</small></span>`; }
  else { const n = h.slice(2), p = face(n), c = Z.FILMS.filter(f => (f.cast || []).map(Z.pname).includes(n) || Z.pname(f.director) === n).length;
    inner = `${p ? `<span class="nface"><img src="/img/${esc(p.photo)}" alt="" style="object-position:${esc(p.focus || '50% 25%')}"></span>` : ''}<span><b>${esc(n)}</b><small>${ar(c)} ${c > 2 && c < 11 ? 'أفلام' : 'فيلمًا'} في الأرشيف</small></span>`; }
  tip = tip || document.body.appendChild(Object.assign(document.createElement('div'), { className: 'ntip', role: 'tooltip' }));
  tip.innerHTML = inner; tip.hidden = false;
  const r = a.getBoundingClientRect(), w = tip.offsetWidth, hgt = tip.offsetHeight;
  tip.style.left = Math.max(8, Math.min(innerWidth - w - 8, r.left + r.width / 2 - w / 2)) + 'px';
  tip.style.top = (r.top > hgt + 16 ? r.top - hgt - 10 : r.bottom + 10) + 'px';
}
const hide = () => { if (tip) tip.hidden = true; };
const xr = e => e.target.closest && e.target.closest('.nbody a.xref');
document.addEventListener('mouseover', e => { const a = xr(e); if (a) preview(a); });
document.addEventListener('mouseout', e => { if (xr(e)) hide(); });
document.addEventListener('focusin', e => { const a = xr(e); a ? preview(a) : hide(); });
addEventListener('scroll', hide, { passive: true }); addEventListener('hashchange', hide);

/* ——— قصاصات في صفحات الأفلام والصنّاع ——— */
const clipBox = (arr, title) => arr.length ? `<div class="box nclips"><h4>${title}</h4>${arr.map(a => `<a class="mini" href="#a-${encodeURIComponent(a.id)}">${stamp(a.kind)}<b>${esc(a.title)}</b><small>${fmt(a.date)}</small></a>`).join('')}</div>` : '';
async function decorate(kindOf, key, hash) {
  const all = await load();
  const hit = all.filter(a => (a[kindOf] || []).includes(key));
  if (!hit.length || decodeURIComponent(location.hash.slice(1)) !== hash) return;
  const side = kindOf === 'films' ? $('side') : document.querySelector('#page .side');
  if (side && !side.querySelector('.nclips')) side.insertAdjacentHTML('afterbegin', clipBox(hit, 'قصاصات صحفية'));
}

window.SZN = {
  route(h) { if (h === 'news') renderIndex(); else if (h.startsWith('a-')) renderArticle(h.slice(2)); },
  film(id) { decorate('films', id, 'film-' + id); },
  person(n) { decorate('people', n, 'p-' + n); }
};
const h = decodeURIComponent(location.hash.slice(1));
if (h === 'news' || h.startsWith('a-')) SZN.route(h);
else if (h.startsWith('film-')) SZN.film(h.slice(5));
else if (h.startsWith('p-')) SZN.person(h.slice(2));
}
