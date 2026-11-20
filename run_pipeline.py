import subprocess, sys, os, time, datetime

def find(name):
    for p in (name, os.path.join("venv", name)):
        if os.path.exists(p): return p
    return None

STAGES = [
    ("Discovery (search)",           "discover_topup.py", True),   # optional, only with --discover
    ("Web scraping (robots.txt-aware)", "scrape.py",       False),
    ("AI extraction",                "extract.py",        False),
    ("Dedup + scoring + Excel",      "score.py",          False),
    ("Outreach drafts",              "outreach.py",       False),
]

use_discovery = "--discover" in sys.argv
log = open("pipeline_log.txt", "a", encoding="utf-8")
def say(msg):
    print(msg); log.write(msg + "\n"); log.flush()

say(f"\n=== Pipeline run {datetime.datetime.now():%Y-%m-%d %H:%M} ===")
for i, (label, script, optional) in enumerate(STAGES, 1):
    if optional and not use_discovery:
        say(f"[{i}/{len(STAGES)}] {label}: skipped (add --discover to run)"); continue
    path = find(script)
    if not path:
        say(f"[{i}/{len(STAGES)}] {label}: {script} NOT FOUND, stopping"); sys.exit(1)
    say(f"[{i}/{len(STAGES)}] {label} ...")
    t = time.time()
    p = subprocess.Popen([sys.executable, path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding="utf-8", errors="replace")
    for line in p.stdout:
        print("   " + line.rstrip()); log.write("   " + line)
    p.wait()
    if p.returncode != 0:
        say(f"[{i}/{len(STAGES)}] {label}: FAILED (exit {p.returncode}), stopping"); sys.exit(p.returncode)
    say(f"[{i}/{len(STAGES)}] {label}: done in {time.time()-t:.0f}s")
say("=== Pipeline complete: OrchardGate_Buyers.xlsx, outreach_drafts.xlsx, pipeline_log.txt ===")