"""يجلب من ويكي بيانات تواريخ ميلاد ووفاة صنّاع الأفلام في الأرشيف، وتاريخ العرض الأول لكل فيلم.
يربط الأفلام عن طريق معرّف IMDb، فلا يعتمد على تشابه الأسماء في البحث. الناتج: data/wikidata.json"""
import json, re, sys, time, datetime
import requests

FILMS = "data/films.json"
OUT = "data/wikidata.json"
S = requests.Session()
S.headers.update({"User-Agent": "ShashaZaman/1.0 (https://cimaeg.github.io; github.com/cimaeg)", "Accept": "application/sparql-results+json"})

FEMALE = {"Q6581072", "Q1052281"}  # أنثى في ويكي بيانات (P21)

def norm(s):
    s = re.sub(r"[ً-ْـ«»\"()]", "", s or "")
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه").replace("ى", "ي")
    return re.sub(r"\s+", " ", s).strip()

def clean(name):
    return re.sub(r"\s*\(.*?\)", "", name).strip()

def day(v, prec):
    if not v:
        return None
    m = re.match(r"\+?(\d{4})-(\d\d)-(\d\d)", v)
    if not m:
        return None
    p = int(prec or 0)
    if p >= 11:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    if p == 9 or p == 10:
        return m.group(1)
    return None

def sparql(q):
    for i in range(4):
        try:
            r = S.get("https://query.wikidata.org/sparql", params={"query": q}, timeout=90)
            if r.status_code == 200:
                return r.json()["results"]["bindings"]
            print("  !", r.status_code, r.text[:200])
        except Exception as e:
            print("  !", e)
        time.sleep(5 + i * 10)
    return None

def main():
    films = json.load(open(FILMS, encoding="utf-8"))
    by_imdb = {f["ratings"]["imdb"]["id"]: f for f in films if f.get("ratings", {}).get("imdb", {}).get("id")}
    try:
        old = json.load(open(OUT, encoding="utf-8"))
    except Exception:
        old = {"films": {}, "people": {}}
    out = {"films": dict(old.get("films", {})), "people": dict(old.get("people", {}))}

    values = " ".join(f'"{i}"' for i in by_imdb)
    q = f"""
SELECT ?imdb ?film ?rd ?rdp ?p ?label ?sx ?b ?bp ?d ?dp WHERE {{
  VALUES ?imdb {{ {values} }}
  ?film wdt:P345 ?imdb .
  OPTIONAL {{ ?film p:P577/psv:P577 [ wikibase:timeValue ?rd ; wikibase:timePrecision ?rdp ] }}
  OPTIONAL {{
    {{ ?film wdt:P161 ?p }} UNION {{ ?film wdt:P57 ?p }} UNION {{ ?film wdt:P58 ?p }}
    ?p rdfs:label ?label FILTER(LANG(?label) = "ar")
    OPTIONAL {{ ?p wdt:P21 ?sx }}
    OPTIONAL {{ ?p p:P569/psv:P569 [ wikibase:timeValue ?b ; wikibase:timePrecision ?bp ] }}
    OPTIONAL {{ ?p p:P570/psv:P570 [ wikibase:timeValue ?d ; wikibase:timePrecision ?dp ] }}
  }}
}}"""
    rows = sparql(q)
    if rows is None:
        print("Wikidata query failed; keeping old data")
        return
    print(f"{len(rows)} rows")

    # candidate people per film (Wikidata label -> data)
    cand = {}
    for r in rows:
        f = by_imdb.get(r["imdb"]["value"])
        if not f:
            continue
        qid = r["film"]["value"].rsplit("/", 1)[-1]
        rel = day(r.get("rd", {}).get("value"), r.get("rdp", {}).get("value"))
        fo = out["films"].setdefault(f["id"], {})
        fo["qid"] = qid
        if rel and (not fo.get("released") or len(rel) > len(fo["released"]) or (len(rel) == len(fo["released"]) and rel < fo["released"])):
            fo["released"] = rel
        if "p" in r:
            pq = r["p"]["value"].rsplit("/", 1)[-1]
            c = cand.setdefault(f["id"], {}).setdefault(pq, {"label": r["label"]["value"], "born": None, "died": None, "f": False})
            if r.get("sx", {}).get("value", "").rsplit("/", 1)[-1] in FEMALE:
                c["f"] = True
            b = day(r.get("b", {}).get("value"), r.get("bp", {}).get("value"))
            d = day(r.get("d", {}).get("value"), r.get("dp", {}).get("value"))
            if b and (not c["born"] or len(b) > len(c["born"])):
                c["born"] = b
            if d and (not c["died"] or len(d) > len(c["died"])):
                c["died"] = d

    # match our names to the people Wikidata lists for the same film
    unmatched = []
    for f in films:
        names = [clean(n) for n in f.get("cast", [])] + ([clean(f["director"])] if f.get("director") else [])
        people = cand.get(f["id"], {})
        for name in names:
            nn = norm(name)
            hit = None
            for pq, c in people.items():
                cl = norm(c["label"])
                if cl == nn or (len(nn) > 6 and (nn in cl or cl in nn)):
                    hit = (pq, c)
                    break
            if hit:
                pq, c = hit
                po = out["people"].setdefault(name, {})
                po["qid"] = pq
                for k in ("born", "died"):
                    if c[k]:
                        po[k] = c[k]
                if c["f"]:
                    po["f"] = True
                else:
                    po.pop("f", None)
            elif name not in out["people"]:
                unmatched.append(f"{name} ({f['title']})")
    # الأسماء التي لم تُذكر في صفحة الفيلم على ويكي بيانات: نبحث عنها بالاسم العربي بين أهل السينما
    names = sorted({u.rsplit(" (", 1)[0] for u in unmatched})
    if names:
        vals = " ".join('"' + n.replace('"', "") + '"@ar' for n in names)
        q2 = f"""
SELECT ?label ?p ?sx ?b ?bp ?d ?dp WHERE {{
  VALUES ?label {{ {vals} }}
  ?p rdfs:label ?label ; wdt:P31 wd:Q5 .
  ?p wdt:P106 ?occ . VALUES ?occ {{ wd:Q33999 wd:Q10800557 wd:Q2526255 wd:Q28389 wd:Q2405480 wd:Q177220 wd:Q3282637 wd:Q10798782 wd:Q2259451 }}
  OPTIONAL {{ ?p wdt:P21 ?sx }}
  OPTIONAL {{ ?p p:P569/psv:P569 [ wikibase:timeValue ?b ; wikibase:timePrecision ?bp ] }}
  OPTIONAL {{ ?p p:P570/psv:P570 [ wikibase:timeValue ?d ; wikibase:timePrecision ?dp ] }}
}}"""
        rows2 = sparql(q2) or []
        found = {}
        for r in rows2:
            n = r["label"]["value"]
            pq = r["p"]["value"].rsplit("/", 1)[-1]
            c = found.setdefault(n, {}).setdefault(pq, {"born": None, "died": None, "f": False})
            if r.get("sx", {}).get("value", "").rsplit("/", 1)[-1] in FEMALE:
                c["f"] = True
            b = day(r.get("b", {}).get("value"), r.get("bp", {}).get("value"))
            d = day(r.get("d", {}).get("value"), r.get("dp", {}).get("value"))
            if b and (not c["born"] or len(b) > len(c["born"])):
                c["born"] = b
            if d and (not c["died"] or len(d) > len(c["died"])):
                c["died"] = d
        still = []
        for n in names:
            opts = found.get(n, {})
            if len(opts) == 1:
                pq, c = next(iter(opts.items()))
                po = out["people"].setdefault(n, {})
                po["qid"] = pq
                for k in ("born", "died"):
                    if c[k]:
                        po[k] = c[k]
                if c["f"]:
                    po["f"] = True
                else:
                    po.pop("f", None)
            else:
                still.append(n + (f" [{len(opts)} نتائج]" if opts else ""))
        if still:
            print("not matched:", "، ".join(still))

    # الجنس لكل من له معرّف في ويكي بيانات (لتأنيث العبارات: وُلدت، ممثلة…)
    qids = {v["qid"]: n for n, v in out["people"].items() if v.get("qid")}
    if qids:
        rows3 = sparql("SELECT ?p ?sx WHERE { VALUES ?p { " + " ".join("wd:" + q for q in qids) + " } ?p wdt:P21 ?sx }")
        if rows3 is not None:
            fem = {r["p"]["value"].rsplit("/", 1)[-1] for r in rows3 if r["sx"]["value"].rsplit("/", 1)[-1] in FEMALE}
            for q, n in qids.items():
                if q in fem:
                    out["people"][n]["f"] = True
                else:
                    out["people"][n].pop("f", None)

    out["updated"] = datetime.date.today().isoformat()
    text = json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    try:
        before = open(OUT, encoding="utf-8").read()
    except Exception:
        before = ""
    strip = lambda t: re.sub(r'"updated": "[^"]*"', "", t)
    if strip(text) != strip(before):
        open(OUT, "w", encoding="utf-8").write(text)
        print("updated", len(out["people"]), "people,", len(out["films"]), "films")
    else:
        print("no changes")

if __name__ == "__main__":
    main()
