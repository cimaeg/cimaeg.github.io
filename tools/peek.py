import sys, re, html, json, requests
S = requests.Session(); S.headers.update({"User-Agent": "Mozilla/5.0 Chrome/124.0", "Accept-Language": "ar"})
cl = lambda s: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
for e in sys.argv[2].split():
    t = S.get(f"https://elcinema.com/work/{e}/", timeout=30).text
    h = re.search(r"<h1[^>]*>(.*?)</h1>", t, re.S)
    m = re.search(r'<ul class="list-separator">(.*?)</ul>', t, re.S)
    c = S.get(f"https://elcinema.com/work/{e}/cast", timeout=30).text
    secs = re.split(r'class="section-title">', c)[1:]
    crew = {cl(s.split("<span")[0]): [cl(n) for n in re.findall(r'<li><a href="/person/\d+/">([^<]+)</a></li>', s)][:5] for s in secs[:3]}
    print("PEEK", json.dumps({"e": e, "h1": cl(h.group(1)) if h else "", "info": cl(m.group(1)) if m else "", "crew": crew}, ensure_ascii=False))
W = requests.Session(); W.headers.update({"User-Agent": "ShashaZaman/1.0 (https://cimaeg.github.io)"})
qs = sys.argv[1].split()
q = "SELECT ?f ?d ?i ?il ?dt ?dir WHERE { VALUES ?f { %s } OPTIONAL{?f schema:description ?d FILTER(lang(?d)='ar')} OPTIONAL{?f wdt:P31 ?i. ?i rdfs:label ?il FILTER(lang(?il)='en')} OPTIONAL{?f wdt:P577 ?dt} OPTIONAL{?f wdt:P57/rdfs:label ?dir FILTER(lang(?dir)='ar')} }" % " ".join("wd:" + x for x in qs)
r = W.post("https://query.wikidata.org/sparql", data={"query": q}, headers={"Accept": "application/sparql-results+json"}, timeout=60).json()
for b in r["results"]["bindings"]: print("WD", json.dumps({k: v["value"] for k, v in b.items()}, ensure_ascii=False))
