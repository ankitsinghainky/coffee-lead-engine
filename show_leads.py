import pandas as pd

names = ["Attesa", "Garbin", "Bijdendijk", "Royal Coffee", "Gulf Coffee",
         "Origin Bridge", "Noordpoort", "InterAmerican", "Leelaprasad"]
d = pd.read_excel("OrchardGate_Buyers.xlsx")
s = pd.read_csv("scraped.csv")

with open("leads_dump.txt", "w", encoding="utf-8") as f:
    for n in names:
        m = d[d["Company (V)"].str.contains(n, case=False, na=False)]
        if m.empty:
            continue
        r = m.iloc[0]
        t = s[s.site_url == r["Website (V)"]]
        text = str(t.text.iloc[0])[:1800] if len(t) else ""
        f.write("=" * 70 + "\n")
        for col in ["Company (V)", "Market", "City (AI)", "Country (AI)", "Website (V)",
                    "Buyer category (AI)", "Description (AI summary)",
                    "Coffee products (AI from site)", "Why relevant (AI assumption)",
                    "Decision-maker (V if found)", "Designation (V if found)",
                    "Public email (V)", "All emails found (V)", "LinkedIn (V)",
                    "Source URL (V)", "Data flags"]:
            f.write(f"{col}: {r[col]}\n")
        f.write(f"SITE TEXT: {text}\n")
print("Saved leads_dump.txt")