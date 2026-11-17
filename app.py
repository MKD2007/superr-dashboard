"""Players under pressure - SupeRR Selector S2 dashboard.
Reads precomputed results from ./data (no model re-run). Start with:  streamlit run app.py
"""
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "data"
st.set_page_config(page_title="Players under pressure", page_icon="🏏", layout="wide")

BLUE, ORANGE, GREY = "#1F4E9C", "#D9622B", "#9AA3AF"

@st.cache_data
def load():
    p = pd.read_csv(DATA / "players.csv")
    for c in ("pressure_score", "normal_score", "change_vs_baseline"):
        p[c + "_100"] = p[c] * 100          # per 100 balls
    sens = {"Batter": pd.read_csv(DATA / "sens_bat.csv"), "Bowler": pd.read_csv(DATA / "sens_bwl.csv")}
    return p, sens

players, sens = load()

with st.sidebar:
    st.title("🏏 Under pressure")
    page = st.radio("Page", ["Final top 10", "Pressure vs normal", "Player explorer", "Stability", "Method"])
    role = st.radio("Players", ["Batter", "Bowler"], horizontal=True)

color = BLUE if role == "Batter" else ORANGE
df = players[players.role == role].copy()
rate_name = "SR" if role == "Batter" else "Econ"
bpe_name = "Balls/dismissal" if role == "Batter" else "Balls/wicket"
rfmt = "{:.1f}" if role == "Batter" else "{:.2f}"
top = df[df.final_rank.notna()].sort_values("final_rank")

st.title(f"Top {role.lower()}s under pressure")
st.caption("788 IPL and T20I matches from 2022. Scores are shrunk, context-adjusted runs above the league average "
           "per 100 balls in the same situation. Tie-break: players within 0.05 composite points are ordered by top-10 share.")

if page == "Final top 10":
    c1, c2, c3 = st.columns(3)
    c1.metric("Eligible players", len(df))
    c2.metric("Leader", top.iloc[0].player)
    c3.metric("Top-10 share of leader", f"{top.iloc[0].top10_share:.0%}")
    t = pd.DataFrame({
        "Rank": top.final_rank.astype(int), "Player": top.player,
        "Press. balls": top.pressure_balls.astype(int), "Matches": top.matches.astype(int),
        f"{rate_name}, pressure": top.rate_p.map(rfmt.format), f"{rate_name}, normal": top.rate_np.map(rfmt.format),
        f"{bpe_name}, pressure": top.bpe_p.round(1), f"{bpe_name}, normal": top.bpe_np.round(1),
        "Pressure score": top.pressure_score_100.round(1), "Normal score": top.normal_score_100.round(1),
        "Top-10 share": top.top10_share})
    st.dataframe(t, hide_index=True, width="stretch",
                 column_config={"Top-10 share": st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=1)})
    fig = go.Figure(go.Bar(x=top.top10_share * 100, y=top.player, orientation="h", marker_color=color,
                           text=(top.top10_share * 100).round(0).astype(int).astype(str) + "%", textposition="outside"))
    fig.update_layout(title="How often each player stays in the top 10 across 300 match resamples",
                      xaxis=dict(title="% of resamples", range=[0, 105]), yaxis=dict(autorange="reversed"),
                      height=420, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig, width="stretch")
    st.info("Ranks 7-10 are close calls: their top-10 share is well below the leaders'.")

elif page == "Pressure vs normal":
    st.write("Above the diagonal = better under pressure than in normal play. Below = dips under pressure.")
    rest, sel = df[df.final_rank.isna()], top
    fig = go.Figure()
    lim = [min(df.normal_score_100.min(), df.pressure_score_100.min()) - 1, max(df.normal_score_100.max(), df.pressure_score_100.max()) + 1]
    fig.add_trace(go.Scatter(x=lim, y=lim, mode="lines", line=dict(color=GREY, dash="dash"), hoverinfo="skip", showlegend=False))
    for d, name, col, size in [(rest, "Other eligible", GREY, 7), (sel, "Final top 10", color, 11)]:
        fig.add_trace(go.Scatter(
            x=d.normal_score_100, y=d.pressure_score_100, mode="markers+text" if name == "Final top 10" else "markers",
            text=d.player if name == "Final top 10" else None,
            textposition=[["top center", "bottom center", "middle right", "middle left", "top right"][i % 5] for i in range(len(d))] if name == "Final top 10" else "top center", name=name,
            marker=dict(color=col, size=size, opacity=0.9 if name == "Final top 10" else 0.55),
            customdata=d[["player", "pressure_balls", "matches"]],
            hovertemplate="<b>%{customdata[0]}</b><br>Normal %{x:.1f} | Pressure %{y:.1f}<br>%{customdata[1]:.0f} pressure balls, %{customdata[2]:.0f} matches<extra></extra>"))
    fig.update_layout(xaxis_title="Normal-play score (per 100 balls)", yaxis_title="Pressure score (per 100 balls)",
                      height=620, margin=dict(l=10, r=10, t=20, b=10), legend=dict(orientation="h", y=1.05))
    st.plotly_chart(fig, width="stretch")

elif page == "Player explorer":
    c1, c2 = st.columns([2, 1])
    q = c1.text_input("Search player")
    minb = c2.slider("Minimum pressure balls", 100, int(df.pressure_balls.max()), 100)
    v = df[(df.pressure_balls >= minb) & df.player.str.contains(q, case=False, na=False)].sort_values("comp_rank")
    t = pd.DataFrame({
        "Composite rank": v.comp_rank, "Final rank": v.final_rank.astype("Int64"), "Player": v.player,
        "Pressure balls": v.pressure_balls.astype(int), "Matches": v.matches.astype(int),
        f"{rate_name}, pressure": v.rate_p.round(2), f"{rate_name}, normal": v.rate_np.round(2),
        f"{bpe_name}, pressure": v.bpe_p.round(1), f"{bpe_name}, normal": v.bpe_np.round(1),
        "Pressure score": v.pressure_score_100.round(1), "Normal-play score": v.normal_score_100.round(1),
        "Hit-rate": v.hit_rate, "Composite score": v.composite_score.round(2), "Top-10 share": v.top10_share})
    st.write(f"{len(t)} players")
    st.dataframe(t, hide_index=True, width="stretch",
                 column_config={"Hit-rate": st.column_config.NumberColumn(format="%.2f"),
                                "Top-10 share": st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=1)})

elif page == "Stability":
    st.subheader("Sensitivity tests")
    st.write("Each row changes one of our choices and shows how many of the headline top 10 stay in the top 10 (out of 10).")
    s = sens[role].copy()
    s["variant"] = s["variant"].str.capitalize()
    s["spearman"] = s["spearman"].round(2)
    s = s.rename(columns={"variant": "Change", "eligible": "Eligible players",
                                    "spearman": "Rank correlation", "top10_overlap": "Names kept (of 10)"})
    st.dataframe(s, hide_index=True, width="stretch")
    fig = go.Figure(go.Bar(x=s["Names kept (of 10)"], y=s["Change"], orientation="h", marker_color=color, text=s["Names kept (of 10)"], textposition="outside"))
    fig.update_layout(xaxis=dict(range=[0, 11], title="Names kept (of 10)"), yaxis=dict(autorange="reversed"),
                      height=max(380, 26 * len(s)), margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, width="stretch")
    st.write("The top 3-4 never leave under any test; the last places swap in and out.")

else:
    st.subheader("How the ranking works")
    st.markdown("""
**Pressure ball.** Decided from the match situation before the ball. *Chase:* required rate high with wickets falling,
or from over 11 the batting team's win probability is 25% or lower (never below 10%). *First innings:* over 16+ with
6 or fewer wickets in hand, or over 18+. *Bowling:* the first-innings rule, plus chase balls from over 7 where the bowling
team's win probability is 10-25%, the ball after two boundaries in a row, and the free hit after a no-ball.

**Ball score.** (runs - expected runs) - wicket cost x (dismissed - expected dismissal). Expected values are league averages
for the same tier, innings, over band, wickets lost and required-rate band. Bowler scores are mirrored.

**Shrunk score.** A player's average is pulled toward zero in proportion to how few balls it rests on, so a small hot streak
cannot outrank a large record. **Composite** = 0.7 / 0.1 / 0.2 (batters) or 0.8 / 0 / 0.2 (bowlers) of the conservative
pressure score, change from own baseline and hit-rate.

**Eligibility.** 100+ pressure balls, 16+ matches with pressure balls, 100+ normal balls.

**Limits.** Pressure performance is only about as repeatable as normal performance; ranks 7-10 are close calls; venue, season
and (for batters) bowler quality are not adjusted.
""")
