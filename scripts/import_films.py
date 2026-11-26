"""يستورد الأفلام الروائية المصرية حتى عام ٢٠٠٠ من ويكي بيانات، ويرتّب طاقم كل فيلم حسب ترتيب IMDb.

المصادر:
- ويكي بيانات: قائمة الأفلام وعناوينها العربية والمخرجين والمؤلفين والممثلين وتواريخهم،
  ومعرّفا الفيلم في IMDb والسينما.كوم (لتحديث التقييمات أسبوعيًا).
- ملفات IMDb الرسمية: ترتيب أسماء الطاقم (من الأبرز) ومدة الفيلم وتصنيفه حين تغيب عن ويكي بيانات.

الأفلام المكتوبة يدويًا في data/films.json لا تُمس. الأفلام المستوردة تحمل "src": "wikidata"،
ويُحدَّث طاقمها وبياناتها في كل تشغيل، إلا الحقول التي يضيفها صاحب الموقع يدويًا (الملخص والأفيش).

التشغيل:  python scripts/import_films.py          (يكتب الملفات)
          python scripts/import_films.py --dry    (يطبع الإحصاءات فقط)
"""
import json, re, sys, time, gzip, io, collections, unicodedata
import requests

FILMS = "data/films.json"
WD = "data/wikidata.json"
DRY = "--dry" in sys.argv
MAX_YEAR = 2000
CAST_N = 6

S = requests.Session()
S.headers.update({"User-Agent": "ShashaZaman/1.0 (https://cimaeg.github.io; github.com/cimaeg)"})
FEMALE = {"Q6581072", "Q1052281"}
ARABIC_LANGS = {"Q13955", "Q29919"}  # العربية، العربية المصرية
EGYPT = "Q79"

AR_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")

# تصنيفات ويكي بيانات/IMDb ← تصنيفات الموقع
GENRE_WD = {
    "Q130232": "دراما", "Q157443": "كوميديا", "Q842256": "غنائي", "Q1054574": "رومانسي",
    "Q959790": "جريمة", "Q2484376": "تشويق", "Q188473": "أكشن", "Q200092": "رعب",
    "Q369747": "حرب", "Q17013749": "تاريخي", "Q1146335": "تاريخي", "Q2973181": "سياسي",
    "Q93204": "وثائقي", "Q1361932": "عائلي", "Q319221": "مغامرات", "Q157394": "فانتازيا",
    "Q471839": "خيال علمي", "Q645928": "سيرة", "Q226540": "صامت", "Q185867": "جريمة",
    "Q1200678": "استعراضي", "Q20443008": "استعراضي", "Q586250": "استعراضي", "Q1135802": "كوميديا",
    "Q860626": "كوميديا", "Q248583": "رومانسي", "Q1341051": "دراما", "Q52162262": "دراما",
    "Q2421031": "كوميديا", "Q24925": "خيال علمي", "Q21401869": "دراما", "Q663106": "رومانسي",
    "Q1257444": "تشويق", "Q3072049": "تشويق", "Q20442589": "جريمة", "Q4984974": "سياسي",
    "Q622548": "دراما", "Q7712296": "تشويق", "Q1033891": "أكشن", "Q2143665": "دراما",
}
GENRE_IMDB = {
    "Drama": "دراما", "Comedy": "كوميديا", "Musical": "غنائي", "Music": "غنائي", "Romance": "رومانسي",
    "Crime": "جريمة", "Thriller": "تشويق", "Action": "أكشن", "Horror": "رعب", "War": "حرب",
    "History": "تاريخي", "Documentary": "وثائقي", "Family": "عائلي", "Adventure": "مغامرات",
    "Fantasy": "فانتازيا", "Sci-Fi": "خيال علمي", "Biography": "سيرة", "Mystery": "تشويق",
}


def sparql(q, tries=4):
    for i in range(tries):
        try:
            r = S.post("https://query.wikidata.org/sparql", data={"query": q},
                       headers={"Accept": "application/sparql-results+json"}, timeout=120)
            if r.status_code == 200:
                return r.json()["results"]["bindings"]
            print("  !", r.status_code, r.text[:200])
        except Exception as e:
            print("  !", e)
        time.sleep(8 + i * 15)
    raise SystemExit("Wikidata query failed")


def qid(v):
    return v.rsplit("/", 1)[-1]


def val(r, k):
    return r.get(k, {}).get("value")


def day(v, prec):
    if not v:
        return None
    m = re.match(r"\+?(\d{4})-(\d\d)-(\d\d)", v)
    if not m:
        return None
    p = int(prec or 0)
    if p >= 11:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    if p in (9, 10):
        return m.group(1)
    return None


def better(a, b):
    """يختار التاريخ الأدق (يوم > سنة)، وعند التساوي الأبكر."""
    if not a:
        return b
    if not b:
        return a
    if len(b) != len(a):
        return b if len(b) > len(a) else a
    return min(a, b)


def norm(s):
    s = re.sub(r"[ً-ْـ«»\"()]", "", s or "")
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه").replace("ى", "ي")
    return re.sub(r"\s+", " ", s).strip()


def clean_label(s):
    """يزيل من العنوان أو الاسم ما يضيفه ويكي بيانات للتمييز، مثل «(فيلم)» أو «(فيلم 1958)»."""
    s = re.sub(r"\s*\((?:فيلم|film|ممثل|ممثلة|مخرج)[^)]*\)\s*$", "", s or "").strip()
    return s


def slug(en, year, taken):
    s = unicodedata.normalize("NFKD", en or "").encode("ascii", "ignore").decode()
    s = re.sub(r"\(.*?\)", "", s).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:48].strip("-")
    base = f"{s}-{year}" if s else f"film-{year}"
    out, n = base, 2
    while out in taken:
        out, n = f"{base}-{n}", n + 1
    taken.add(out)
    return out


def chunks(xs, n):
    xs = list(xs)
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


# ——— ١) الأفلام ———
def fetch_films():
    q = f"""
SELECT ?f ?ar ?en ?d ?dp ?imdb ?elc ?lang ?dur ?ctry ?g WHERE {{
  ?f wdt:P495 wd:{EGYPT} ; wdt:P31/wdt:P279* wd:Q11424 .
  ?f p:P577/psv:P577 [ wikibase:timeValue ?d ; wikibase:timePrecision ?dp ] .
  OPTIONAL {{ ?f rdfs:label ?ar FILTER(LANG(?ar) = "ar") }}
  OPTIONAL {{ ?f rdfs:label ?en FILTER(LANG(?en) = "en") }}
  OPTIONAL {{ ?f wdt:P345 ?imdb }}
  OPTIONAL {{ ?f wdt:P3135 ?elc }}
  OPTIONAL {{ ?f wdt:P364 ?lang }}
  OPTIONAL {{ ?f wdt:P2047 ?dur }}
  OPTIONAL {{ ?f wdt:P495 ?ctry }}
  OPTIONAL {{ ?f wdt:P136 ?g }}
  FILTER NOT EXISTS {{ ?f wdt:P31 wd:Q24862 }}   # فيلم قصير
  FILTER NOT EXISTS {{ ?f wdt:P31 wd:Q506240 }}  # فيلم تلفزيوني
  FILTER NOT EXISTS {{ ?f wdt:P31 wd:Q93204 }}   # وثائقي
}}"""
    rows = sparql(q)
    films = {}
    for r in rows:
        k = qid(r["f"]["value"])
        f = films.setdefault(k, {"qid": k, "ar": None, "en": None, "date": None, "imdb": set(), "elc": set(),
                                 "lang": set(), "dur": None, "ctry": set(), "genre": set()})
        f["ar"] = f["ar"] or val(r, "ar")
        f["en"] = f["en"] or val(r, "en")
        f["date"] = better(f["date"], day(val(r, "d"), val(r, "dp")))
        for key, field in (("imdb", "imdb"), ("elc", "elc")):
            if val(r, key):
                f[field].add(val(r, key))
        if val(r, "lang"):
            f["lang"].add(qid(val(r, "lang")))
        if val(r, "ctry"):
            f["ctry"].add(qid(val(r, "ctry")))
        if val(r, "g"):
            f["genre"].add(qid(val(r, "g")))
        if val(r, "dur"):
            try:
                f["dur"] = f["dur"] or round(float(val(r, "dur")))
            except ValueError:
                pass
    # أقدم تاريخ عرض هو سنة الفيلم
    out = {}
    stats = collections.Counter()
    for k, f in films.items():
        if not f["date"]:
            stats["no date"] += 1
            continue
        f["year"] = int(f["date"][:4])
        if f["year"] > MAX_YEAR:
            continue
        if not f["ar"] or not re.search(r"[؀-ۿ]", f["ar"]):
            stats["no arabic title"] += 1
            continue
        # فيلم مصري: لغته عربية، أو بلا لغة مسجّلة ومصر بلده الوحيد
        if f["lang"]:
            if not (f["lang"] & ARABIC_LANGS):
                stats["not arabic"] += 1
                continue
        elif f["ctry"] - {EGYPT}:
            stats["co-production, no language"] += 1
            continue
        out[k] = f
    print("films:", len(out), dict(stats))
    return out


# ——— ٢) صنّاع كل فيلم ———
def fetch_credits(films):
    credits = collections.defaultdict(lambda: {"cast": [], "director": [], "writer": [], "producer": []})
    roles = {"P161": "cast", "P57": "director", "P58": "writer", "P162": "producer"}
    for part in chunks(films, 250):
        vals = " ".join("wd:" + k for k in part)
        rows = sparql(f"""
SELECT ?f ?prop ?p ?ord WHERE {{
  VALUES ?f {{ {vals} }}
  VALUES ?prop {{ p:P161 p:P57 p:P58 p:P162 }}
  ?f ?prop ?st . ?st ?ps ?p .
  ?pp wikibase:claim ?prop ; wikibase:statementProperty ?ps .
  OPTIONAL {{ ?st pq:P1545 ?ord }}
}}""")
        for r in rows:
            role = roles[qid(r["prop"]["value"])]
            p = r["p"]["value"]
            if not p.startswith("http://www.wikidata.org/entity/Q"):
                continue
            o = val(r, "ord")
            credits[qid(r["f"]["value"])][role].append((qid(p), int(o) if o and o.isdigit() else None))
        time.sleep(1)
    return credits


# ——— ٣) بيانات الأشخاص ———
def fetch_people(qids):
    people = {}
    for part in chunks(qids, 300):
        vals = " ".join("wd:" + k for k in part)
        rows = sparql(f"""
SELECT ?p ?ar ?sx ?b ?bp ?d ?dp ?nm WHERE {{
  VALUES ?p {{ {vals} }}
  OPTIONAL {{ ?p rdfs:label ?ar FILTER(LANG(?ar) = "ar") }}
  OPTIONAL {{ ?p wdt:P21 ?sx }}
  OPTIONAL {{ ?p wdt:P345 ?nm }}
  OPTIONAL {{ ?p p:P569/psv:P569 [ wikibase:timeValue ?b ; wikibase:timePrecision ?bp ] }}
  OPTIONAL {{ ?p p:P570/psv:P570 [ wikibase:timeValue ?d ; wikibase:timePrecision ?dp ] }}
}}""")
        for r in rows:
            k = qid(r["p"]["value"])
            p = people.setdefault(k, {"qid": k, "ar": None, "f": False, "born": None, "died": None, "nm": None})
            p["ar"] = p["ar"] or val(r, "ar")
            if val(r, "sx") and qid(val(r, "sx")) in FEMALE:
                p["f"] = True
            p["nm"] = p["nm"] or val(r, "nm")
            p["born"] = better(p["born"], day(val(r, "b"), val(r, "bp")))
            p["died"] = better(p["died"], day(val(r, "d"), val(r, "dp")))
        time.sleep(1)
    return people


def fetch_people_by_nm(nms):
    """أشخاص يذكرهم IMDb في طاقم الفيلم ولم يذكرهم ويكي بيانات: نجدهم بمعرّفهم في IMDb."""
    found = {}
    for part in chunks(nms, 300):
        vals = " ".join(f'"{n}"' for n in part)
        rows = sparql(f"""SELECT ?p ?nm WHERE {{ VALUES ?nm {{ {vals} }} ?p wdt:P345 ?nm . }}""")
        for r in rows:
            found[val(r, "nm")] = qid(r["p"]["value"])
        time.sleep(1)
    return found


# ——— ٤) ملفات IMDb ———
def imdb_stream(name):
    r = S.get(f"https://datasets.imdbws.com/{name}", stream=True, timeout=300)
    r.raise_for_status()
    r.raw.decode_content = False
    with gzip.open(r.raw, "rt", encoding="utf-8") as fp:
        next(fp)
        for line in fp:
            yield line.rstrip("\n").split("\t")


def imdb_principals(tts):
    out = collections.defaultdict(list)
    n = 0
    for tconst, ordering, nconst, cat, *_ in imdb_stream("title.principals.tsv.gz"):
        n += 1
        if tconst in tts:
            out[tconst].append((int(ordering), nconst, cat))
    print(f"IMDb principals: scanned {n:,} rows, {len(out)} films")
    return out


def imdb_basics(tts):
    out = {}
    for row in imdb_stream("title.basics.tsv.gz"):
        if row[0] in tts:
            out[row[0]] = {"type": row[1], "runtime": row[7], "genres": row[8]}
    print(f"IMDb basics: {len(out)} films")
    return out


def main():
    try:
        existing = json.load(open(FILMS, encoding="utf-8"))
    except Exception:
        existing = []
    try:
        wd = json.load(open(WD, encoding="utf-8"))
    except Exception:
        wd = {"films": {}, "people": {}}

    films = fetch_films()
    credits = fetch_credits(films)

    tts = {next(iter(sorted(f["imdb"]))) for f in films.values() if f["imdb"]}
    prin = imdb_principals(tts) if tts else {}
    basics = imdb_basics(tts) if tts else {}

    # الأفلام التي يصنّفها IMDb مسلسلًا أو حلقة أو فيلمًا قصيرًا ليست أفلامًا روائية طويلة
    drop = set()
    for k, f in films.items():
        if f["imdb"]:
            b = basics.get(next(iter(sorted(f["imdb"]))))
            if b and b["type"] not in ("movie", "tvMovie"):
                drop.add(k)
            elif b and b["runtime"].isdigit() and int(b["runtime"]) < 45:
                drop.add(k)
    for k in drop:
        films.pop(k)
    print("dropped (IMDb says short/series):", len(drop))

    pq = {p for c in credits.values() for role in c.values() for p, _ in role}
    nms = {nc for rows in prin.values() for _, nc, cat in rows if cat in ("actor", "actress", "self", "director", "writer")}
    people = fetch_people(pq)
    known_nm = {p["nm"]: k for k, p in people.items() if p["nm"]}
    extra = fetch_people_by_nm(nms - set(known_nm))
    people.update(fetch_people(set(extra.values()) - set(people)))
    known_nm = {p["nm"]: k for k, p in people.items() if p["nm"]}
    print("people:", len(people), "with Arabic name:", sum(1 for p in people.values() if p["ar"]))

    def name(k):
        p = people.get(k)
        if not p or not p["ar"] or not re.search(r"[؀-ۿ]", p["ar"]):
            return None
        return clean_label(p["ar"])

    # شهرة الممثل = عدد أفلامه في القائمة؛ نرتّب بها حين يغيب ترتيب IMDb
    fame = collections.Counter(p for c in credits.values() for p, _ in c["cast"])

    # ——— بناء السجلات ———
    by_imdb, by_qid, by_title = {}, {}, {}
    wdf = wd.get("films", {})
    for f in existing:
        i = ((f.get("ratings") or {}).get("imdb") or {}).get("id")
        if i:
            by_imdb[i] = f
        q = f.get("qid") or (wdf.get(f["id"]) or {}).get("qid")
        if q:
            by_qid[q] = f
        by_title[(norm(f["title"]), f["year"])] = f
    taken = {f["id"] for f in existing}
    curated_ids = {f["id"] for f in existing if f.get("src") != "wikidata"}

    records, used = [], set()
    people_out = wd.setdefault("people", {})
    for k, f in sorted(films.items(), key=lambda kv: (kv[1]["date"], kv[1]["ar"])):
        tt = next(iter(sorted(f["imdb"]))) if f["imdb"] else None
        title = clean_label(f["ar"])
        old = by_qid.get(k) or (by_imdb.get(tt) if tt else None) or by_title.get((norm(title), f["year"]))
        if old and old["id"] in curated_ids:
            # فيلم مكتوب يدويًا: نُكمل فقط ما ينقصه من معرّفات
            used.add(old["id"])
            r = old.setdefault("ratings", {})
            if tt and not (r.get("imdb") or {}).get("id"):
                r["imdb"] = {"id": tt}
            if f["elc"] and not (r.get("elcinema") or {}).get("id"):
                r["elcinema"] = {"id": sorted(f["elc"])[0]}
            continue
        c = credits.get(k, {"cast": [], "director": [], "writer": [], "producer": []})

        # الممثلون: ترتيب IMDb أولًا، ثم ترتيب ويكي بيانات، ثم الأشهر
        order = []
        for o, nc, cat in sorted(prin.get(tt, [])):
            if cat in ("actor", "actress") and nc in known_nm:
                order.append(known_nm[nc])
        wd_cast = sorted(c["cast"], key=lambda x: (x[1] is None, x[1] or 0, -fame[x[0]]))
        order += [p for p, _ in wd_cast]
        cast, seen = [], set()
        for p in order:
            n = name(p)
            if n and n not in seen:
                seen.add(n)
                cast.append((p, n))
            if len(cast) >= CAST_N:
                break

        def names(role, imdb_cat):
            ks = [p for p, _ in c[role]]
            ks += [known_nm[nc] for _, nc, cat in sorted(prin.get(tt, [])) if cat == imdb_cat and nc in known_nm]
            out = []
            for p in ks:
                n = name(p)
                if n and n not in out:
                    out.append((p, n))
            return out

        directors = names("director", "director")
        writers = names("writer", "writer")
        producers = names("producer", "producer")

        genre = [GENRE_WD[g] for g in sorted(f["genre"]) if g in GENRE_WD]
        if not genre and tt in basics:
            genre = [GENRE_IMDB[g] for g in basics[tt]["genres"].split(",") if g in GENRE_IMDB]
        genre = list(dict.fromkeys(genre))[:3] or ["دراما"]

        dur = f["dur"]
        if not dur and tt in basics and basics[tt]["runtime"].isdigit():
            dur = int(basics[tt]["runtime"])

        rec = old if old else {"id": slug(f["en"], f["year"], taken)}
        used.add(rec["id"])
        rec.update({
            "title": title,
            "year": f["year"],
            "director": "، ".join(n for _, n in directors[:2]) or None,
            "cast": [n for _, n in cast],
            "genre": genre,
            "writer": "، ".join(n for _, n in writers[:3]) or None,
            "producer": "، ".join(n for _, n in producers[:2]) or None,
            "duration": f"{str(dur).translate(AR_DIGITS)} دقيقة" if dur else None,
            "src": "wikidata",
            "qid": k,
        })
        if f["en"]:
            rec["title_en"] = f["en"]
        rec.setdefault("summary", "")
        rec.setdefault("poster", {"status": "generated", "url": None, "credit": None})
        r = rec.setdefault("ratings", {})
        if tt:
            r.setdefault("imdb", {})["id"] = tt
        if f["elc"]:
            r.setdefault("elcinema", {})["id"] = sorted(f["elc"])[0]
        for key in ("director", "writer", "producer", "duration"):
            if rec.get(key) is None:
                rec.pop(key, None)
        records.append(rec)

        # تواريخ الصنّاع وجنسهم لصفحات الأشخاص
        for p, n in cast + directors[:2]:
            pd = people[p]
            po = people_out.setdefault(n, {})
            if po.get("qid") and po["qid"] != p:
                continue  # اسم واحد لشخصين: نترك ما سبق
            po["qid"] = p
            for kk in ("born", "died"):
                if pd[kk]:
                    po[kk] = better(po.get(kk), pd[kk])
            if pd["f"]:
                po["f"] = True
        rel = f["date"]
        wdf.setdefault(rec["id"], {}).update({"qid": k, "released": rel})

    # الأفلام المستوردة سابقًا ولم تعد في ويكي بيانات تُحذف؛ المكتوبة يدويًا تبقى دائمًا
    final = [f for f in existing if f["id"] in curated_ids]
    final += [f for f in records if f["id"] not in curated_ids]
    final.sort(key=lambda f: (f["year"], f["title"]))

    dec = collections.Counter((f["year"] // 10) * 10 for f in final)
    print("total films:", len(final), "imported:", len(records), "curated:", len(curated_ids))
    print("by decade:", sorted(dec.items()))
    print("cast sizes:", sorted(collections.Counter(len(f.get("cast", [])) for f in records).items()))
    print("no director:", sum(1 for f in records if not f.get("director")),
          "with writer:", sum(1 for f in records if f.get("writer")),
          "imdb:", sum(1 for f in records if f["ratings"].get("imdb")),
          "elcinema:", sum(1 for f in records if f["ratings"].get("elcinema")))
    print("genres:", collections.Counter(g for f in records for g in f["genre"]).most_common())
    for f in records[::max(1, len(records) // 12)]:
        print("  sample:", json.dumps(f, ensure_ascii=False)[:400])

    if DRY:
        return
    open(FILMS, "w", encoding="utf-8").write("[\n" + ",\n".join(json.dumps(x, ensure_ascii=False) for x in final) + "\n]\n")
    wd["films"] = wdf
    json.dump(wd, open(WD, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("written")


if __name__ == "__main__":
    main()
