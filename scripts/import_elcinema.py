"""يكمل الأرشيف من السينما.كوم: كل فيلم مصري حتى عام ٢٠٠٠ غير موجود في الأرشيف يُضاف بطاقمه،
والأفلام المستوردة من ويكي بيانات التي ينقصها مخرج أو ممثلون تُكمَّل من صفحة طاقمها هناك.

- القائمة من فهرس الأعمال المصرية: elcinema.com/index/work/country/eg
- الطاقم من صفحة /work/<رقم>/cast/ بترتيب الظهور فيها، والتصنيف والمدة من صفحة العمل.
- ما يُجلب يُحفظ في data/elcinema.json فلا يُعاد جلبه في كل أسبوع.
- الأسماء تُوحَّد مع ويكي بيانات عن طريق معرّف الشخص في السينما.كوم (P3136).

يُشغَّل بعد scripts/import_films.py. الأفلام المضافة تحمل "src": "elcinema".
"""
import json, re, sys, time, html, unicodedata, collections
import requests

FILMS = "data/films.json"
WD = "data/wikidata.json"
CACHE = "data/elcinema.json"
MAX_YEAR, MIN_YEAR = 2000, 1920
CAST_N = 6
BASE = "https://elcinema.com"
DELAY = 0.6
BUDGET = float(sys.argv[sys.argv.index("--minutes") + 1]) * 60 if "--minutes" in sys.argv else 75 * 60
T0 = time.time()

S = requests.Session()
S.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "ar,en;q=0.8",
})
AR_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
GENRES = {
    "كوميدي": "كوميديا", "كوميديا": "كوميديا", "دراما": "دراما", "رومانسي": "رومانسي", "رومانسية": "رومانسي",
    "موسيقي": "غنائي", "غنائي": "غنائي", "استعراضي": "استعراضي", "جريمة": "جريمة", "إثارة": "تشويق",
    "تشويق": "تشويق", "أكشن": "أكشن", "حركة": "أكشن", "رعب": "رعب", "حرب": "حرب", "حربي": "حرب",
    "تاريخي": "تاريخي", "سياسي": "سياسي", "خيال علمي": "خيال علمي", "فانتازيا": "فانتازيا",
    "مغامرات": "مغامرات", "مغامرة": "مغامرات", "عائلي": "عائلي", "سيرة ذاتية": "سيرة", "اجتماعي": "دراما",
    "غموض": "تشويق", "بوليسي": "جريمة", "ميلودراما": "دراما", "صامت": "صامت",
}


def time_left():
    return BUDGET - (time.time() - T0)


def get(path):
    for i in range(3):
        try:
            r = S.get(BASE + path, timeout=30)
            time.sleep(DELAY)
            if r.status_code == 200:
                return r.text
            if r.status_code == 404:
                return None
            print("  !", r.status_code, path, flush=True)
        except Exception as e:
            print("  !", e, path, flush=True)
        time.sleep(5 + 10 * i)
    return None


def text(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s)).strip()


def norm(s):
    s = re.sub(r"[ً-ْـ«»\"()]", "", s or "")
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه").replace("ى", "ي")
    s = re.sub(r"\bعبد\s+", "عبد", s)
    return re.sub(r"\s+", " ", s).strip()


# ——— ١) فهرس الأعمال المصرية ———
def crawl_index(cache):
    """يقرأ صفحات الفهرس (الأحدث أولًا) ويتوقف بعد أن يتجاوز عام ١٩٢٠ بصفحتين."""
    works = cache.setdefault("index", {})
    first = get("/index/work/country/eg/")
    if not first:
        print("index unavailable")
        return works
    pages = [int(p) for p in re.findall(r"[?&]page=(\d+)", first)]
    last = max(pages) if pages else 1
    print("index pages:", last, flush=True)
    old_pages = 0
    for page in range(1, last + 1):
        t = first if page == 1 else get(f"/index/work/country/eg/?page={page}")
        if not t:
            continue
        years = []
        for row in re.findall(r"<tr>(.*?)</tr>", t, re.S):
            m = re.search(r'href="/work/(\d+)/">([^<]+)</a>', row)
            tds = re.findall(r"<td>(.*?)</td>", row, re.S)
            if not m or len(tds) < 5:
                continue
            y = re.search(r"(1[89]\d\d|20\d\d)", text(tds[4]))
            year = int(y.group(1)) if y else None
            years.append(year or 9999)
            cat, sub = text(tds[2]), text(tds[3])
            if any(x in sub for x in ("قصير", "تسجيلي", "وثائقي", "تلفزيون", "إذاعي")):
                continue
            if cat == "فيلم" and year and MIN_YEAR <= year <= MAX_YEAR:
                works[m.group(1)] = {"title": text(m.group(2)), "year": year}
        if years and max(years) < MIN_YEAR:
            old_pages += 1
            if old_pages >= 2:
                break
        if page % 50 == 0:
            print(f"  page {page}/{last}: {len(works)} films so far", flush=True)
    print("films in index (<=2000):", len(works), flush=True)
    return works


# ——— ٢) صفحة العمل وصفحة الطاقم ———
def parse_work(wid):
    t = get(f"/work/{wid}/")
    if not t:
        return None
    out = {}
    m = re.search(r"<title>\s*([^<]+?)\s*</title>", t)
    if m:
        parts = [p.strip() for p in html.unescape(m.group(1)).split(" - ")]
        if len(parts) >= 2:
            out["title"] = parts[1]
    out["country_eg"] = "/index/work/country/eg" in t
    out["movie"] = 'href="/index/work/category/1"' in t
    m = re.search(r"<li>\s*(\d{2,3})\s*دقيقة\s*</li>", t)
    if m:
        out["duration"] = int(m.group(1))
    m = re.search(r'release_day/(\d\d)-(\d\d)/">[^<]*</a>\s*<a href="/index/work/release_year/(\d{4})/', t)
    if m:
        out["released"] = f"{m.group(3)}-{m.group(1)}-{m.group(2)}"
    else:
        m = re.search(r'release_year/(\d{4})/', t)
        if m:
            out["released"] = m.group(1)
    out["genre"] = list(dict.fromkeys(text(g) for g in re.findall(r'href="/index/work/genre/\d+">([^<]+)</a>', t)))
    m = re.search(r'title="التقييم\s*:\s*([\d.]+)', t)
    if m and float(m.group(1)) > 0:
        out["score"] = round(float(m.group(1)), 1)
    return out


def parse_cast(wid):
    t = get(f"/work/{wid}/cast/")
    if not t:
        return None
    sections = {}
    chunks = re.split(r'<h3 class="section-title">', t)[1:]
    for ch in chunks:
        title = text(ch.split("</h3>", 1)[0])
        title = re.sub(r"\(\d+\)", "", title).strip()
        people = []
        for pid, name in re.findall(r'<li><a href="/person/(\d+)/">([^<]+)</a></li>', ch):
            if pid not in [p for p, _ in people]:
                people.append((pid, text(name)))
        if people:
            sections.setdefault(title, people)
    return sections


def pick(sections, *keys):
    for k, v in sections.items():
        if any(x in k for x in keys):
            return v
    return []


# ——— ٣) توحيد الأسماء عبر ويكي بيانات ———
def wikidata_people(pids):
    out = {}
    pids = list(pids)
    for i in range(0, len(pids), 300):
        vals = " ".join(f'"{p}"' for p in pids[i:i + 300])
        q = f"""SELECT ?e ?p ?ar ?sx ?b ?bp ?d ?dp WHERE {{
  VALUES ?e {{ {vals} }} ?p wdt:P3136 ?e .
  OPTIONAL {{ ?p rdfs:label ?ar FILTER(LANG(?ar) = "ar") }}
  OPTIONAL {{ ?p wdt:P21 ?sx }}
  OPTIONAL {{ ?p p:P569/psv:P569 [ wikibase:timeValue ?b ; wikibase:timePrecision ?bp ] }}
  OPTIONAL {{ ?p p:P570/psv:P570 [ wikibase:timeValue ?d ; wikibase:timePrecision ?dp ] }}
}}"""
        for k in range(4):
            try:
                r = requests.post("https://query.wikidata.org/sparql", data={"query": q}, timeout=120,
                                  headers={"Accept": "application/sparql-results+json",
                                           "User-Agent": "ShashaZaman/1.0 (https://cimaeg.github.io)"})
                if r.status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(20 + 30 * k)
        else:
            continue
        for b in r.json()["results"]["bindings"]:
            g = lambda k: b.get(k, {}).get("value")
            e = g("e")
            o = out.setdefault(e, {"qid": g("p").rsplit("/", 1)[-1], "ar": None, "f": False, "born": None, "died": None})
            o["ar"] = o["ar"] or g("ar")
            if g("sx") and g("sx").rsplit("/", 1)[-1] in ("Q6581072", "Q1052281"):
                o["f"] = True
            for key, v, pr in (("born", g("b"), g("bp")), ("died", g("d"), g("dp"))):
                m = re.match(r"\+?(\d{4})-(\d\d)-(\d\d)", v or "")
                if m:
                    val = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if int(pr or 0) >= 11 else m.group(1)
                    if not o[key] or len(val) > len(o[key]):
                        o[key] = val
        time.sleep(1)
    return out


def test():
    """تجربة سريعة: صفحتان من الفهرس وثلاثة أعمال، بلا حفظ."""
    t = get("/index/work/country/eg/")
    pages = [int(p) for p in re.findall(r"[?&]page=(\d+)", t or "")]
    print("pages:", max(pages) if pages else None)
    for page in (max(pages) - 40, max(pages) - 120):
        t = get(f"/index/work/country/eg/?page={page}")
        rows = re.findall(r"<tr>(.*?)</tr>", t, re.S)
        print("page", page, [(re.search(r'href="/work/(\d+)/">([^<]+)', r).groups(), [text(x) for x in re.findall(r"<td>(.*?)</td>", r, re.S)][2:5]) for r in rows[1:6] if re.search(r'href="/work/', r)])
    for wid in ("1005029", "1003847", "1010326"):
        print(wid, parse_work(wid))
        c = parse_cast(wid)
        print("  sections:", {k: v[:4] for k, v in (c or {}).items()})
        print("  picked:", pick(c, "إخراج", "اخراج")[:2], pick(c, "تأليف", "سيناريو", "قصة")[:3], pick(c, "تمثيل", "بطولة")[:6])
    print(wikidata_people(["1049796", "1072547", "1037623"]))


def main():
    films = json.load(open(FILMS, encoding="utf-8"))
    wd = json.load(open(WD, encoding="utf-8"))
    try:
        cache = json.load(open(CACHE, encoding="utf-8"))
    except Exception:
        cache = {}
    cache.setdefault("works", {})

    index = crawl_index(cache)

    by_elc = {}
    by_title = {}
    for f in films:
        e = ((f.get("ratings") or {}).get("elcinema") or {}).get("id")
        if e:
            by_elc[str(e)] = f
        by_title.setdefault((norm(f["title"]), f["year"]), f)

    # الأعمال المطلوبة: الجديدة كليًا، ثم المستوردة الناقصة
    new_ids = [w for w, x in sorted(index.items(), key=lambda kv: kv[1]["year"])
               if w not in by_elc and not any((norm(x["title"]), x["year"] + d) in by_title for d in (0, -1, 1))]
    fill_ids = [e for e, f in by_elc.items() if f.get("src") == "wikidata" and (not f.get("cast") or not f.get("director"))]
    print("new works:", len(new_ids), "imported films to complete:", len(fill_ids), flush=True)

    fetched = 0
    for wid in new_ids + fill_ids:
        if wid in cache["works"]:
            continue
        if time_left() < 60:
            print("time budget reached; the rest continues next run", flush=True)
            break
        w = parse_work(wid) if wid in new_ids else {}
        if w is None:
            continue
        c = parse_cast(wid)
        if c is None:
            continue
        w["cast"] = pick(c, "تمثيل", "بطولة")
        w["director"] = pick(c, "إخراج", "اخراج")
        w["writer"] = pick(c, "تأليف", "سيناريو", "قصة")
        w["producer"] = pick(c, "إنتاج", "انتاج")
        cache["works"][wid] = w
        fetched += 1
        if fetched % 50 == 0:
            print(f"  fetched {fetched} ({int(time_left() // 60)} min left)", flush=True)
            json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    print("fetched this run:", fetched, flush=True)

    # توحيد الأسماء
    pids = {p for w in cache["works"].values() for role in ("cast", "director", "writer", "producer") for p, _ in w.get(role, [])}
    wdp = wikidata_people(pids) if pids else {}
    curated = {re.sub(r"\s*\(.*?\)", "", n).strip() for f in films if not f.get("src")
               for n in (f.get("cast") or []) + [f.get("director") or ""]}
    by_qid_name = {v["qid"]: n for n, v in wd.get("people", {}).items() if v.get("qid") and n in curated}
    known_names = {}
    for f in films:
        for n in (f.get("cast") or []) + [f.get("director") or ""]:
            if n:
                known_names.setdefault(norm(n), n)

    def name(pid, raw):
        x = wdp.get(pid)
        if x:
            if x["qid"] in by_qid_name:
                return by_qid_name[x["qid"]]
            if x["ar"] and re.search(r"[؀-ۿ]", x["ar"]):
                return re.sub(r"\s*\([^)]*\)\s*$", "", x["ar"]).strip()
        return known_names.get(norm(raw), raw)

    people_out = wd.setdefault("people", {})

    def note(pid, n):
        x = wdp.get(pid)
        if not x:
            return
        po = people_out.setdefault(n, {})
        if po.get("qid") and po["qid"] != x["qid"]:
            return
        po["qid"] = x["qid"]
        for k in ("born", "died"):
            if x[k] and (not po.get(k) or len(x[k]) > len(po[k])):
                po[k] = x[k]
        if x["f"]:
            po["f"] = True

    # ——— إكمال الأفلام المستوردة من ويكي بيانات ———
    completed = 0
    for wid in fill_ids:
        w, f = cache["works"].get(wid), by_elc[wid]
        if not w:
            continue
        if not f.get("cast") and w.get("cast"):
            f["cast"] = [name(p, n) for p, n in w["cast"][:CAST_N]]
            for p, n in w["cast"][:CAST_N]:
                note(p, name(p, n))
            completed += 1
        if not f.get("director") and w.get("director"):
            p, n = w["director"][0]
            f["director"] = name(p, n)
            note(p, f["director"])
        if not f.get("writer") and w.get("writer"):
            f["writer"] = "، ".join(dict.fromkeys(name(p, n) for p, n in w["writer"][:3]))

    # ——— الأفلام الجديدة ———
    taken = {f["id"] for f in films}
    added = []
    # الأفلام المضافة في تشغيلات سابقة تبقى كما هي؛ لا يُضاف هنا إلا الجديد
    old_elc = {}
    for wid in new_ids:
        w, x = cache["works"].get(wid), index[wid]
        if not w or not w.get("movie", True) or w.get("country_eg") is False:
            continue
        year = x["year"]
        rid = f"{year}-elc{wid}"
        if rid in taken:
            continue
        # نفس الفيلم بسنة مختلفة قليلًا في المصدر الآخر: نفس العنوان، ونفس المخرج أو ممثل مشترك
        raw_cast = {name(p, n) for p, n in w.get("cast", [])[:CAST_N]}
        raw_dir = name(*w["director"][0]) if w.get("director") else None
        if any(norm(o["title"]) == norm(w.get("title") or x["title"]) and abs(o["year"] - year) <= 3
               and ((raw_dir and o.get("director") == raw_dir) or raw_cast & set(o.get("cast") or []))
               for o in films):
            continue
        rec = old_elc.get(rid, {"id": rid})
        cast = [(p, name(p, n)) for p, n in w.get("cast", [])[:CAST_N]]
        director = [(p, name(p, n)) for p, n in w.get("director", [])[:1]]
        writers = list(dict.fromkeys(name(p, n) for p, n in w.get("writer", [])[:3]))
        producers = list(dict.fromkeys(name(p, n) for p, n in w.get("producer", [])[:2]))
        genre = list(dict.fromkeys(GENRES[g] for g in w.get("genre", []) if g in GENRES))[:3] or ["دراما"]
        rec.update({
            "title": w.get("title") or x["title"],
            "year": year,
            "director": director[0][1] if director else None,
            "cast": [n for _, n in cast],
            "genre": genre,
            "writer": "، ".join(writers) or None,
            "producer": "، ".join(producers) or None,
            "duration": f"{str(w['duration']).translate(AR_DIGITS)} دقيقة" if w.get("duration") else None,
            "src": "elcinema",
        })
        for k in ("director", "writer", "producer", "duration"):
            if rec.get(k) is None:
                rec.pop(k, None)
        rec.setdefault("summary", "")
        rec.setdefault("poster", {"status": "generated", "url": None, "credit": None})
        el = rec.setdefault("ratings", {}).setdefault("elcinema", {})
        el["id"] = wid
        if w.get("score") and not el.get("score"):
            el["score"] = w["score"]
        for p, n in cast + director:
            note(p, n)
        if w.get("released"):
            wd.setdefault("films", {}).setdefault(rid, {})["released"] = w["released"]
        added.append(rec)
        taken.add(rid)

    films += added
    films.sort(key=lambda f: (f["year"], f["title"]))
    print("completed from elCinema:", completed, "added:", len(added), "total films:", len(films))
    print("by decade:", sorted(collections.Counter((f["year"] // 10) * 10 for f in films).items()))
    for f in added[:: max(1, len(added) // 10)]:
        print("  sample:", json.dumps(f, ensure_ascii=False)[:300])

    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    open(FILMS, "w", encoding="utf-8").write("[\n" + ",\n".join(json.dumps(x, ensure_ascii=False) for x in films) + "\n]\n")
    json.dump(wd, open(WD, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    test() if "--test" in sys.argv else main()
