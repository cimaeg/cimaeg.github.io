import requests, re, time, html
S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36", "Accept-Language": "ar,en;q=0.8"})
r = S.post("https://query.wikidata.org/sparql", data={"query": 'SELECT ?e WHERE { wd:Q4165427 wdt:P3136 ?e }'}, headers={"Accept": "application/sparql-results+json", "User-Agent": "ShashaZaman/1.0"}, timeout=60)
pid = r.json()["results"]["bindings"][0]["e"]["value"] if r.ok and r.json()["results"]["bindings"] else None
print("PERSON", pid)
def dump(url, n=9000):
    t = S.get(url, timeout=30); print("\n##### ", url, t.status_code, len(t.text))
    s = re.sub(r"<script.*?</script>|<style.*?</style>|<svg.*?</svg>", "", t.text, flags=re.S)
    s = re.sub(r"\s+", " ", s)
    i = s.find("<main") if "<main" in s else 0
    print(s[i:i+n])
    return t.text
dump("https://elcinema.com/work/1005029/")
dump("https://elcinema.com/work/1005029/cast/", 7000)
if pid:
    t = dump(f"https://elcinema.com/person/{pid}/filmography/", 9000)
