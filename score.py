import re, json, pandas as pd

QUOTA = {"USA & Canada": 25, "Europe": 30, "Japan & South Korea": 15,
         "UAE & GCC": 15, "Australia & Singapore": 15}
# Market suitability (0-100): ASSUMPTION, justify in Part E
MARKET = {"Europe": 100, "UAE & GCC": 85, "USA & Canada": 80,
          "Japan & South Korea": 80, "Australia & Singapore": 75}
W = {"specialty": .30, "india": .25, "fit": .20, "market": .15, "contact": .10}
FIT = {"Green Coffee Importer": 100, "Trading Company": 90, "Specialty Roaster": 85,
       "Private Label": 80, "Distributor": 75, "Wholesaler": 70, "Coffee Chain": 60}
SPEC_KW = ["specialty", "single origin", "single-origin", "microlot", "direct trade",
           "traceab", "sca ", "cupping", "q grader", "estate", "lot "]

c = pd.read_csv("candidates.csv").drop_duplicates("domain")
s = pd.read_csv("scraped.csv").drop_duplicates("domain")
e = pd.read_csv("extracted.csv").drop_duplicates("domain")
for col in ["company_name","city","country","buyer_category","description","coffee_products",
            "sources_origins","buys_green_coffee","mentions_india","decision_maker_name",
            "decision_maker_title","relevance_notes"]:
    if col not in e.columns: e[col] = None
df = s.merge(e, on="domain", how="inner")
df = df[(df.ai_ok == True) & (df.buyer_category.fillna("Not a buyer") != "Not a buyer")].copy()
print("After AI filter:", len(df))

# ---- Deduplication (domain, normalised name, email) ----
def norm(n):
    n = re.sub(r"[^a-z0-9 ]", " ", str(n).lower())
    n = re.sub(r"\b(coffee|coffees|roasters?|roastery|roasting|co|company|ltd|llc|inc|gmbh|pty|the|and)\b", " ", n)
    return re.sub(r"\s+", " ", n).strip()
df["name_key"] = df.company_name.fillna(df.domain).map(norm)
before = len(df)
df = df.drop_duplicates("name_key")
df["first_email"] = df.emails.fillna("").str.split(";").str[0].str.strip()
df = df[~((df.first_email != "") & df.duplicated("first_email", keep="first"))]
print(f"Dedup removed {before - len(df)} records")

# ---- Scoring ----
def blob(r):
    return " ".join(str(r[k]) for k in ["description","coffee_products","sources_origins","title","snippet"]
                    if pd.notna(r[k])).lower()

def score(r):
    b = blob(r); reasons = []
    spec = min(100, 20 * sum(k in b for k in SPEC_KW))
    if r.buyer_category in ("Specialty Roaster", "Green Coffee Importer"): spec = min(100, spec + 25)
    reasons.append(f"Specialty signals: {spec}/100")

    ind = 0
    if str(r.mentions_india).lower() == "true": ind += 45; reasons.append("site mentions India")
    if "india" in str(r.sources_origins).lower(): ind += 15
    if str(r.buys_green_coffee).lower() == "true": ind += 30; reasons.append("buys green coffee")
    try:
        if len(json.loads(r.sources_origins)) >= 3: ind += 10; reasons.append("multi-origin sourcing")
    except Exception: pass
    ind = min(100, ind)

    fit = FIT.get(r.buyer_category, 30)
    mkt = MARKET.get(r.market, 60)
    con = 0
    if r.first_email: con += 50
    if pd.notna(r.decision_maker_name): con += 30
    if pd.notna(r.linkedin) and r.linkedin: con += 10
    if pd.notna(r.phones) and r.phones: con += 10

    total = round(spec*W["specialty"] + ind*W["india"] + fit*W["fit"] + mkt*W["market"] + con*W["contact"], 1)
    return pd.Series({"score_specialty": spec, "score_india_potential": ind, "score_buyer_fit": fit,
                      "score_market": mkt, "score_contact": con, "priority_score": total,
                      "score_reason": "; ".join(reasons) + f"; category={r.buyer_category} ({fit}); market={r.market} ({mkt}); contact={con}"})

df = pd.concat([df, df.apply(score, axis=1)], axis=1)
df["priority_tier"] = pd.cut(df.priority_score, [-1, 49.9, 69.9, 101], labels=["C", "B", "A"])

# ---- Flags (missing / unverified) ----
def flags(r):
    f = []
    if not r.first_email: f.append("No public email found")
    if pd.isna(r.decision_maker_name): f.append("Decision-maker not found")
    if not (pd.notna(r.linkedin) and r.linkedin): f.append("No LinkedIn link found on site")
    if str(r.mentions_india).lower() != "true": f.append("India sourcing not confirmed (AI assumption)")
    if pd.isna(r.city): f.append("City missing")
    return "; ".join(f) if f else "None"
df["data_flags"] = df.apply(flags, axis=1)

# ---- Quota selection ----
picked = []
for m, n in QUOTA.items():
    g = df[df.market == m].sort_values("priority_score", ascending=False).head(n)
    print(f"{m}: have {len(g)} / need {n}")
    picked.append(g)
final = pd.concat(picked).sort_values("priority_score", ascending=False).reset_index(drop=True)
final.insert(0, "rank", final.index + 1)

# ---- Output: verified facts vs AI assumptions kept in separate column groups ----
out = pd.DataFrame({
    "Rank": final["rank"], "Market": final.market, "Priority": final.priority_tier,
    "Score (/100)": final.priority_score,
    "Company (V)": final.company_name.fillna(final.domain), "Website (V)": final.site_url,
    "Country (AI)": final.country, "City (AI)": final.city,
    "Buyer category (AI)": final.buyer_category, "Description (AI summary)": final.description,
    "Coffee products (AI from site)": final.coffee_products,
    "Decision-maker (V if found)": final.decision_maker_name,
    "Designation (V if found)": final.decision_maker_title,
    "Public email (V)": final.first_email.replace("", "Not found"),
    "All emails found (V)": final.emails.fillna("Not found"),
    "LinkedIn (V)": final.linkedin.fillna("Not found"),
    "Source URL (V)": final.pages.fillna("").str.split(";").str[0],
    "Why relevant (AI assumption)": final.relevance_notes,
    "Score reason": final.score_reason, "Data flags": final.data_flags,
    "Specialty /100": final.score_specialty, "India potential /100": final.score_india_potential,
    "Buyer fit /100": final.score_buyer_fit, "Market /100": final.score_market, "Contact /100": final.score_contact,
})
with pd.ExcelWriter("OrchardGate_Buyers.xlsx", engine="openpyxl") as w:
    out.to_excel(w, sheet_name="Prospects", index=False)
    out.head(20).to_excel(w, sheet_name="Top 20", index=False)
    pd.DataFrame({
        "Legend": ["(V) = taken directly from the company's public website, with source URL",
                   "(AI) = extracted or inferred by an LLM from website text; verify before use",
                   "Weights: Specialty 30%, India potential 25%, Buyer fit 20%, Market 15%, Contact 10%",
                   "Market scores are an assumption, not verified data"]}
    ).to_excel(w, sheet_name="Legend", index=False)
print("Saved OrchardGate_Buyers.xlsx with", len(out), "rows")
print(out.Priority.value_counts())