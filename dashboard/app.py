import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "logs" / "guard.jsonl"
LAT = ROOT / "logs" / "latency.jsonl"

st.set_page_config(page_title="LLM-Guard | SOC", page_icon="🛡️", layout="wide")

CYAN, RED, GREEN, AMBER, PURPLE = "#00e5ff", "#ff2e63", "#00ff9c", "#ffb703", "#9d4edd"

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@400;600&display=swap');
.stApp {{
  background: radial-gradient(1200px 600px at 10% -10%, #0b2a3a 0%, transparent 60%),
              radial-gradient(900px 500px at 100% 0%, #2a0b3a 0%, transparent 55%),
              #05070d;
  color: #d6e4f0; font-family: 'Rajdhani', sans-serif;
}}
header, footer, #MainMenu {{visibility: hidden;}}
.block-container {{padding-top: 1.2rem; max-width: 1500px;}}
.hero {{
  padding: 22px 28px; border-radius: 16px; margin-bottom: 18px;
  background: linear-gradient(120deg, rgba(0,229,255,.10), rgba(157,78,221,.10));
  border: 1px solid rgba(0,229,255,.35);
  box-shadow: 0 0 30px rgba(0,229,255,.15), inset 0 0 30px rgba(0,229,255,.05);
}}
.hero h1 {{
  font-family: 'Orbitron', sans-serif; font-weight: 900; letter-spacing: 4px; margin: 0;
  font-size: 2.2rem; color: {CYAN}; text-shadow: 0 0 18px {CYAN};
}}
.hero p {{margin: 4px 0 0 0; color: #8fb3c9; letter-spacing: 2px; font-size: 1rem;}}
.pulse {{display:inline-block; width:10px; height:10px; border-radius:50%;
  background:{GREEN}; box-shadow:0 0 12px {GREEN}; margin-right:8px; animation: p 1.4s infinite;}}
@keyframes p {{0%{{opacity:1}} 50%{{opacity:.25}} 100%{{opacity:1}}}}
.kpi {{
  border-radius: 14px; padding: 16px 18px; background: rgba(10,18,30,.75);
  border: 1px solid var(--c); box-shadow: 0 0 18px var(--g), inset 0 0 22px rgba(255,255,255,.02);
}}
.kpi .l {{font-size: .85rem; letter-spacing: 3px; color: #8fb3c9; text-transform: uppercase;}}
.kpi .v {{font-family:'Orbitron',sans-serif; font-size: 2.1rem; font-weight: 700;
  color: var(--c); text-shadow: 0 0 14px var(--c);}}
.kpi .s {{font-size: .85rem; color: #6f8ea3;}}
.sec {{font-family:'Orbitron',sans-serif; letter-spacing:3px; color:{CYAN};
  font-size:1rem; margin: 18px 0 6px 0; text-shadow: 0 0 10px rgba(0,229,255,.6);}}
.feed {{
  background: rgba(8,14,24,.8); border: 1px solid rgba(255,46,99,.35); border-radius: 12px;
  padding: 10px 14px; max-height: 360px; overflow-y: auto;
  box-shadow: 0 0 22px rgba(255,46,99,.12);
}}
.row {{border-left: 3px solid {RED}; padding: 6px 10px; margin: 6px 0;
  background: rgba(255,46,99,.06); border-radius: 4px; font-size: .92rem;}}
.row .t {{color:#6f8ea3; font-size:.78rem;}}
.row .r {{color:{AMBER}; font-weight:600;}}
.row .p {{color:#cfe3f1;}}
[data-testid="stSidebar"] {{background:#070b14; border-right:1px solid rgba(0,229,255,.2);}}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=3)
def load(path):
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    return pd.DataFrame(rows)


def kpi(col, label, value, sub, color, glow):
    col.markdown(
        f'<div class="kpi" style="--c:{color};--g:{glow}"><div class="l">{label}</div>'
        f'<div class="v">{value}</div><div class="s">{sub}</div></div>',
        unsafe_allow_html=True,
    )


def style_fig(fig, h=320):
    fig.update_layout(
        height=h, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#b9d3e3", family="Rajdhani"), margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor="rgba(0,229,255,.08)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(0,229,255,.08)", zeroline=False)
    return fig


st.markdown(
    '<div class="hero"><h1>🛡️ LLM-GUARD // THREAT OPERATIONS</h1>'
    '<p><span class="pulse"></span>GENERATIVE AI PROMPT FIREWALL &nbsp;|&nbsp; LIVE SECURITY MONITOR</p></div>',
    unsafe_allow_html=True,
)

df = load(LOG)
import time as _t
st.sidebar.toggle("Auto-refresh (5s)", value=False, key="auto")
st.sidebar.caption(f"Last updated: {_t.strftime('%H:%M:%S')}")

if df.empty:
    st.warning("No telemetry yet. Proxy chalao aur red team script run karo.")
    st.stop()

df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

st.sidebar.markdown("### ⚙️ CONTROLS")
events = sorted(df["event"].dropna().unique())
users = sorted(df["user_id"].dropna().unique())
sel_e = st.sidebar.multiselect("Event type", events, default=events)
sel_u = st.sidebar.multiselect("User", users, default=users)
if st.sidebar.button("🔄 Refresh now"):
    st.cache_data.clear()
    st.rerun()

f = df[df["event"].isin(sel_e) & df["user_id"].isin(sel_u)]
bl = f[f["event"] == "BLOCKED"]

blocked = int((df["event"] == "BLOCKED").sum())
allowed = int((df["event"] == "ALLOWED").sum())
total = blocked + allowed
rate = 100 * blocked / total if total else 0
dlp = int((df["event"] == "DLP_MASKED").sum())
denied = int(df["event"].isin(["AUTH_FAILED", "LOGIN_FAILED", "ACCESS_DENIED"]).sum())

c = st.columns(5)
kpi(c[0], "Total requests", total, "all traffic", CYAN, "rgba(0,229,255,.25)")
kpi(c[1], "Threats blocked", blocked, f"{rate:.0f}% of traffic", RED, "rgba(255,46,99,.3)")
kpi(c[2], "Allowed", allowed, "clean prompts", GREEN, "rgba(0,255,156,.25)")
kpi(c[3], "DLP masked", dlp, "PII protected", AMBER, "rgba(255,183,3,.25)")
kpi(c[4], "Access denied", denied, "auth / rbac", PURPLE, "rgba(157,78,221,.3)")

l, r = st.columns([1, 1])
with l:
    st.markdown('<div class="sec">▍ THREAT VECTORS (BY RULE)</div>', unsafe_allow_html=True)
    if bl.empty:
        st.info("No blocked events.")
    else:
        vc = bl["rule"].value_counts().reset_index()
        vc.columns = ["rule", "count"]
        fig = px.pie(vc, names="rule", values="count", hole=0.62,
                     color_discrete_sequence=[RED, CYAN, AMBER, PURPLE, GREEN])
        fig.update_traces(textinfo="label+value", marker=dict(line=dict(color="#05070d", width=3)))
        st.plotly_chart(style_fig(fig), use_container_width=True)
with r:
    st.markdown('<div class="sec">▍ TOP ATTACKERS (BY USER)</div>', unsafe_allow_html=True)
    if bl.empty:
        st.info("No blocked events.")
    else:
        uc = bl["user_id"].value_counts().reset_index()
        uc.columns = ["user", "blocks"]
        fig = px.bar(uc, x="blocks", y="user", orientation="h", color="blocks",
                     color_continuous_scale=[[0, PURPLE], [1, RED]])
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(style_fig(fig), use_container_width=True)

st.markdown('<div class="sec">▍ ACTIVITY TIMELINE</div>', unsafe_allow_html=True)
ts = f.dropna(subset=["timestamp"]).set_index("timestamp")
if not ts.empty:
    pm = ts.groupby([pd.Grouper(freq="1min"), "event"]).size().reset_index(name="n")
    cmap = {"BLOCKED": RED, "ALLOWED": GREEN, "DLP_MASKED": AMBER, "OUTPUT_REDACTED": PURPLE}
    fig = px.area(pm, x="timestamp", y="n", color="event", color_discrete_map=cmap)
    st.plotly_chart(style_fig(fig, 300), use_container_width=True)

a, b = st.columns([1.1, 0.9])
with a:
    st.markdown('<div class="sec">▍ LIVE THREAT FEED</div>', unsafe_allow_html=True)
    feed = bl.sort_values("timestamp", ascending=False).head(25)
    html = '<div class="feed">'
    if feed.empty:
        html += '<div class="row">No threats detected.</div>'
    for _, x in feed.iterrows():
        t = x["timestamp"].strftime("%H:%M:%S") if pd.notna(x["timestamp"]) else "--"
        sc = f" | score {x['score']}" if pd.notna(x.get("score")) else ""
        pr = str(x.get("prompt", ""))[:110].replace("<", "&lt;")
        html += (f'<div class="row"><span class="t">{t} · {x["user_id"]}</span> '
                 f'<span class="r">[{x["rule"]}]{sc}</span><br><span class="p">{pr}</span></div>')
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
with b:
    st.markdown('<div class="sec">▍ DETECTION CONFIDENCE</div>', unsafe_allow_html=True)
    sc = bl["score"].dropna() if "score" in bl.columns else pd.Series(dtype=float)
    if sc.empty:
        st.info("No ML scores yet.")
    else:
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=float(sc.mean()) * 100,
            number={"suffix": "%", "font": {"color": CYAN}},
            title={"text": "Avg ML attack score"},
            gauge={"axis": {"range": [0, 100]}, "bar": {"color": RED},
                   "bgcolor": "rgba(0,0,0,0)",
                   "steps": [{"range": [0, 50], "color": "rgba(0,255,156,.15)"},
                             {"range": [50, 85], "color": "rgba(255,183,3,.15)"},
                             {"range": [85, 100], "color": "rgba(255,46,99,.2)"}]}))
        st.plotly_chart(style_fig(fig, 340), use_container_width=True)

st.markdown('<div class="sec">▍ PIPELINE LATENCY (MS PER STAGE)</div>', unsafe_allow_html=True)
lat = load(LAT)
if lat.empty:
    st.info("Run: python scripts/latency_audit.py")
else:
    cols = [x for x in ["rules_ms", "classifier_ms", "dlp_ms", "output_ms", "llm_ms"] if x in lat.columns]
    m = lat[cols].mean().reset_index()
    m.columns = ["stage", "ms"]
    m["stage"] = m["stage"].str.replace("_ms", "")
    fig = px.bar(m, x="stage", y="ms", color="stage",
                 color_discrete_sequence=[CYAN, RED, GREEN, AMBER, "#6c7a89"])
    fig.update_layout(showlegend=False)
    st.plotly_chart(style_fig(fig, 280), use_container_width=True)
    if "guard_overhead_ms" in lat.columns:
        st.caption(f"Guard overhead avg: {lat['guard_overhead_ms'].mean():.1f} ms over {len(lat)} requests")

with st.expander("📋 Raw blocked events"):
    cols = [x for x in ["timestamp", "user_id", "rule", "score", "reason", "prompt"] if x in bl.columns]
    st.dataframe(bl.sort_values("timestamp", ascending=False)[cols], use_container_width=True)

if st.session_state.get("auto"):
    _t.sleep(5)
    st.cache_data.clear()
    st.rerun()