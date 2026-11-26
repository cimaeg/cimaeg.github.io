import json, requests, time, re
f = json.load(open("data/films.json"))
q = [x["qid"] for x in f if x.get("qid")]
print("films with qid:", len(q), "of", len(f))
S = requests.Session(); S.headers.update({"User-Agent": "ShashaZaman/1.0 (https://cimaeg.github.io)", "Accept": "application/sparql-results+json"})
has = {}
for i in range(0, len(q), 300):
    vals = " ".join("wd:" + k for k in q[i:i+300])
    for k in range(4):
        r = S.post("https://query.wikidata.org/sparql", data={"query": f'SELECT ?f ?a WHERE {{ VALUES ?f {{ {vals} }} ?a schema:about ?f ; schema:isPartOf <https://ar.wikipedia.org/> }}'}, timeout=120)
        if r.ok: break
        time.sleep(20)
    for b in r.json()["results"]["bindings"]:
        has[b["f"]["value"].rsplit("/",1)[-1]] = b["a"]["value"]
print("with Arabic Wikipedia article:", len(has))
# sample plot sections
W = requests.Session(); W.headers.update({"User-Agent": "ShashaZaman/1.0 (https://cimaeg.github.io)"})
plot = 0; n = 0
for k, url in list(has.items())[:60]:
    title = requests.utils.unquote(url.rsplit("/", 1)[-1])
    r = W.get("https://ar.wikipedia.org/w/api.php", params={"action": "parse", "page": title, "prop": "sections", "format": "json"}, timeout=30).json()
    secs = [s["line"] for s in r.get("parse", {}).get("sections", [])]
    n += 1
    if any(re.search("قصة|القصة|الأحداث|ملخص|حبكة", s) for s in secs): plot += 1
    if n <= 8: print(title, secs[:8])
print(f"plot section in {plot}/{n} sampled articles")
