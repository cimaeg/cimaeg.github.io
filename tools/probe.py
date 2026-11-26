"""استكشاف: كم فيلمًا مصريًا حتى ٢٠٠٠ في ويكي بيانات، وما مدى اكتمال بياناتها."""
import requests, time
S = requests.Session()
S.headers.update({"User-Agent": "ShashaZaman/1.0 (https://cimaeg.github.io)", "Accept": "application/sparql-results+json"})
def q(s):
    for i in range(3):
        r = S.get("https://query.wikidata.org/sparql", params={"query": s}, timeout=120)
        if r.status_code == 200: return r.json()["results"]["bindings"]
        print("!", r.status_code, r.text[:300]); time.sleep(10)
    return []
for r in q('SELECT ?p ?l WHERE { ?p a wikibase:Property; rdfs:label ?l. FILTER(LANG(?l)="en" && CONTAINS(LCASE(?l),"elcinema")) }'):
    print("PROP", r["p"]["value"], r["l"]["value"])
base = '?f wdt:P495 wd:Q79 . ?f wdt:P31/wdt:P279* wd:Q11424 . ?f wdt:P577 ?d . FILTER(YEAR(?d) <= 2000)'
for name, extra in [("all", ""), ("imdb", "?f wdt:P345 ?i ."),
                    ("ar", '?f rdfs:label ?a . FILTER(LANG(?a)="ar")'),
                    ("director", "?f wdt:P57 ?x ."), ("cast", "?f wdt:P161 ?x ."), ("writer", "?f wdt:P58 ?x .")]:
    r = q(f"SELECT (COUNT(DISTINCT ?f) AS ?n) WHERE {{ {base} {extra} }}")
    print("COUNT", name, r[0]["n"]["value"] if r else "?")
for r in q(f"SELECT ?y (COUNT(DISTINCT ?f) AS ?n) WHERE {{ {base} BIND(FLOOR(YEAR(?d)/10)*10 AS ?y) }} GROUP BY ?y ORDER BY ?y"):
    print("DECADE", r["y"]["value"], r["n"]["value"])
for r in q(f"SELECT ?t ?tl (COUNT(DISTINCT ?f) AS ?n) WHERE {{ {base} ?f wdt:P31 ?t . ?t rdfs:label ?tl FILTER(LANG(?tl)='en') }} GROUP BY ?t ?tl ORDER BY DESC(?n) LIMIT 15"):
    print("TYPE", r["tl"]["value"], r["n"]["value"])
# أفلام بلا P31 film لكن بلد المنشأ مصر ونوعها فيلم؟ + عينة
for r in q(f'SELECT ?f ?a ?i ?d WHERE {{ {base} OPTIONAL{{?f rdfs:label ?a FILTER(LANG(?a)="ar")}} OPTIONAL{{?f wdt:P345 ?i}} }} LIMIT 15'):
    print("SAMPLE", {k: v["value"] for k, v in r.items()})
# بديل: أفلام لغتها الأصلية العربية المصرية/العربية ومنتجة في مصر عبر IMDb؟ عدد الممثلين بأسماء عربية
r = q(f'SELECT (COUNT(DISTINCT ?x) AS ?n) (COUNT(DISTINCT ?xa) AS ?na) WHERE {{ {base} ?f wdt:P161 ?x . OPTIONAL{{?x rdfs:label ?l FILTER(LANG(?l)="ar") BIND(?x AS ?xa)}} }}')
print("CASTPEOPLE", r)
