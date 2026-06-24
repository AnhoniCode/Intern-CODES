import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import streamlit as st

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="FIFA World Cup 2026 · Player Stats",
    page_icon="⚽",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Barlow', sans-serif; }

    .stApp { background-color: #020F2A; color: #e8eaf0; }

    section[data-testid="stSidebar"] {
        background-color: #051428 !important;
        border-right: 1px solid #0d2a50;
    }

    h1 { font-size: 2rem !important; font-weight: 800 !important; color: #F0C030 !important; letter-spacing: -0.5px; }
    h2, h3 { color: #cdd3e8 !important; font-weight: 700 !important; }

    .fifa-badge {
        display: inline-block;
        background: #F0C030;
        color: #020F2A;
        font-weight: 800;
        font-size: 11px;
        padding: 3px 10px;
        border-radius: 3px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .trophy-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 4px;
    }

    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #051428 0%, #0a2040 100%);
        border: 1px solid #0d2a50;
        border-top: 3px solid #F0C030;
        border-radius: 8px;
        padding: 14px 18px;
    }
    div[data-testid="metric-container"] label {
        color: #6e7fa8 !important;
        font-size: 11px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600 !important;
    }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #F0C030 !important;
        font-size: 26px !important;
        font-weight: 800 !important;
    }

    .stDataFrame {
        border: 1px solid #0d2a50;
        border-radius: 8px;
    }

    .stSelectbox label, .stMultiSelect label, .stSlider label, .stTextInput label {
        color: #7a8fb8 !important;
        font-size: 11px !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-weight: 600 !important;
    }

    .stButton > button {
        background-color: #F0C030;
        color: #020F2A;
        font-weight: 700;
        border: none;
        border-radius: 4px;
    }
    .stButton > button:hover { background-color: #d4a820; }

    .stDownloadButton > button {
        background-color: #0a2040;
        color: #F0C030;
        border: 1px solid #F0C030;
        border-radius: 4px;
        font-weight: 700;
    }

    hr { border-color: #0d2a50; }

    .info-box {
        background: #051428;
        border-left: 3px solid #F0C030;
        padding: 10px 14px;
        border-radius: 0 6px 6px 0;
        font-size: 13px;
        color: #7a8fb8;
        margin-bottom: 12px;
    }

    .player-card {
        background: linear-gradient(135deg, #051428 0%, #0a2040 100%);
        border: 1px solid #0d2a50;
        border-radius: 10px;
        padding: 18px 22px;
        margin-top: 12px;
    }

    .rank-gold   { color: #F0C030; font-weight: 800; font-size: 18px; }
    .rank-silver { color: #C0C0C0; font-weight: 800; font-size: 18px; }
    .rank-bronze { color: #CD7F32; font-weight: 800; font-size: 18px; }
</style>
""", unsafe_allow_html=True)



@st.cache_data(ttl=900)   # refresh every 15 minutes
def fetch_top_scorers():
    url = (
        "https://www.whereig.com/football/world-cup/"
        "fifa-world-cup-2026-top-goal-scorers-golden-boot-race.html"
    )
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        return None, f"Network error: {e}"

    soup = bs(resp.content, "html.parser")

    # The page has one main stats table — grab the first one with Rank/Player/Team/Goals
    tables = soup.find_all("table")
    target = None
    for t in tables:
        headers_row = t.find("tr")
        if headers_row:
            cols = [th.get_text(strip=True).lower() for th in headers_row.find_all(["th", "td"])]
            if "player" in cols and "goals" in cols:
                target = t
                break

    if not target:
        return None, "Could not find the stats table on the page."

    # Parse header
    header_cells = target.find("tr").find_all(["th", "td"])
    col_names = [c.get_text(strip=True) for c in header_cells]

    rows = []
    for tr in target.find_all("tr")[1:]:  # skip header
        cells = tr.find_all(["td", "th"])
        if not cells:
            continue
        row = {col_names[i]: cells[i].get_text(strip=True) for i in range(min(len(col_names), len(cells)))}
        rows.append(row)

    if not rows:
        return None, "Table found but no data rows."

    df = pd.DataFrame(rows)

    # Clean numeric columns
    for col in df.columns:
        if col.lower() in ["rank", "goals", "assists", "apps", "minutes"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df, None



COUNTRY_FLAGS = {
    "Argentina": "🇦🇷", "Norway": "🇳🇴", "France": "🇫🇷", "Germany": "🇩🇪",
    "Canada": "🇨🇦", "Japan": "🇯🇵", "Netherlands": "🇳🇱", "Portugal": "🇵🇹",
    "New Zealand": "🇳🇿", "USA": "🇺🇸", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Morocco": "🇲🇦",
    "Senegal": "🇸🇳", "Switzerland": "🇨🇭", "Brazil": "🇧🇷", "Uruguay": "🇺🇾",
    "Spain": "🇪🇸", "Sweden": "🇸🇪", "Uzbekistan": "🇺🇿", "Saudi Arabia": "🇸🇦",
    "Colombia": "🇨🇴", "Egypt": "🇪🇬", "Bosnia and Herzegovina": "🇧🇦",
    "Ivory Coast": "🇨🇮", "Algeria": "🇩🇿", "Australia": "🇦🇺", "Mexico": "🇲🇽",
    "Croatia": "🇭🇷", "Paraguay": "🇵🇾", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Austria": "🇦🇹",
    "Iran": "🇮🇷", "Czechia": "🇨🇿", "Ghana": "🇬🇭", "Republic of Korea": "🇰🇷",
    "Iraq": "🇮🇶", "DR Congo": "🇨🇩", "Cabo Verde": "🇨🇻", "South Africa": "🇿🇦",
    "Tunisia": "🇹🇳", "Jordan": "🇯🇴", "Curacao": "🇨🇼",
}

def flag(team):
    return COUNTRY_FLAGS.get(team, "🏳️")


# ─────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────
def main():
    # ── Header ──
    st.markdown('<div class="fifa-badge">🏆 Live 2026 Data</div>', unsafe_allow_html=True)
    st.title("⚽ FIFA World Cup 2026 · Golden Boot Tracker")
    st.caption("Live top scorers scraped from **whereig.com** (Official FIFA source) · Refreshes every 15 min")

    # ── Sidebar ──
    st.sidebar.markdown("## 🔍 Filters")
    st.sidebar.markdown(
        '<div class="info-box">Search by player name, filter by country, or set a minimum goals threshold.</div>',
        unsafe_allow_html=True
    )

    # ── Load data ──
    with st.spinner("⏳ Fetching live World Cup 2026 stats..."):
        df, error = fetch_top_scorers()

    if error or df is None:
        st.error(f"❌ **Failed to load data:** {error}")
        return

    # ── Column detection ──
    all_cols   = list(df.columns)
    player_col = next((c for c in all_cols if "player" in c.lower()), all_cols[0])
    team_col   = next((c for c in all_cols if "team"   in c.lower()), None)
    goals_col  = next((c for c in all_cols if "goal"   in c.lower()), None)
    rank_col   = next((c for c in all_cols if "rank"   in c.lower()), None)

    # ── Sidebar filters ──
    search = st.sidebar.text_input("🔎 Search Player", placeholder="e.g. Messi")

    team_choice = []
    if team_col:
        teams = sorted(df[team_col].dropna().unique().tolist())
        team_choice = st.sidebar.multiselect(
            "🌍 Filter by Country",
            [f"{flag(t)} {t}" for t in teams],
            placeholder="All countries"
        )
        # Strip flag emoji back for filtering
        team_choice_clean = [t.split(" ", 1)[-1] for t in team_choice]

    min_goals = 0
    if goals_col and df[goals_col].notna().any():
        max_g    = int(df[goals_col].max())
        min_goals = st.sidebar.slider("⚽ Min Goals", 0, max_g, 0)

    top_n = st.sidebar.select_slider(
        "📊 Show Top N Players",
        options=[10, 20, 30, 50, len(df)],
        value=20
    )

    # ── Apply filters ──
    filtered = df.copy()

    if search:
        filtered = filtered[filtered[player_col].str.contains(search, case=False, na=False)]
    if team_col and team_choice:
        filtered = filtered[filtered[team_col].isin(team_choice_clean)]
    if goals_col:
        filtered = filtered[filtered[goals_col] >= min_goals]

    filtered = filtered.head(top_n)

    # ── Metrics row ──
    st.divider()
    m1, m2, m3, m4 = st.columns(4)

    m1.metric("👤 Players Shown", len(filtered))

    if goals_col and not df.empty and df[goals_col].notna().any():
        total_goals = int(df[goals_col].sum())
        m2.metric("⚽ Total Goals in WC2026", total_goals)

        leader_row    = df.loc[df[goals_col].idxmax()]
        leader_name   = leader_row[player_col]
        leader_goals  = int(leader_row[goals_col])
        leader_team   = leader_row[team_col] if team_col else ""
        m3.metric("🥇 Golden Boot Leader", leader_name, f"{leader_goals} goals · {flag(leader_team)} {leader_team}")

    if team_col:
        m4.metric("🌍 Nations Represented", df[team_col].nunique())

    st.divider()

    # ── Top 3 podium ──
    if goals_col and len(df) >= 3:
        st.subheader("🏆 Podium")
        p1, p2, p3 = st.columns(3)

        podium_data = df.nlargest(3, goals_col).reset_index(drop=True)

        with p2:  # Gold — center
            r = podium_data.iloc[0]
            t = r[team_col] if team_col else ""
            st.markdown(f"""
            <div class="player-card" style="border-top: 3px solid #F0C030; text-align:center;">
                <div style="font-size:2rem">🥇</div>
                <div style="color:#F0C030; font-size:1.3rem; font-weight:800;">{r[player_col]}</div>
                <div style="color:#7a8fb8; font-size:0.9rem;">{flag(t)} {t}</div>
                <div style="color:#F0C030; font-size:2rem; font-weight:800; margin-top:6px;">{int(r[goals_col])} ⚽</div>
            </div>""", unsafe_allow_html=True)

        with p1:  # Silver — left
            r = podium_data.iloc[1]
            t = r[team_col] if team_col else ""
            st.markdown(f"""
            <div class="player-card" style="border-top: 3px solid #C0C0C0; text-align:center; margin-top:30px;">
                <div style="font-size:1.8rem">🥈</div>
                <div style="color:#C0C0C0; font-size:1.1rem; font-weight:800;">{r[player_col]}</div>
                <div style="color:#7a8fb8; font-size:0.85rem;">{flag(t)} {t}</div>
                <div style="color:#C0C0C0; font-size:1.7rem; font-weight:800; margin-top:6px;">{int(r[goals_col])} ⚽</div>
            </div>""", unsafe_allow_html=True)

        with p3:  # Bronze — right
            r = podium_data.iloc[2]
            t = r[team_col] if team_col else ""
            st.markdown(f"""
            <div class="player-card" style="border-top: 3px solid #CD7F32; text-align:center; margin-top:30px;">
                <div style="font-size:1.8rem">🥉</div>
                <div style="color:#CD7F32; font-size:1.1rem; font-weight:800;">{r[player_col]}</div>
                <div style="color:#7a8fb8; font-size:0.85rem;">{flag(t)} {t}</div>
                <div style="color:#CD7F32; font-size:1.7rem; font-weight:800; margin-top:6px;">{int(r[goals_col])} ⚽</div>
            </div>""", unsafe_allow_html=True)

    st.divider()

    # ── Bar chart — goals per player ──
    if goals_col and not filtered.empty:
        st.subheader("📊 Goals Leaderboard")

        chart_df = filtered[[player_col, goals_col]].dropna()
        chart_df = chart_df.sort_values(goals_col, ascending=True).tail(20)

        # Build HTML bar chart (no plotly — just CSS bars)
        max_val = float(chart_df[goals_col].max()) if not chart_df.empty else 1
        bars_html = ""
        for _, row in chart_df.sort_values(goals_col, ascending=False).iterrows():
            pct   = (row[goals_col] / max_val) * 100
            team  = filtered.loc[filtered[player_col] == row[player_col], team_col].values[0] if team_col else ""
            bars_html += f"""
            <div style="display:flex; align-items:center; margin-bottom:6px; gap:10px;">
                <div style="width:170px; text-align:right; font-size:13px; color:#cdd3e8; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{flag(team)} {row[player_col]}</div>
                <div style="flex:1; background:#0a2040; border-radius:3px; height:22px; position:relative;">
                    <div style="width:{pct}%; background:linear-gradient(90deg, #F0C030, #e08010); height:100%; border-radius:3px; transition:width 0.3s;"></div>
                </div>
                <div style="width:30px; text-align:left; font-size:14px; font-weight:700; color:#F0C030;">{int(row[goals_col])}</div>
            </div>"""

        st.markdown(
            f'<div style="padding: 16px; background:#051428; border-radius:10px; border:1px solid #0d2a50;">{bars_html}</div>',
            unsafe_allow_html=True
        )

    st.divider()

    # ── Full stats table ──
    st.subheader("📋 Full Player Rankings")

    # Add flag column for display
    display_df = filtered.copy()
    if team_col:
        display_df["Flag"] = display_df[team_col].apply(flag)
        display_cols = ["Flag"] + [c for c in all_cols if c in display_df.columns]
    else:
        display_cols = all_cols

    st.dataframe(
        display_df[display_cols].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Flag": st.column_config.TextColumn("🏳️", width="small"),
            goals_col: st.column_config.ProgressColumn(
                "Goals ⚽",
                min_value=0,
                max_value=int(df[goals_col].max()) if goals_col and df[goals_col].notna().any() else 10,
                format="%d",
            ) if goals_col else None,
        }
    )

    # ── Goals by country ──
    if team_col and goals_col:
        st.divider()
        st.subheader("🌍 Goals by Country")
        country_goals = (
            df.groupby(team_col)[goals_col]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
            .head(15)
        )
        country_goals.columns = ["Country", "Total Goals"]
        country_goals["Flag"] = country_goals["Country"].apply(flag)

        max_cg = float(country_goals["Total Goals"].max()) if not country_goals.empty else 1
        cbars = ""
        for _, row in country_goals.iterrows():
            pct = (row["Total Goals"] / max_cg) * 100
            cbars += f"""
            <div style="display:flex; align-items:center; margin-bottom:6px; gap:10px;">
                <div style="width:150px; text-align:right; font-size:13px; color:#cdd3e8;">{row['Flag']} {row['Country']}</div>
                <div style="flex:1; background:#0a2040; border-radius:3px; height:20px; position:relative;">
                    <div style="width:{pct}%; background:linear-gradient(90deg, #3060c0, #5090e0); height:100%; border-radius:3px;"></div>
                </div>
                <div style="width:30px; text-align:left; font-size:14px; font-weight:700; color:#5090e0;">{int(row['Total Goals'])}</div>
            </div>"""

        st.markdown(
            f'<div style="padding:16px; background:#051428; border-radius:10px; border:1px solid #0d2a50;">{cbars}</div>',
            unsafe_allow_html=True
        )

    # ── Download ──
    st.divider()
    csv = filtered.to_csv(index=False)
    st.download_button(
        label="📥 Export to CSV",
        data=csv,
        file_name="fifa_wc2026_top_scorers.csv",
        mime="text/csv"
    )
    st.caption("⚠️ Data sourced from whereig.com (official FIFA data). For personal & educational use only.")


main()
