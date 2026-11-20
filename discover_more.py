import time, tldextract, pandas as pd
from ddgs import DDGS

MORE = {
    "Japan & South Korea": [
        ("specialty coffee roaster Tokyo Japan wholesale", "jp-jp"),
        ("green coffee importer Japan", "jp-jp"),
        ("コーヒー生豆 輸入 商社", "jp-jp"),
        ("スペシャルティコーヒー 焙煎 卸", "jp-jp"),
        ("コーヒー豆 卸売 業務用", "jp-jp"),
        ("스페셜티 커피 로스터리 도매", "kr-kr"),
        ("생두 수입 업체", "kr-kr"),
        ("coffee roaster Seoul Korea wholesale beans", "kr-kr"),
        ("coffee importer Korea green beans", "kr-kr"),
    ],
    "USA & Canada": [
        ("specialty green coffee importer United States", "us-en"),
        ("coffee roaster wholesale program Canada", "ca-en"),
        ("private label coffee roaster USA", "us-en"),
    ],
    "Australia & Singapore": [
        ("coffee roaster wholesale Melbourne Sydney", "au-en"),
        ("green bean importer Australia", "au-en"),
        ("specialty coffee roaster Singapore wholesale", "sg-en"),
    ],
    "UAE & GCC": [
        ("coffee roaster Abu Dhabi wholesale", "xa-en"),
        ("specialty coffee roaster Riyadh Jeddah", "xa-en"),
        ("coffee trading company Dubai green coffee", "xa-en"),
    ],
}
BLOCK = {"facebook","instagram","linkedin","yelp","tripadvisor","wikipedia","youtube","reddit",
         "amazon","pinterest","medium","twitter","x","tiktok","indeed","glassdoor","eventbrite",
         "forbes","timeout","cntraveler","rakuten","naver","tistory","note","ameblo","google"}

df = pd.read_csv("candidates.csv")
seen = set(df.domain)
new = []
with DDGS() as d:
    for market, qs in MORE.items():
        got = 0
        for q, region in qs:
            try:
                res = d.text(q, region=region, max_results=20)
            except Exception as e:
                print("fail", q, e); time.sleep(5); continue
            for r in res:
                ext = tldextract.extract(r["href"])
                dom = f"{ext.domain}.{ext.suffix}"
                if ext.domain in BLOCK or dom in seen: continue
                seen.add(dom)
                new.append({"market": market, "query": q, "domain": dom,
                            "url": r["href"], "title": r["title"], "snippet": r["body"]})
                got += 1
            time.sleep(2)
        print(market, "new:", got)

pd.concat([df, pd.DataFrame(new)]).to_csv("candidates.csv", index=False, encoding="utf-8")
print("Total candidates now:", len(df) + len(new))