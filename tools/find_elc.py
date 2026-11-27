"""يبحث في السينما.كوم عن أفلام بلا رابط ويقرأ طاقمها وبلدها. للقراءة فقط."""
import json, re, sys, time, html, requests
S = requests.Session(); S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36", "Accept-Language": "ar"})
def clean(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
if sys.argv[1] == "debug":
    t = S.get("https://elcinema.com/search/", params={"q": sys.argv[2]}, timeout=30).text
    i = t.find("/work/")
    print("DBG", repr(t[max(0, i-800):i+4000])); sys.exit()
F = json.load(open("data/films.json"))
T = [x for x in F if len(x.get("cast") or []) <= 2 and not ((x.get("ratings") or {}).get("elcinema") or {}).get("id")]
def cast_country(e):
    t = S.get(f"https://elcinema.com/work/{e}/", timeout=30).text
    m = re.search(r'id="work_country">(.*?)</ul>', t, re.S)
    country = re.findall(r'/index/work/country/([a-z]{2})">([^<]+)<', m.group(1)) if m else []
    h = re.search(r"<h1[^>]*>(.*?)</h1>", t, re.S)
    c = S.get(f"https://elcinema.com/work/{e}/cast", timeout=30).text
    parts = c.split('class="section-title"'); seg = parts[1] if len(parts) > 1 else ""
    names = list(dict.fromkeys(clean(n) for _, n in re.findall(r'<li><a href="/person/(\d+)/">([^<]+)</a></li>', seg)))
    dm = re.search(r'ﺇﺧﺮاﺝ|إخراج', c)
    return {"h1": clean(h.group(1)) if h else "", "country": country, "cast": names[:10]}
for x in T:
    o = {"id": x["id"], "title": x["title"], "year": x["year"], "dir": x.get("director")}
    try:
        t = S.get("https://elcinema.com/search/", params={"q": x["title"]}, timeout=30).text
        cands = []
        for wid, rest in re.findall(r'href="/work/(\d+)/"[^>]*>(.*?)</a>', t, re.S):
            s = clean(rest)
            if s and wid not in [c[0] for c in cands]: cands.append((wid, s))
        o["cands"] = cands[:8]
        yr = str(x["year"])
        nz = lambda v: re.sub(r"[\s/()،,:.!؟?-]", "", re.sub("[أإآ]", "ا", v).replace("ة", "ه").replace("ى", "ي"))
        a = nz(x["title"])
        good = [c for c in cands if nz(c[1]) and (nz(c[1]) in a or a in nz(c[1]))]
        for wid, s in good[:5]:
            m = cast_country(wid); time.sleep(0.3)
            if any(str(int(yr) + d) in m["h1"] for d in (0, -1, 1)):
                o["match"] = wid; o.update(m); break
    except Exception as ex:
        o["err"] = str(ex)
    print("FIND", json.dumps(o, ensure_ascii=False), flush=True)
    time.sleep(0.3)
