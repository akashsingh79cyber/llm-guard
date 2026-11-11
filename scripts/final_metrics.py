import json
from pathlib import Path


def load(p):
    f = Path(p)
    return json.loads(f.read_text()) if f.exists() else {}


rt = load("reports/redteam_report.json")
before = load("reports/redteam_round2_before.json")
lat = load("reports/latency_report.json")
st = load("reports/system_test.json")

print("=" * 56)
print("LLM-GUARD: FINAL METRICS")
print("=" * 56)
if before:
    print(f"Red team block rate (before tuning) : {before.get('block_rate_pct')} %")
print(f"Red team block rate (final)         : {rt.get('block_rate_pct')} %")
print(f"False block rate (final)            : {rt.get('false_block_rate_pct')} %")
print(f"Attacks tested / blocked            : {rt.get('attacks')} / {rt.get('blocked')}")
print("Category-wise block rate:")
for c, v in rt.get("category_rates", {}).items():
    print(f"   {c:<18}{v:>6} %")
if lat:
    g = lat.get("guard_overhead_ms", {})
    print(f"Guard overhead (avg / p95)          : {g.get('avg')} / {g.get('p95')} ms")
if st:
    print(f"System tests passed                 : {st['passed']}/{st['total']}")
print("=" * 56)