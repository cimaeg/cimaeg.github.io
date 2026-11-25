"""يجلب من ويكي بيانات تواريخ ميلاد ووفاة صنّاع الأفلام في الأرشيف، وتاريخ العرض الأول لكل فيلم.
يربط الأفلام عن طريق معرّف IMDb، فلا يعتمد على تشابه الأسماء في البحث. الناتج: data/wikidata.json"""
import json, re, sys, time, datetime
import requests

FILMS = "data/films.json"
OUT = "data/wikidata.json"
S = requests.Session()
S.headers.update({"User-Agent": "ShashaZaman/1.0 (https://cimaeg.github.io; github.com/cimaeg)", "Accept": "application/sparql-results+json"})

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
SELECT ?imdb ?film ?rd ?rdp ?p ?label ?b ?bp ?d ?dp WHERE {{
  VALUES ?imdb {{ {values} }}
  ?film wdt:P345 ?imdb .
  OPTIONAL {{ ?film p:P577/psv:P577 [ wikibase:timeValue ?rd ; wikibase:timePrecision ?rdp ] }}
  OPTIONAL {{
    {{ ?film wdt:P161 ?p }} UNION {{ ?film wdt:P57 ?p }} UNION {{ ?film wdt:P58 ?p }}
    ?p rdfs:label ?label FILTER(LANG(?label) = "ar")
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
            c = cand.setdefault(f["id"], {}).setdefault(pq, {"label": r["label"]["value"], "born": None, "died": None})
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
            elif name not in out["people"]:
                unmatched.append(f"{name} ({f['title']})")
    if unmatched:
        print("not matched:", "، ".join(unmatched))

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
