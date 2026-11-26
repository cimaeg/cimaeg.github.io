import requests, re, html
S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36", "Accept-Language": "ar,en;q=0.8"})
def get(u):
    t = S.get(u, timeout=30).text
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<svg.*?</svg>|<head>.*?</head>", "", t, flags=re.S)
    return re.sub(r"\s+", " ", t)
def ctx(t, words, w=500):
    for k in words:
        for m in list(re.finditer(k, t))[:2]:
            print(f"--[{k}]", t[max(0, m.start()-w): m.end()+w].replace("\n"," "))
t = get("https://elcinema.com/work/1005029/")
ctx(t, ["إخراج", "تأليف", "مصر", "دقيقة", "النوع", "تاريخ العرض"], 350)
print("PERSONLINKS", re.findall(r'href="/person/(\d+)/"[^>]*>([^<]+)<', t)[:30])
t = get("https://elcinema.com/work/1005029/cast/")
ctx(t, ["إخراج", "تأليف", "تمثيل", "سيناريو"], 600)
print("CASTLINKS", re.findall(r'href="/person/(\d+)/"[^>]*>([^<]+)<', t)[:40])
t = get("https://elcinema.com/person/1049796/")
print("WORKLINKS", re.findall(r'href="/work/(\d+)/"[^>]*>([^<]+)<', t)[:60])
ctx(t, ["أحمر شفايف"], 700)
t2 = get("https://elcinema.com/person/1049796/filmography/")
print("FILMO", len(t2), re.findall(r'href="/work/(\d+)/"[^>]*>([^<]+)<', t2)[:60])
ctx(t2, ["أحمر شفايف"], 900)
