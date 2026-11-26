"""يجمع مواد النبذ (ملخص السينما.كوم + قصة ويكيبيديا) لأشهر الأفلام بلا نبذة. الناتج للقراءة فقط، لا يُنشر."""
import json, re, sys, time, html, requests
N = int(sys.argv[1]) if len(sys.argv) > 1 else 300
SKIP = int(sys.argv[2]) if len(sys.argv) > 2 else 0
films = [f for f in json.load(open("data/films.json")) if not f.get("summary")]
pop = lambda f: (((f.get("ratings") or {}).get("imdb") or {}).get("votes") or 0, ((f.get("ratings") or {}).get("elcinema") or {}).get("score") or 0)
films.sort(key=pop, reverse=True)
films = films[SKIP:SKIP + N]
S = requests.Session(); S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36", "Accept-Language": "ar"})
W = requests.Session(); W.headers.update({"User-Agent": "ShashaZaman/1.0 (https://cimaeg.github.io)"})
def clean(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
# روابط ويكيبيديا العربية
qids = [f["qid"] for f in films if f.get("qid")]; wiki = {}
for i in range(0, len(qids), 300):
    vals = " ".join("wd:" + q for q in qids[i:i+300])
    r = W.post("https://query.wikidata.org/sparql", data={"query": f'SELECT ?f ?a WHERE {{ VALUES ?f {{ {vals} }} ?a schema:about ?f ; schema:isPartOf <https://ar.wikipedia.org/> }}'}, headers={"Accept": "application/sparql-results+json"}, timeout=120)
    if r.ok:
        for b in r.json()["results"]["bindings"]: wiki[b["f"]["value"].rsplit("/", 1)[-1]] = requests.utils.unquote(b["a"]["value"].rsplit("/", 1)[-1])
out = []
for f in films:
    o = {"id": f["id"], "title": f["title"], "year": f["year"], "director": f.get("director"), "cast": (f.get("cast") or [])[:4], "genre": f.get("genre")}
    e = ((f.get("ratings") or {}).get("elcinema") or {}).get("id")
    if e:
        try:
            t = S.get(f"https://elcinema.com/work/{e}/", timeout=30).text
            m = re.search(r"<strong>ملخص القصة:</strong>\s*<p>(.*?)</p>", t, re.S)
            if m: o["elc"] = clean(re.sub(r"<a href='#' id='read-more'>.*?</a>", "", m.group(1)))
        except Exception as ex: print("!", ex)
        time.sleep(0.5)
    t = wiki.get(f.get("qid"))
    if t:
        try:
            r = W.get("https://ar.wikipedia.org/w/api.php", params={"action": "query", "prop": "extracts", "explaintext": 1, "titles": t, "format": "json", "redirects": 1}, timeout=30).json()
            txt = next(iter(r["query"]["pages"].values())).get("extract", "")
            m = re.search(r"==+\s*(?:القصة|قصة الفيلم|الأحداث|ملخص|ملخص القصة|الحبكة|حبكة)\s*==+\s*(.+?)(?:\n==|$)", txt, re.S)
            if m: o["wiki"] = re.sub(r"\s+", " ", m.group(1)).strip()[:900]
            o["wiki_title"] = t
        except Exception as ex: print("!", ex)
    out.append(o)
json.dump(out, open("sources.json", "w"), ensure_ascii=False, indent=0)
print("films:", len(out), "elc:", sum(1 for o in out if o.get("elc")), "wiki:", sum(1 for o in out if o.get("wiki")), "none:", sum(1 for o in out if not o.get("elc") and not o.get("wiki")))
