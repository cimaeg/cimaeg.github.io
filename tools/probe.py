import requests, re
S = requests.Session(); S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36", "Accept-Language": "ar"})
for u in ["https://elcinema.com/work/1005029/", "https://elcinema.com/work/1003847/", "https://elcinema.com/work/1003847/story/"]:
    r = S.get(u, timeout=30); t = re.sub(r"<script.*?</script>|<style.*?</style>|<svg.*?</svg>|<head>.*?</head>", "", r.text, flags=re.S); t = re.sub(r"\s+", " ", t)
    print("####", u, r.status_code)
    for k in ["ملخص", "القصة", "/story", "قصة الفيلم"]:
        for m in list(re.finditer(k, t))[:2]:
            print(f"--[{k}]", t[max(0, m.start()-300): m.end()+700])
