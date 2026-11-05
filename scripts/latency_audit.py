import json
import statistics
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000"
LAT = Path("logs/latency.jsonl")
prompts = [
    "What is the capital of France?",
    "Explain how photosynthesis works in simple words.",
    "Write a short email about project management.",
    "Give me three tips about healthy eating.",
    "My email is ramesh@gmail.com, please summarize cloud computing.",
]

with httpx.Client(timeout=30) as c:
    tok = c.post(
        BASE + "/auth/login", json={"username": "akash", "password": "employee123"}
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    LAT.parent.mkdir(exist_ok=True)
    if LAT.exists():
        LAT.unlink()
    N = 100
    for i in range(N):
        c.post(
            BASE + "/v1/chat/completions",
            headers=h,
            json={"model": "mock", "messages": [{"role": "user", "content": prompts[i % len(prompts)]}]},
        )

rows = [json.loads(x) for x in LAT.read_text().splitlines()]
rows = rows[5:]  # warm-up hata do
keys = ["rules_ms", "classifier_ms", "dlp_ms", "llm_ms", "output_ms", "guard_overhead_ms", "total_ms"]

print("=" * 60)
print(f"LATENCY AUDIT ({len(rows)} requests, warm-up hata ke)")
print("=" * 60)
print(f"{'Stage':<20}{'Avg':>9}{'p95':>9}{'Max':>9}  (ms)")
summary = {}
for k in keys:
    vals = sorted(r[k] for r in rows if k in r)
    avg = statistics.mean(vals)
    p95 = vals[int(len(vals) * 0.95) - 1]
    summary[k] = {"avg": round(avg, 2), "p95": round(p95, 2), "max": round(max(vals), 2)}
    print(f"{k:<20}{avg:>9.2f}{p95:>9.2f}{max(vals):>9.2f}")

pct = 100 * summary["guard_overhead_ms"]["avg"] / summary["total_ms"]["avg"]
print(f"\nGuard overhead (rules+classifier+DLP+output): {summary['guard_overhead_ms']['avg']:.1f} ms avg")
print(f"Share of total request time: {pct:.0f}%")
print("Note: llm_ms Mock LLM ka time hai. Real LLM me ye 500-3000 ms hota hai,")
print("isliye guard ka overhead real me total ka bahut chhota hissa hoga.")

Path("reports").mkdir(exist_ok=True)
Path("reports/latency_report.json").write_text(json.dumps(summary, indent=2))
print("\nSaved: reports/latency_report.json")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    stages = ["rules_ms", "classifier_ms", "dlp_ms", "llm_ms", "output_ms"]
    plt.figure(figsize=(8, 4))
    plt.bar([s.replace("_ms", "") for s in stages], [summary[s]["avg"] for s in stages],
            color=["#4c78a8", "#e45756", "#54a24b", "#9d9d9d", "#f58518"])
    plt.ylabel("Average time (ms)")
    plt.title("LLM-Guard latency per stage")
    plt.tight_layout()
    plt.savefig("reports/latency_graph.png", dpi=120)
    print("Saved: reports/latency_graph.png")
except Exception as e:
    print("Graph skipped (matplotlib nahi):", type(e).__name__)