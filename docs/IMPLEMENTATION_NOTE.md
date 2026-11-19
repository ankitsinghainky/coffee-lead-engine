# Implementation Note

## 1. What exactly did I build?

An end-to-end lead-generation pipeline for a coffee-export business. Given search queries per market, it finds candidate buyers (importers, roasters, traders), scrapes their public pages, uses an LLM to extract and classify each company, removes duplicates, scores every lead with a transparent weighted framework, flags missing or unverified data, exports a prioritised Excel database, and drafts personalised outreach for the top leads.

Results: [x] qualified leads in the database against a target of 100 ([per-market counts]), [x] websites scraped, [x] skipped because their `robots.txt` disallowed automated access. Five outreach drafts were prepared for the top-ranked leads after a manual check.

## 2. Tools and technologies, and why

| Tool | Used for | Why |
|---|---|---|
| Python | Whole pipeline | Fastest to build and test; matches my existing stack |
| `ddgs` | Candidate discovery | Free, no API key, scriptable per market |
| `requests` + BeautifulSoup | Scraping | Lightweight and reliable for static about/contact pages; easy to add `robots.txt` handling |
| OpenAI `[model]` | Extraction, classification, drafts | Low cost, follows JSON-only instructions well |
| Gemini / OpenRouter | Fallback providers | Free tiers were rate-limited or retired during the build |
| pandas + openpyxl | Dedup, scoring, Excel output | Simple, inspectable tabular processing |
| FastAPI | Optional API layer | Lets a frontend trigger runs and read results |
| [Emergent] | [Frontend UI] | [Quick dashboard on top of the API] |

I chose a plain Python pipeline over n8n or Make because every step could be debugged, resumed and explained in code.

## 3. What is automated and what needs a human

**Automated:** discovery, scraping, email, LinkedIn and phone extraction, LLM extraction and
