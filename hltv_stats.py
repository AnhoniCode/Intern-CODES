import cloudscraper
from bs4 import BeautifulSoup as bs
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="HLTV Player Stats",
    page_icon="🎯",
    layout="wide"
)


st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stApp { background-color: #111318; color: #d0d3db; }

    section[data-testid="stSidebar"] {
        background-color: #1a1d26 !important;
        border-right: 1px solid #2a2f3e;
    }

    h1 { color: #f4a61b !important; font-weight: 700; letter-spacing: -0.5px; }
    h2, h3 { color: #e0e3eb !important; }

    .hltv-badge {
        display: inline-block;
        background: #f4a61b;
        color: #111318;
        font-weight: 700;
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 3px;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 6px;
    }

    div[data-testid="metric-container"] {
        background: #1a1d26;
        border: 1px solid #2a2f3e;
        border-top: 3px solid #f4a61b;
        border-radius: 6px;
        padding: 12px 16px;
    }

    div[data-testid="metric-container"] label {
        color: #7a7f91 !important;
        font-size: 11px !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }

    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #f4a61b !important;
        font-size: 22px !important;
        font-weight: 700;
    }

    .stDataFrame { border: 1px solid #2a2f3e; border-radius: 6px; }

    .stSelectbox label, .stMultiSelect label, .stSlider label {
        color: #9298ab !important;
        font-size: 12px !important;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }

    .stButton > button {
        background-color: #f4a61b;
        color: #111318;
        font-weight: 600;
        border: none;
        border-radius: 4px;
    }
    .stButton > button:hover { background-color: #d4900f; color: #111318; }

    .stDownloadButton > button {
        background-color: #1e2130;
        color: #f4a61b;
        border: 1px solid #f4a61b;
        border-radius: 4px;
        font-weight: 600;
    }

    .stAlert { border-radius: 6px; }

    hr { border-color: #2a2f3e; }

    .tip-box {
        background: #1a1d26;
        border-left: 3px solid #f4a61b;
        padding: 10px 14px;
        border-radius: 0 6px 6px 0;
        font-size: 13px;
        color: #9298ab;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=1800)  # Cache for 30 mins so we don't hammer HLTV
def fetch_hltv_stats():
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
    }

    try:
        resp = scraper.get(
            "https://www.hltv.org/stats/players",
            headers=headers,
            timeout=20
        )
    except Exception as e:
        return None, f"Connection error: {e}"

    if resp.status_code != 200:
        return None, f"HTTP {resp.status_code} — HLTV may be blocking the request."

    soup = bs(resp.content, "html.parser")

    # Locate the stats table (HLTV uses .stats-table class)
    table = soup.find("table", class_=lambda c: c and "stats-table" in c)
    if not table:
        table = soup.find("table")
    if not table:
        return None, "Stats table not found — HLTV may have changed their page structure."

    # Parse column headers dynamically
    header_cells = table.find("thead").find_all("th") if table.find("thead") else []
    col_names = [h.get_text(strip=True) for h in header_cells]

    rows = table.find("tbody").find_all("tr") if table.find("tbody") else []
    if not rows:
        return None, "No player rows found in the table."

    players = []
    for row in rows:
        cols = row.find_all("td")
        if not cols:
            continue

        player_data = {}
        for i, col in enumerate(cols):
            key = col_names[i] if i < len(col_names) else f"Col {i+1}"
            player_data[key] = col.get_text(strip=True)

        # Grab profile link from first cell
        link = cols[0].find("a") if cols else None
        if link and link.get("href"):
            player_data["Profile URL"] = "https://www.hltv.org" + link["href"]

        players.append(player_data)

    if not players:
        return None, "Scraped 0 players — the page may be dynamically rendered via JS."

    df = pd.DataFrame(players)
    return df, None


# ─────────────────────────────────────────────
#  HELPER — detect column by keyword
# ─────────────────────────────────────────────
def find_col(df, keyword):
    for c in df.columns:
        if keyword.lower() in c.lower():
            return c
    return None


# ─────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────
def main():
    # Header
    st.markdown('<div class="hltv-badge">Live Data</div>', unsafe_allow_html=True)
    st.title("🎯 HLTV CS2 Player Stats Tracker")
    st.caption("Scraped in real-time from **hltv.org/stats/players** — data refreshes every 30 minutes.")

    # ── Sidebar ──
    st.sidebar.markdown("## 🔍 Filters")
    st.sidebar.markdown(
        '<div class="tip-box">Use the filters below to search, narrow by team, or set a minimum rating threshold.</div>',
        unsafe_allow_html=True
    )

    # ── Fetch data ──
    with st.spinner("⏳ Connecting to HLTV and scraping stats..."):
        df, error = fetch_hltv_stats()

    if error or df is None:
        st.error(f"❌ **Failed to load data:** {error}")
        st.markdown("""
        <div class="tip-box">
        💡 <strong>Tip:</strong> HLTV uses Cloudflare protection. Try running this locally with
        <code>streamlit run hltv_stats.py</code> — local environments often have better success
        bypassing bot detection than cloud runners.
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Auto-detect important columns ──
    all_cols  = [c for c in df.columns if c != "Profile URL"]
    player_col = all_cols[0] if all_cols else None
    team_col   = find_col(df, "team")
    rating_col = find_col(df, "rating")
    maps_col   = find_col(df, "maps")
    kd_col     = find_col(df, "k/d")

    # Convert numeric columns
    for col in [rating_col, maps_col, kd_col]:
        if col:
            df[col] = pd.to_numeric(df[col].str.replace("+", "", regex=False), errors="coerce")

    # ── Sidebar: Player search ──
    player_names = sorted(df[player_col].dropna().unique().tolist()) if player_col else []
    player_choice = st.sidebar.selectbox(
        "🧑 Player",
        ["All Players"] + player_names
    )

    # ── Sidebar: Team filter ──
    team_choice = []
    if team_col:
        teams = sorted(df[team_col].dropna().unique().tolist())
        team_choice = st.sidebar.multiselect("🏟️ Team", teams, placeholder="Any team")

    # ── Sidebar: Rating 2.0 filter ──
    rating_range = None
    if rating_col and df[rating_col].notna().any():
        min_r = float(df[rating_col].min())
        max_r = float(df[rating_col].max())
        rating_range = st.sidebar.slider(
            "⭐ Min Rating 2.0",
            min_value=min_r,
            max_value=max_r,
            value=min_r,
            step=0.01,
            format="%.2f"
        )

    # ── Sidebar: Maps played filter ──
    maps_range = None
    if maps_col and df[maps_col].notna().any():
        min_m = int(df[maps_col].min())
        max_m = int(df[maps_col].max())
        maps_range = st.sidebar.slider(
            "🗺️ Min Maps Played",
            min_value=min_m,
            max_value=max_m,
            value=min_m
        )

    # ── Sidebar: Column selector ──
    st.sidebar.markdown("---")
    visible_cols = st.sidebar.multiselect(
        "📊 Columns to Display",
        all_cols,
        default=all_cols
    )

    # ── Apply filters ──
    filtered = df.copy()

    if player_choice != "All Players" and player_col:
        filtered = filtered[filtered[player_col] == player_choice]

    if team_col and team_choice:
        filtered = filtered[filtered[team_col].isin(team_choice)]

    if rating_col and rating_range is not None:
        filtered = filtered[filtered[rating_col] >= rating_range]

    if maps_col and maps_range is not None:
        filtered = filtered[filtered[maps_col] >= maps_range]

    # ── Metrics row ──
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("👤 Players", len(filtered))

    if rating_col and filtered[rating_col].notna().any():
        avg = filtered[rating_col].mean()
        m2.metric("⭐ Avg Rating", f"{avg:.2f}")

        best_idx = filtered[rating_col].idxmax()
        best_name = filtered.loc[best_idx, player_col] if player_col else "—"
        best_rating = filtered.loc[best_idx, rating_col]
        m3.metric("🏆 Top Rated", best_name, f"{best_rating:.2f}")

    if team_col:
        m4.metric("🏟️ Teams", filtered[team_col].nunique())

    st.divider()

    # ── Main data table ──
    st.subheader("📋 Player Statistics")

    display_cols = visible_cols if visible_cols else all_cols
    valid_display = [c for c in display_cols if c in filtered.columns]

    st.dataframe(
        filtered[valid_display].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
        column_config={
            rating_col: st.column_config.NumberColumn(format="%.2f") if rating_col in valid_display else None,
            kd_col: st.column_config.NumberColumn(format="%.2f") if kd_col in valid_display else None,
        }
    )

    # ── Single player detail card ──
    if player_choice != "All Players" and not filtered.empty:
        st.divider()
        st.subheader(f"📊 {player_choice} — Full Stat Card")
        player_row = filtered.iloc[0]

        stat_display = [c for c in valid_display if c != player_col]
        if stat_display:
            card_cols = st.columns(min(len(stat_display), 5))
            for i, col_name in enumerate(stat_display):
                val = player_row.get(col_name, "N/A")
                if pd.isna(val):
                    val = "N/A"
                elif isinstance(val, float):
                    val = f"{val:.2f}"
                card_cols[i % len(card_cols)].metric(col_name, val)

        if "Profile URL" in filtered.columns and pd.notna(player_row.get("Profile URL")):
            st.markdown(f"🔗 [View {player_choice}'s full HLTV profile]({player_row['Profile URL']})")

    # ── Download ──
    st.divider()
    col_dl, col_info = st.columns([1, 3])
    with col_dl:
        csv_data = filtered[valid_display].to_csv(index=False)
        st.download_button(
            label="📥 Export to CSV",
            data=csv_data,
            file_name="hltv_player_stats.csv",
            mime="text/csv"
        )
    with col_info:
        st.caption("⚠️ Data is sourced from HLTV.org. For personal and educational use only. Respect HLTV's Terms of Service.")


main()
