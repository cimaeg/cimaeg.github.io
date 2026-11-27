"""يجمع الطاقم الكامل من صفحات الطاقم في السينما.كوم. الناتج ملف JSONL يُرفع كأثر للتشغيل."""
import json, re, sys, time, html, requests
S = requests.Session(); S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36", "Accept-Language": "ar"})
cl = lambda s: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
def get(u):
    for k in range(6):
        try:
            r = S.get(u, timeout=40)
            if r.status_code == 200: return r.text
            if r.status_code in (429, 503, 403): time.sleep(30 * (k + 1)); continue
            return None
        except Exception: time.sleep(10)
    return None
if sys.argv[1] == "debug":
    t = get(f"https://elcinema.com/work/{sys.argv[2]}/cast")
    parts = t.split('class="section-title"')
    for p in parts[1:4]: print("SEC", repr(p[:2500]))
    sys.exit()
import unicodedata
def parse(t):
    out = {}
    for sec in t.split('class="section-title"')[1:]:
        title = unicodedata.normalize("NFKC", cl(sec.split("<span", 1)[0].split(">", 1)[-1]))
        if "تمثيل" not in title: continue
        rows = []
        for pid, name, role in re.findall(r'<li><a href="/person/(\d+)/">([^<]+)</a></li>\s*(?:<li class="subheader">([^<]*)</li>)?', sec):
            role = cl(role).strip("() \u00a0")
            if not any(r[0] == pid for r in rows): rows.append([pid, cl(name), role])
        out[title] = rows
    return out
F = json.load(open("data/films.json"))
todo = [(f["id"], f["ratings"]["elcinema"]["id"]) for f in F if ((f.get("ratings") or {}).get("elcinema") or {}).get("id")]
a, b = int(sys.argv[2]), int(sys.argv[3])
with open("cast.jsonl", "w", encoding="utf-8") as o:
    for fid, e in todo[a:b]:
        t = get(f"https://elcinema.com/work/{e}/cast")
        rec = {"id": fid, "e": e, "secs": parse(t) if t else None}
        o.write(json.dumps(rec, ensure_ascii=False) + "\n"); o.flush()
        time.sleep(0.8)
print("done", a, b)
