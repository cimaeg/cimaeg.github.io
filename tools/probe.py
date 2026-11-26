import requests, time, json
S = requests.Session(); S.headers.update({"User-Agent": "ShashaZaman/1.0 (https://cimaeg.github.io)", "Accept": "application/sparql-results+json"})
def q(s):
    for i in range(5):
        r = S.post("https://query.wikidata.org/sparql", data={"query": s}, timeout=120)
        if r.status_code == 200: return r.json()["results"]["bindings"]
        print("!", r.status_code); time.sleep(20)
    return []
def show(t, rows):
    print("==", t, len(rows))
    for r in rows[:40]: print("  ", {k: v["value"].rsplit("/",1)[-1] for k, v in r.items()})
show("lipstick label search", q('''SELECT ?f ?l ?t ?c ?d WHERE { ?f rdfs:label ?l . FILTER(LANG(?l)="ar") FILTER(STR(?l) IN ("أحمر شفايف","احمر شفايف","أحمر شفاه")) OPTIONAL{?f wdt:P31 ?t} OPTIONAL{?f wdt:P495 ?c} OPTIONAL{?f wdt:P577 ?d} }'''))
show("rihani films (P161)", q('''SELECT ?f ?l ?t ?c ?d WHERE { ?f wdt:P161 wd:Q2621467 . OPTIONAL{?f rdfs:label ?l FILTER(LANG(?l)="ar")} OPTIONAL{?f wdt:P31 ?t} OPTIONAL{?f wdt:P495 ?c} OPTIONAL{?f wdt:P577 ?d} }'''))
for name, cond in [
  ("film, arabic/egyptian lang, no P495", '?f wdt:P31 wd:Q11424 . ?f wdt:P364 ?lg . VALUES ?lg {wd:Q13955 wd:Q29919} FILTER NOT EXISTS {?f wdt:P495 ?c}'),
  ("film, has elCinema id, not P495 Egypt", '?f wdt:P31 wd:Q11424 . ?f wdt:P3135 ?e . FILTER NOT EXISTS {?f wdt:P495 wd:Q79}'),
  ("has elCinema id, not P31 film", '?f wdt:P3135 ?e . FILTER NOT EXISTS {?f wdt:P31 wd:Q11424}'),
  ("film Egypt, no date", '?f wdt:P31 wd:Q11424 ; wdt:P495 wd:Q79 . FILTER NOT EXISTS {?f wdt:P577 ?d}'),
]:
    r = q(f"SELECT (COUNT(DISTINCT ?f) AS ?n) WHERE {{ {cond} }}"); print("COUNT", name, r[0]["n"]["value"] if r else "?")
show("elCinema not P31 film: types", q('SELECT ?t (COUNT(?f) AS ?n) WHERE { ?f wdt:P3135 ?e . ?f wdt:P31 ?t . FILTER NOT EXISTS {?f wdt:P31 wd:Q11424} } GROUP BY ?t ORDER BY DESC(?n) LIMIT 10'))
