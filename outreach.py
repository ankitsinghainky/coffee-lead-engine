import json, pandas as pd
from extract import call

d = pd.read_excel("OrchardGate_Buyers.xlsx", sheet_name="Prospects")
d = d[d["Public email (V)"].astype(str).str.contains("@")]
top = d.sort_values("Score (/100)", ascending=False).head(5)

PROMPT = """You write first-contact emails for Orchard Gate, an Indian specialty coffee sourcing and export business (Arabica, Robusta, distinctive processed coffees, Monsooned Malabar).
Use ONLY the facts below. Do not invent facts, names, certifications or prices. If a fact is missing, leave it out.
If there is no named contact, address the sourcing team. Max 120 words. Sign off as [Name], Orchard Gate.
Return JSON with keys: subject, body, approach (person or department to contact), offering (which Orchard Gate coffee to introduce and why), research_used (list of the facts from below you used).

FACTS
Company: {company} | Country: {country} | Category: {cat}
Description: {desc}
Coffee products: {prod}
Relevance note: {why}
Contact: {dm} ({title}) | Email: {email}"""

rows = []
for _, r in top.iterrows():
    out = call(PROMPT.format(company=r["Company (V)"], country=r["Country (AI)"], cat=r["Buyer category (AI)"],
                             desc=r["Description (AI summary)"], prod=r["Coffee products (AI from site)"],
                             why=r["Why relevant (AI assumption)"], dm=r["Decision-maker (V if found)"],
                             title=r["Designation (V if found)"], email=r["Public email (V)"]))
    if not out:
        print("FAILED:", r["Company (V)"]); continue
    out["research_used"] = "; ".join(out["research_used"]) if isinstance(out.get("research_used"), list) else out.get("research_used")
    rows.append({"Company": r["Company (V)"], "Score": r["Score (/100)"], "Email": r["Public email (V)"], **out})
    print("drafted:", r["Company (V)"])

pd.DataFrame(rows).to_excel("outreach_drafts.xlsx", index=False)
print("Saved outreach_drafts.xlsx with", len(rows), "drafts")