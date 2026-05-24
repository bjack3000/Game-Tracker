import re
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

try:
    from nba_api.stats.endpoints import LeagueGameFinder, PlayByPlayV3, ShotChartDetail
    from nba_api.stats.static import teams as nba_teams
    NBA_API_AVAILABLE = True
except Exception:
    NBA_API_AVAILABLE = False

APP_VERSION = "0.6.0"

TEAM_META = {
    "Atlanta Hawks": {"abbr": "ATL", "primary": "#E03A3E", "secondary": "#FDB9B9"},
    "Boston Celtics": {"abbr": "BOS", "primary": "#007A33", "secondary": "#BA9653"},
    "Brooklyn Nets": {"abbr": "BKN", "primary": "#111111", "secondary": "#CFCFCF"},
    "Charlotte Hornets": {"abbr": "CHA", "primary": "#1D1160", "secondary": "#00788C"},
    "Chicago Bulls": {"abbr": "CHI", "primary": "#CE1141", "secondary": "#F9CDD6"},
    "Cleveland Cavaliers": {"abbr": "CLE", "primary": "#6F263D", "secondary": "#FFB81C"},
    "Dallas Mavericks": {"abbr": "DAL", "primary": "#00538C", "secondary": "#B8C4CA"},
    "Denver Nuggets": {"abbr": "DEN", "primary": "#0E2240", "secondary": "#FEC524"},
    "Detroit Pistons": {"abbr": "DET", "primary": "#C8102E", "secondary": "#1D42BA"},
    "Golden State Warriors": {"abbr": "GSW", "primary": "#1D428A", "secondary": "#FFC72C"},
    "Houston Rockets": {"abbr": "HOU", "primary": "#CE1141", "secondary": "#F3C0C8"},
    "Indiana Pacers": {"abbr": "IND", "primary": "#002D62", "secondary": "#FDBB30"},
    "LA Clippers": {"abbr": "LAC", "primary": "#C8102E", "secondary": "#1D428A"},
    "Los Angeles Lakers": {"abbr": "LAL", "primary": "#552583", "secondary": "#FDB927"},
    "Memphis Grizzlies": {"abbr": "MEM", "primary": "#5D76A9", "secondary": "#D7DFEC"},
    "Miami Heat": {"abbr": "MIA", "primary": "#98002E", "secondary": "#F9A01B"},
    "Milwaukee Bucks": {"abbr": "MIL", "primary": "#00471B", "secondary": "#EEE1C6"},
    "Minnesota Timberwolves": {"abbr": "MIN", "primary": "#0C2340", "secondary": "#78BE20"},
    "New Orleans Pelicans": {"abbr": "NOP", "primary": "#0C2340", "secondary": "#C8102E"},
    "New York Knicks": {"abbr": "NYK", "primary": "#006BB6", "secondary": "#F58426"},
    "Oklahoma City Thunder": {"abbr": "OKC", "primary": "#007AC1", "secondary": "#EF3B24"},
    "Orlando Magic": {"abbr": "ORL", "primary": "#0077C0", "secondary": "#C4CED4"},
    "Philadelphia 76ers": {"abbr": "PHI", "primary": "#006BB6", "secondary": "#ED174C"},
    "Phoenix Suns": {"abbr": "PHX", "primary": "#1D1160", "secondary": "#E56020"},
    "Portland Trail Blazers": {"abbr": "POR", "primary": "#E03A3E", "secondary": "#000000"},
    "Sacramento Kings": {"abbr": "SAC", "primary": "#5A2D81", "secondary": "#C5B4E3"},
    "San Antonio Spurs": {"abbr": "SAS", "primary": "#666666", "secondary": "#C4CED4"},
    "Toronto Raptors": {"abbr": "TOR", "primary": "#CE1141", "secondary": "#B4975A"},
    "Utah Jazz": {"abbr": "UTA", "primary": "#002B5C", "secondary": "#F9A01B"},
    "Washington Wizards": {"abbr": "WAS", "primary": "#002B5C", "secondary": "#E31837"},
}


st.set_page_config(page_title="NBA ARCADE DASHBOARD", page_icon="🕹️", layout="wide")

CUSTOM_CSS = """
<style>
/* ═══════════════════════════════════════════════════════════════
   RETRO 16-BIT ARCADE BASKETBALL DASHBOARD — v0.6.0
   Fonts: Press Start 2P (headings/labels) + VT323 (body text)
   Palette: dark navy/black, neon cyan, magenta, gold, green
═══════════════════════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&display=swap');

:root {
    --bg: #040d1a;
    --surface: #07152b;
    --surface-2: #0a1f3d;
    --border: #0ff;
    --border-dim: rgba(0,255,255,0.25);
    --neon-cyan: #00ffff;
    --neon-magenta: #ff00cc;
    --neon-gold: #ffd700;
    --neon-green: #39ff14;
    --neon-orange: #ff6a00;
    --text: #e0f4ff;
    --text-muted: #7ab8d4;
    --shadow-cyan: 0 0 12px rgba(0,255,255,0.45);
    --shadow-magenta: 0 0 12px rgba(255,0,204,0.45);
    --shadow-gold: 0 0 12px rgba(255,215,0,0.45);
    --pixel-border: 3px solid var(--neon-cyan);
    --pixel-border-gold: 3px solid var(--neon-gold);
    --font-pixel: 'Press Start 2P', monospace;
    --font-vt: 'VT323', monospace;
}

/* ── Global background + CRT scanline overlay ── */
.stApp {
    background-color: var(--bg) !important;
    background-image:
        repeating-linear-gradient(
            0deg,
            rgba(0,0,0,0.18) 0px,
            rgba(0,0,0,0.18) 1px,
            transparent 1px,
            transparent 3px
        ),
        radial-gradient(ellipse at 50% 0%, rgba(0,255,255,0.06) 0%, transparent 70%),
        radial-gradient(ellipse at 20% 100%, rgba(255,0,204,0.05) 0%, transparent 60%) !important;
    color: var(--text) !important;
    font-family: var(--font-vt) !important;
}

/* ── Layout ── */
.block-container {
    max-width: 1500px;
    padding-top: 1.2rem;
    padding-bottom: 3rem;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #040d1a 0%, #07152b 100%) !important;
    border-right: 2px solid var(--neon-cyan) !important;
    box-shadow: 4px 0 18px rgba(0,255,255,0.12);
}
[data-testid="stSidebar"] * {
    font-family: var(--font-vt) !important;
    color: var(--text) !important;
}
[data-testid="stSidebar"] .stMarkdown h3,
[data-testid="stSidebar"] label {
    font-family: var(--font-pixel) !important;
    font-size: 0.55rem !important;
    color: var(--neon-cyan) !important;
    text-shadow: 0 0 8px var(--neon-cyan);
    letter-spacing: 0.05em;
}

/* ── Buttons — console menu style ── */
.stButton > button {
    font-family: var(--font-pixel) !important;
    font-size: 0.5rem !important;
    text-transform: uppercase !important;
    background: var(--surface-2) !important;
    color: var(--neon-gold) !important;
    border: 3px solid var(--neon-gold) !important;
    border-radius: 0 !important;
    padding: 0.55rem 1.1rem !important;
    letter-spacing: 0.08em !important;
    box-shadow: 0 0 10px rgba(255,215,0,0.3), inset 0 0 6px rgba(255,215,0,0.08) !important;
    transition: all 0.15s ease !important;
    cursor: pointer;
}
.stButton > button:hover {
    background: var(--neon-gold) !important;
    color: #040d1a !important;
    box-shadow: 0 0 22px rgba(255,215,0,0.8), 0 0 40px rgba(255,215,0,0.4) !important;
    transform: translateY(-1px);
}
.stButton > button:active {
    transform: translateY(1px);
    box-shadow: 0 0 8px rgba(255,215,0,0.5) !important;
}

/* ── Download buttons ── */
.stDownloadButton > button {
    font-family: var(--font-pixel) !important;
    font-size: 0.42rem !important;
    text-transform: uppercase !important;
    background: transparent !important;
    color: var(--neon-green) !important;
    border: 2px solid var(--neon-green) !important;
    border-radius: 0 !important;
    box-shadow: 0 0 8px rgba(57,255,20,0.25) !important;
}
.stDownloadButton > button:hover {
    background: rgba(57,255,20,0.1) !important;
    box-shadow: 0 0 18px rgba(57,255,20,0.6) !important;
}

/* ── Headings ── */
h1, h2, h3 {
    font-family: var(--font-pixel) !important;
    color: var(--neon-cyan) !important;
    text-shadow: 0 0 14px rgba(0,255,255,0.5);
    letter-spacing: 0.04em;
    line-height: 1.6 !important;
}
h1 { font-size: 0.9rem !important; }
h2 { font-size: 0.65rem !important; color: var(--neon-magenta) !important; text-shadow: 0 0 14px rgba(255,0,204,0.5); }
h3 { font-size: 0.55rem !important; }

/* ── Metric values ── */
div[data-testid="stMetricValue"] {
    font-family: var(--font-pixel) !important;
    color: var(--neon-gold) !important;
    text-shadow: 0 0 10px rgba(255,215,0,0.5);
}

/* ── Info/warning/error boxes ── */
.stAlert {
    border-radius: 0 !important;
    border-left: 4px solid var(--neon-cyan) !important;
    background: rgba(0,255,255,0.06) !important;
    font-family: var(--font-vt) !important;
    font-size: 1.05rem !important;
}

/* ── Selectbox / multiselect ── */
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: var(--surface) !important;
    border: 2px solid var(--border-dim) !important;
    border-radius: 0 !important;
    color: var(--text) !important;
    font-family: var(--font-vt) !important;
    font-size: 1.1rem !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    font-family: var(--font-pixel) !important;
    font-size: 0.5rem !important;
    color: var(--neon-cyan) !important;
    background: var(--surface) !important;
    border: 2px solid var(--border-dim) !important;
    border-radius: 0 !important;
    text-shadow: 0 0 6px rgba(0,255,255,0.4);
}
.streamlit-expanderContent {
    background: var(--surface) !important;
    border: 2px solid var(--border-dim) !important;
    border-top: none !important;
}

/* ── Dataframe / table ── */
.stDataFrame {
    border: 2px solid var(--border-dim) !important;
    background: var(--surface) !important;
}
.stDataFrame thead th {
    background: var(--surface-2) !important;
    color: var(--neon-cyan) !important;
    font-family: var(--font-pixel) !important;
    font-size: 0.45rem !important;
    border-bottom: 2px solid var(--neon-cyan) !important;
}
.stDataFrame tbody td {
    font-family: var(--font-vt) !important;
    font-size: 1rem !important;
    color: var(--text) !important;
    border-color: rgba(0,255,255,0.12) !important;
}

/* ══════════════════════════════════════════
   CUSTOM COMPONENT CLASSES
══════════════════════════════════════════ */

/* Retro arcade panel wrapper */
.retro-panel {
    background: var(--surface);
    border: 3px solid var(--neon-cyan);
    box-shadow: var(--shadow-cyan), inset 0 0 20px rgba(0,255,255,0.04);
    padding: 1rem 1.1rem;
    margin-bottom: 0.5rem;
    position: relative;
}
.retro-panel::before {
    content: '';
    position: absolute;
    top: 4px; left: 4px; right: 4px; bottom: 4px;
    border: 1px solid rgba(0,255,255,0.15);
    pointer-events: none;
}

/* Gold accent panel */
.retro-panel-gold {
    background: var(--surface);
    border: 3px solid var(--neon-gold);
    box-shadow: var(--shadow-gold), inset 0 0 20px rgba(255,215,0,0.03);
    padding: 1rem 1.1rem;
    margin-bottom: 0.5rem;
}

/* Magenta accent panel */
.retro-panel-magenta {
    background: var(--surface);
    border: 3px solid var(--neon-magenta);
    box-shadow: var(--shadow-magenta), inset 0 0 20px rgba(255,0,204,0.04);
    padding: 1rem 1.1rem;
    margin-bottom: 0.5rem;
}

/* Card / metric-card */
.card, .metric-card {
    background: var(--surface);
    border: 2px solid var(--border-dim);
    box-shadow: 0 0 12px rgba(0,255,255,0.15);
    padding: 1rem 1.1rem;
    border-radius: 0;
}

/* Scoreboard header */
.header-shell {
    background: linear-gradient(180deg, #061228 0%, #040d1a 100%);
    border: 3px solid var(--neon-gold);
    box-shadow: var(--shadow-gold), 0 0 40px rgba(255,215,0,0.1);
    padding: 1.2rem;
    margin-bottom: 1rem;
    border-radius: 0;
    position: relative;
}
.header-shell::after {
    content: '► SCOREBOARD ◄';
    position: absolute;
    top: -0.7rem;
    left: 50%;
    transform: translateX(-50%);
    font-family: var(--font-pixel);
    font-size: 0.45rem;
    color: var(--neon-gold);
    background: var(--bg);
    padding: 0 0.5rem;
    text-shadow: 0 0 8px var(--neon-gold);
    letter-spacing: 0.1em;
}

/* Team band in header */
.team-band {
    padding: 1rem;
    color: white;
    min-height: 118px;
    border: 2px solid rgba(255,255,255,0.18);
    box-shadow: inset 0 0 18px rgba(0,0,0,0.4);
}

/* Score center */
.score-center {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    min-height: 118px;
}

/* KPI value */
.kpi {
    font-family: var(--font-pixel) !important;
    font-size: 1.4rem;
    font-weight: 400;
    line-height: 1.3;
    color: var(--neon-gold);
    text-shadow: 0 0 12px rgba(255,215,0,0.6);
}

/* Subtle text */
.subtle {
    font-family: var(--font-vt);
    color: var(--text-muted);
    font-size: 1rem;
}

/* Story / narrative text */
.story {
    font-family: var(--font-vt);
    font-size: 1.15rem;
    line-height: 1.6;
    color: var(--text);
}

/* Turning point highlight */
.turning {
    border-left: 4px solid var(--neon-magenta);
    box-shadow: -4px 0 16px rgba(255,0,204,0.3);
}

/* Small pixel label */
.small-label {
    font-family: var(--font-pixel) !important;
    font-size: 0.45rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--neon-cyan);
    text-shadow: 0 0 6px rgba(0,255,255,0.5);
    margin-bottom: 0.25rem;
}

/* Heatmap shell — dark HUD panel */
.heat-shell {
    background: linear-gradient(180deg, #061228 0%, #040d1a 100%);
    border: 3px solid var(--neon-magenta);
    box-shadow: var(--shadow-magenta), 0 16px 40px rgba(255,0,204,0.08);
    padding: 1rem 1rem 1.2rem 1rem;
    border-radius: 0;
    position: relative;
}
.heat-shell::before {
    content: '';
    position: absolute;
    top: 4px; left: 4px; right: 4px; bottom: 4px;
    border: 1px solid rgba(255,0,204,0.15);
    pointer-events: none;
}

.heat-title {
    font-family: var(--font-pixel) !important;
    color: var(--neon-magenta);
    font-size: 0.7rem;
    text-shadow: 0 0 12px rgba(255,0,204,0.6);
    margin-bottom: 0.3rem;
    letter-spacing: 0.05em;
}

.heat-subtle {
    font-family: var(--font-vt);
    color: rgba(224,244,255,0.75);
    font-size: 1rem;
}

.heat-note {
    background: rgba(255,0,204,0.06);
    border: 1px solid rgba(255,0,204,0.2);
    color: rgba(224,244,255,0.9);
    padding: 0.8rem 0.9rem;
    font-family: var(--font-vt);
    font-size: 1rem;
}

.legend-item {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    color: var(--text);
    margin-bottom: 0.45rem;
    font-family: var(--font-vt);
    font-size: 1rem;
}

.legend-dot {
    width: 12px;
    height: 12px;
    border-radius: 0;
    display: inline-block;
    border: 1px solid rgba(255,255,255,0.4);
}

/* ── Arcade title banner (static header when no game loaded) ── */
.arcade-banner {
    background: linear-gradient(180deg, #061228 0%, #040d1a 100%);
    border: 3px solid var(--neon-cyan);
    box-shadow: var(--shadow-cyan), 0 0 60px rgba(0,255,255,0.08);
    padding: 1.5rem 2rem;
    text-align: center;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.arcade-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(0deg, rgba(0,255,255,0.03) 0px, rgba(0,255,255,0.03) 1px, transparent 1px, transparent 4px);
    pointer-events: none;
}
.arcade-banner-title {
    font-family: var(--font-pixel) !important;
    font-size: 1rem;
    color: var(--neon-gold);
    text-shadow: 0 0 20px rgba(255,215,0,0.8), 0 0 40px rgba(255,215,0,0.4);
    letter-spacing: 0.1em;
    display: block;
    margin-bottom: 0.5rem;
}
.arcade-banner-sub {
    font-family: var(--font-vt) !important;
    font-size: 1.2rem;
    color: var(--neon-cyan);
    text-shadow: 0 0 8px rgba(0,255,255,0.5);
    display: block;
}
.arcade-insert {
    font-family: var(--font-pixel) !important;
    font-size: 0.45rem;
    color: var(--neon-magenta);
    text-shadow: 0 0 8px rgba(255,0,204,0.6);
    letter-spacing: 0.15em;
    display: block;
    margin-top: 0.6rem;
    animation: blink 1.2s step-end infinite;
}
@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
}

/* ── Section header pixel badge ── */
.section-badge {
    font-family: var(--font-pixel) !important;
    font-size: 0.5rem;
    color: var(--neon-gold);
    background: var(--surface-2);
    border: 2px solid var(--neon-gold);
    display: inline-block;
    padding: 0.3rem 0.7rem;
    margin-bottom: 0.5rem;
    text-shadow: 0 0 8px rgba(255,215,0,0.5);
    box-shadow: 0 0 10px rgba(255,215,0,0.2);
    letter-spacing: 0.06em;
}

/* ── Radio buttons ── */
[data-testid="stRadio"] label {
    font-family: var(--font-vt) !important;
    font-size: 1.1rem !important;
    color: var(--text) !important;
}

/* ── Code block ── */
pre, code {
    font-family: 'Press Start 2P', monospace !important;
    font-size: 0.45rem !important;
    background: var(--surface) !important;
    border: 1px solid var(--border-dim) !important;
    color: var(--neon-green) !important;
    padding: 0.8rem !important;
}

/* ── Scrollbar retro styling ── */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--neon-cyan); }
::-webkit-scrollbar-thumb:hover { background: var(--neon-gold); }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def team_lookup_maps() -> Tuple[Dict[int, str], Dict[str, str]]:
    id_to_name = {}
    abbr_to_name = {}
    if NBA_API_AVAILABLE:
        for t in nba_teams.get_teams():
            id_to_name[int(t["id"])] = t["full_name"]
            abbr_to_name[t["abbreviation"]] = t["full_name"]
    for name, meta in TEAM_META.items():
        abbr_to_name.setdefault(meta["abbr"], name)
    return id_to_name, abbr_to_name


TEAM_ID_TO_NAME, TEAM_ABBR_TO_NAME = team_lookup_maps()


SEASON_TYPE_OPTIONS = ["Regular Season", "Playoffs"]


@st.cache_data(show_spinner=False)
def fetch_games(season: str = "2025-26", season_type: str = "Regular Season", limit: int = 100) -> pd.DataFrame:
    if not NBA_API_AVAILABLE:
        return pd.DataFrame()
    finder = LeagueGameFinder(
        season_nullable=season,
        season_type_nullable=season_type,
        league_id_nullable="00",
    )
    df = finder.get_data_frames()[0]
    if df.empty:
        return df
    df = df.sort_values("GAME_DATE", ascending=False)
    grouped = (
        df.groupby("GAME_ID")
        .agg(GAME_DATE=("GAME_DATE", "first"), MATCHUP_LIST=("MATCHUP", list), TEAM_LIST=("TEAM_NAME", list))
        .reset_index()
    )
    grouped["LABEL"] = grouped.apply(build_game_label, axis=1)
    return grouped.head(limit)


def build_game_label(row: pd.Series) -> str:
    teams = row.get("TEAM_LIST", []) or []
    matchups = row.get("MATCHUP_LIST", []) or []
    away = None
    home = None
    for matchup, team in zip(matchups, teams):
        if " @ " in str(matchup):
            away = team
        elif " vs. " in str(matchup):
            home = team
    if not away and len(teams) >= 2:
        away = teams[0]
    if not home and len(teams) >= 2:
        home = teams[-1]
    return f"{away} at {home} — {row.get('GAME_DATE', '')}"


@st.cache_data(show_spinner=False)
def load_pbp_from_api(game_id: str) -> pd.DataFrame:
    if not NBA_API_AVAILABLE:
        raise RuntimeError("nba_api is not installed or unavailable.")
    pbp = PlayByPlayV3(game_id=game_id)
    frames = pbp.get_data_frames()
    if frames and not frames[0].empty:
        return frames[0].copy()
    raise RuntimeError("Unable to load play-by-play data from NBA API.")


@st.cache_data(show_spinner=False)
def load_shot_locations(game_id: str, team_id: int) -> pd.DataFrame:
    if not NBA_API_AVAILABLE:
        return pd.DataFrame()
    try:
        shot = ShotChartDetail(team_id=team_id, player_id=0, game_id_nullable=game_id, context_measure_simple="FGA", season_nullable="")
        frames = shot.get_data_frames()
        if frames and not frames[0].empty:
            df = frames[0].copy()
            df.columns = [str(c).strip().lower() for c in df.columns]
            return df
    except Exception:
        return pd.DataFrame()
    return pd.DataFrame()


def format_clock(clock_val: Optional[str]) -> str:
    """Convert an NBA API duration string or bare M:SS string to basketball display format (M:SS).

    Handles:
      - ISO 8601 duration variants: ``PT07M39.00S``, ``PT7M39S``, ``PT00M39.00S``
      - Seconds-only ISO variant:  ``PT39.00S`` (no ``M`` component)
      - Already-normal strings:    ``7:39``, ``12:00``, ``0:00``
      - ``None`` / NaN             → ``"--:--"``

    Returns a string like ``"7:39"`` (no leading zero on minutes).
    """
    if clock_val is None or (isinstance(clock_val, float) and pd.isna(clock_val)):
        return "--:--"
    text = str(clock_val).strip()
    if not text or text in ("nan", "None", "null"):
        return "--:--"
    # ISO 8601 duration: PT##M##.##S or PT##M##S
    if text.upper().startswith("PT"):
        try:
            inner = text[2:]  # strip leading PT
            if "M" in inner.upper():
                m_idx = inner.upper().index("M")
                mins = int(inner[:m_idx])
                s_part = inner[m_idx + 1:]
                if s_part.upper().endswith("S"):
                    s_part = s_part[:-1]
                secs = int(round(float(s_part))) if s_part else 0
            else:
                # PT##.##S — only seconds, no minutes component
                s_part = inner
                if s_part.upper().endswith("S"):
                    s_part = s_part[:-1]
                total = int(round(float(s_part))) if s_part else 0
                mins, secs = divmod(total, 60)
            return f"{mins}:{secs:02d}"
        except Exception:
            return text  # return as-is on unexpected format
    # Already M:SS or MM:SS
    if ":" in text:
        try:
            mm, ss = text.split(":", 1)
            return f"{int(mm)}:{int(float(ss)):02d}"
        except Exception:
            return text
    # Plain numeric seconds
    try:
        total = int(round(float(text)))
        mins, secs = divmod(total, 60)
        return f"{mins}:{secs:02d}"
    except Exception:
        return text


def format_period_clock(period: int, clock_val: Optional[str]) -> str:
    """Combine a period number and clock value into basketball-readable display.

    Examples:
      period=4, clock="PT07M39.00S"  → ``"Q4 7:39"``
      period=1, clock="PT12M00.00S" → ``"Q1 12:00"``
      period=5, clock="PT03M05.00S" → ``"OT 3:05"``
      period=6, clock="PT01M30.00S" → ``"OT2 1:30"``
    """
    clock_str = format_clock(clock_val)
    if period <= 0:
        return clock_str
    if period <= 4:
        return f"Q{period} {clock_str}"
    ot_num = period - 4
    ot_label = "OT" if ot_num == 1 else f"OT{ot_num}"
    return f"{ot_label} {clock_str}"


def parse_clock_to_seconds(clock_val: Optional[str]) -> Optional[int]:
    if clock_val is None or pd.isna(clock_val):
        return None
    text = str(clock_val).strip()
    if text.startswith("PT") and "M" in text and "S" in text:
        try:
            mins = int(text.split("PT")[1].split("M")[0])
            secs = float(text.split("M")[1].split("S")[0])
            return int(round(mins * 60 + secs))
        except Exception:
            return None
    if ":" in text:
        try:
            mm, ss = text.split(":")
            return int(float(mm) * 60 + float(ss))
        except Exception:
            return None
    return None


def compute_elapsed_seconds(row: pd.Series) -> float:
    period = int(row.get("period", 0) or 0)
    remaining = row.get("clock_seconds")
    if remaining is None or pd.isna(remaining):
        remaining = 0
    period_len = 12 * 60 if period <= 4 else 5 * 60
    prior = max(period - 1, 0)
    return min(prior, 4) * 12 * 60 + max(prior - 4, 0) * 5 * 60 + max(period_len - int(remaining), 0)


def resolve_team_name(row: pd.Series) -> str:
    tid = row.get("team_id")
    tri = str(row.get("team_tricode") or "").upper().strip()
    if pd.notna(tid) and int(tid) in TEAM_ID_TO_NAME:
        return TEAM_ID_TO_NAME[int(tid)]
    if tri in TEAM_ABBR_TO_NAME:
        return TEAM_ABBR_TO_NAME[tri]
    return "Unknown"


def classify_event(row: pd.Series) -> str:
    text = " ".join([str(row.get("action_type", "") or ""), str(row.get("sub_type", "") or ""), str(row.get("description", "") or "")]).lower()
    if "free throw" in text or "made shot" in text or "makes" in text:
        return "Scoring"
    if "miss" in text:
        return "Misses"
    if "turnover" in text:
        return "Turnovers"
    if "foul" in text:
        return "Fouls"
    if "rebound" in text:
        return "Rebounds"
    if "substitution" in text or re.search(r"sub\b", text):
        return "Substitutions"
    if "jump ball" in text:
        return "Jump Ball"
    return "Other"


def classify_shot_zone(description: str) -> str:
    text = str(description or "").lower()
    if any(k in text for k in ["3pt", "3-pt", "three point", "3-point"]):
        return "3PT"
    if any(k in text for k in ["free throw", "technical free throw"]):
        return "FT"
    if any(k in text for k in ["layup", "dunk", "tip shot", "hook shot", "driving", "cutting", "putback", "alley oop"]):
        return "Rim"
    if any(k in text for k in ["pullup", "pull-up", "jump shot", "fadeaway", "turnaround", "bank shot", "floating"]):
        return "Midrange"
    return "Unknown"


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    mapping = {
        "gameId": "game_id", "actionNumber": "action_number", "period": "period", "clock": "clock",
        "timeActual": "time_actual", "teamId": "team_id", "teamTricode": "team_tricode", "personId": "person_id",
        "playerName": "player_name", "playerNameI": "player_name_i", "description": "description", "subType": "sub_type",
        "actionType": "action_type", "shotResult": "shot_result", "isFieldGoal": "is_field_goal", "scoreHome": "score_home",
        "scoreAway": "score_away", "scoreMargin": "score_margin", "eventmsgtype": "event_msg_type",
        "eventmsgactiontype": "event_msg_action_type", "homedescription": "home_description", "visitordescription": "away_description",
        "neutraldescription": "neutral_description", "pctimestring": "clock", "wctimestring": "wall_clock",
        "player1_name": "player_name", "player1_team_id": "team_id", "player1_id": "person_id",
    }
    out = out.rename(columns={c: mapping.get(c, c) for c in out.columns})
    needed = ["game_id", "action_number", "period", "clock", "time_actual", "team_id", "team_tricode", "person_id", "player_name",
              "description", "sub_type", "action_type", "shot_result", "is_field_goal", "score_home", "score_away", "score_margin",
              "event_msg_type", "home_description", "away_description", "neutral_description"]
    for col in needed:
        if col not in out.columns:
            out[col] = np.nan
    out["description"] = out["description"].fillna("")
    if out["description"].eq("").all():
        out["description"] = out["home_description"].fillna("")
        out["description"] = out["description"].where(out["description"].astype(str).ne(""), out["away_description"].fillna(""))
        out["description"] = out["description"].where(out["description"].astype(str).ne(""), out["neutral_description"].fillna(""))
    out["team_id"] = pd.to_numeric(out["team_id"], errors="coerce")
    out["period"] = pd.to_numeric(out["period"], errors="coerce").fillna(0).astype(int)
    out["action_number"] = pd.to_numeric(out["action_number"], errors="coerce")
    out["clock"] = out["clock"].astype(str).replace({"nan": None})
    out["clock_seconds"] = out["clock"].apply(parse_clock_to_seconds)
    out["elapsed_game_seconds"] = out.apply(compute_elapsed_seconds, axis=1)
    out["score_home"] = pd.to_numeric(out["score_home"], errors="coerce")
    out["score_away"] = pd.to_numeric(out["score_away"], errors="coerce")
    if out[["score_home", "score_away"]].isna().all().all() and "score" in out.columns:
        parsed = out["score"].astype(str).str.extract(r"(?P<away>\d+)\s*-\s*(?P<home>\d+)")
        out["score_away"] = pd.to_numeric(parsed["away"], errors="coerce")
        out["score_home"] = pd.to_numeric(parsed["home"], errors="coerce")
    out[["score_home", "score_away"]] = out[["score_home", "score_away"]].ffill().fillna(0)
    out["team_name"] = out.apply(resolve_team_name, axis=1)
    out["event_family"] = out.apply(classify_event, axis=1)
    out["shot_zone"] = out["description"].apply(classify_shot_zone)
    return out.sort_values(["period", "elapsed_game_seconds", "action_number"], ascending=[True, True, True]).reset_index(drop=True)


def infer_teams(df: pd.DataFrame) -> Dict[str, str]:
    score_events = df[(df["score_home"].diff().fillna(df["score_home"]) > 0) | (df["score_away"].diff().fillna(df["score_away"]) > 0)]
    home_team = None
    away_team = None
    if not score_events.empty:
        home_candidates = score_events.loc[score_events["score_home"].diff().fillna(score_events["score_home"]) > 0, "team_name"]
        away_candidates = score_events.loc[score_events["score_away"].diff().fillna(score_events["score_away"]) > 0, "team_name"]
        if not home_candidates.empty:
            home_team = home_candidates.mode().iloc[0]
        if not away_candidates.empty:
            away_team = away_candidates.mode().iloc[0]
    all_known = [t for t in df["team_name"].dropna().unique().tolist() if t != "Unknown"]
    if not home_team and all_known:
        home_team = all_known[0]
    if not away_team:
        remaining = [t for t in all_known if t != home_team]
        away_team = remaining[0] if remaining else (all_known[0] if all_known else "Away")
    if home_team == away_team and len(all_known) >= 2:
        home_team, away_team = all_known[:2]
    return {"home": home_team or "Home", "away": away_team or "Away"}


def enrich_game(df: pd.DataFrame, game_date: Optional[str] = None) -> Tuple[pd.DataFrame, Dict]:
    teams = infer_teams(df)
    home_team, away_team = teams["home"], teams["away"]
    enriched = df.copy()
    enriched["home_points_added"] = enriched["score_home"].diff().fillna(enriched["score_home"]).clip(lower=0)
    enriched["away_points_added"] = enriched["score_away"].diff().fillna(enriched["score_away"]).clip(lower=0)
    enriched["scoring_team"] = np.where(enriched["home_points_added"] > 0, home_team, np.where(enriched["away_points_added"] > 0, away_team, None))
    enriched["points_added"] = enriched[["home_points_added", "away_points_added"]].max(axis=1)
    enriched["score_margin_home"] = enriched["score_home"] - enriched["score_away"]
    enriched["absolute_margin"] = enriched["score_margin_home"].abs()
    enriched["period_label"] = enriched["period"].apply(lambda p: f"Q{p}" if p <= 4 else ("OT" if p == 5 else f"OT{p - 4}"))
    enriched["clock_display"] = enriched.apply(
        lambda row: format_clock(row["clock"]), axis=1
    )
    meta = {
        "home_team": home_team,
        "away_team": away_team,
        "home_score": int(enriched["score_home"].max()),
        "away_score": int(enriched["score_away"].max()),
        "winner": home_team if enriched["score_home"].max() >= enriched["score_away"].max() else away_team,
        "date": game_date,
        "home_colors": TEAM_META.get(home_team, {"primary": "#2563eb", "secondary": "#93c5fd"}),
        "away_colors": TEAM_META.get(away_team, {"primary": "#ef4444", "secondary": "#fca5a5"}),
    }
    return enriched, meta


def compute_possessions(df: pd.DataFrame, meta: Dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
    out = df.copy()
    home, away = meta["home_team"], meta["away_team"]
    out["turnover_flag"] = (out["event_family"] == "Turnovers").astype(int)
    out["made_ft_flag"] = ((out["event_family"] == "Scoring") & out["description"].str.contains("free throw", case=False, na=False)).astype(int)
    out["made_shot_flag"] = ((out["event_family"] == "Scoring") & (out["points_added"] > 0) & (~out["description"].str.contains("free throw", case=False, na=False))).astype(int)
    current_team = None
    poss_id = 0
    possession_team = []
    possession_id = []
    change_next = False
    for _, row in out.iterrows():
        scoring_team = row.get("scoring_team")
        team_name = row.get("team_name")
        if current_team is None:
            current_team = scoring_team if scoring_team is not None else (team_name if team_name != "Unknown" else home)
        if change_next:
            poss_id += 1
            current_team = away if current_team == home else home
            change_next = False
        possession_team.append(current_team)
        possession_id.append(poss_id)
        desc = str(row.get("description", "") or "")
        event_family = row.get("event_family")
        if row.get("made_shot_flag", 0) == 1 or event_family == "Turnovers":
            change_next = True
        elif event_family == "Rebounds" and team_name != current_team and team_name != "Unknown":
            change_next = True
        elif event_family == "Jump Ball" and team_name != current_team and team_name != "Unknown":
            change_next = True
        elif row.get("made_ft_flag", 0) == 1 and ("2 of 2" in desc or "3 of 3" in desc or "1 of 1" in desc):
            change_next = True
    out["possession_id"] = possession_id
    out["possession_team"] = possession_team
    poss_summary = out.groupby(["possession_id", "possession_team"], dropna=False).agg(
        start_elapsed=("elapsed_game_seconds", "min"), end_elapsed=("elapsed_game_seconds", "max"), period=("period", "first"),
        start_clock=("clock_display", "first"), points=("points_added", "sum"), turnovers=("turnover_flag", "sum"),
        events=("description", "count"), last_description=("description", "last")
    ).reset_index()
    poss_summary["duration_seconds"] = poss_summary["end_elapsed"] - poss_summary["start_elapsed"]
    return out, poss_summary


def compute_momentum(df: pd.DataFrame, meta: Dict) -> pd.DataFrame:
    out = df.copy()
    home, away = meta["home_team"], meta["away_team"]
    out["swing"] = np.where(out["scoring_team"] == home, out["points_added"], np.where(out["scoring_team"] == away, -out["points_added"], 0))
    out["raw_momentum"] = out["swing"].cumsum()
    return out


def detect_runs(df: pd.DataFrame, meta: Dict, min_team_points: int = 8, max_opponent_points: int = 4) -> pd.DataFrame:
    scoring = df[df["points_added"] > 0].copy().reset_index(drop=True)
    if scoring.empty:
        return pd.DataFrame()
    runs = []
    for i in range(len(scoring)):
        team = scoring.loc[i, "scoring_team"]
        if team is None:
            continue
        team_pts = 0
        opp_pts = 0
        best_j = None
        for j in range(i, len(scoring)):
            pts = int(scoring.loc[j, "points_added"])
            scorer = scoring.loc[j, "scoring_team"]
            team_pts += pts if scorer == team else 0
            opp_pts += pts if scorer != team else 0
            if team_pts >= min_team_points and opp_pts <= max_opponent_points:
                best_j = j
            if opp_pts > max_opponent_points or team_pts >= 18:
                break
        if best_j is not None:
            slice_df = scoring.loc[i:best_j].copy()
            start_row, end_row = slice_df.iloc[0], slice_df.iloc[-1]
            before_home = int(scoring.loc[i - 1, "score_home"]) if i > 0 else 0
            before_away = int(scoring.loc[i - 1, "score_away"]) if i > 0 else 0
            key_plays = slice_df["description"].dropna().astype(str).tolist()[:4]
            player_points = slice_df.groupby("player_name", dropna=True)["points_added"].sum().sort_values(ascending=False)
            top_players = ", ".join([f"{idx} ({int(val)} pts)" for idx, val in player_points.head(3).items() if str(idx) != "nan"])
            runs.append({
                "team": team, "run_label": f"{int(team_pts)}-{int(opp_pts)}", "start_time": f"{start_row['period_label']} {start_row['clock_display']}",
                "end_time": f"{end_row['period_label']} {end_row['clock_display']}", "quarter": int(start_row["period"]),
                "score_before": f"{meta['away_team']} {before_away} - {before_home} {meta['home_team']}",
                "score_after": f"{meta['away_team']} {int(end_row['score_away'])} - {int(end_row['score_home'])} {meta['home_team']}",
                "points_for": int(team_pts), "points_against": int(opp_pts), "key_plays": " | ".join(key_plays), "top_players": top_players or "Not available",
                "start_elapsed": float(start_row["elapsed_game_seconds"]), "end_elapsed": float(end_row["elapsed_game_seconds"]), "swing_value": int(team_pts - opp_pts),
            })
    if not runs:
        return pd.DataFrame()
    return pd.DataFrame(runs).sort_values(["swing_value", "points_for"], ascending=False).drop_duplicates().reset_index(drop=True)


def detect_turning_point(df: pd.DataFrame, runs_df: pd.DataFrame, meta: Dict) -> Optional[Dict]:
    winner = meta["winner"]
    score_col = "score_home" if winner == meta["home_team"] else "score_away"
    opp_col = "score_away" if winner == meta["home_team"] else "score_home"
    lead = df[score_col] - df[opp_col]
    candidate = None
    for i in range(len(df)):
        if lead.iloc[i] > 0 and lead.iloc[i:].min() > -0.01:
            candidate = df.iloc[i]
            break
    best = candidate
    if not runs_df.empty:
        win_runs = runs_df[runs_df["team"] == winner].sort_values(["swing_value", "points_for", "end_elapsed"], ascending=[False, False, True])
        if not win_runs.empty:
            run = win_runs.iloc[0]
            near = df[(df["elapsed_game_seconds"] >= run["start_elapsed"]) & (df["elapsed_game_seconds"] <= run["end_elapsed"]) & (df["scoring_team"] == winner)]
            if not near.empty:
                best = near.iloc[-1]
    if best is None and not df.empty:
        best = df.iloc[df["absolute_margin"].idxmax()]
    if best is None:
        return None
    return {"team": winner, "quarter": int(best["period"]), "clock": str(best["clock_display"]), "score": f"{meta['away_team']} {int(best['score_away'])} - {int(best['score_home'])} {meta['home_team']}", "description": str(best.get("description", "Lead-changing sequence")) or "Lead-changing sequence", "elapsed": float(best["elapsed_game_seconds"])}


def detect_clutch(df: pd.DataFrame, meta: Dict) -> Dict:
    clutch = df[(df["period"] >= 4) & (df["clock_seconds"] <= 300) & (df["absolute_margin"] <= 5)].copy()
    if clutch.empty:
        return {"qualified": False}
    scoring = clutch[clutch["points_added"] > 0].copy()
    lead_changes = int(((clutch["score_margin_home"] > 0).astype(int).diff().fillna(0).abs() == 1).sum())
    return {"qualified": True, "plays": len(scoring), "lead_changes": lead_changes, "home_points": int(scoring["home_points_added"].sum()), "away_points": int(scoring["away_points_added"].sum()), "key_plays": scoring[["period_label", "clock_display", "description"]].head(8)}


def segment_summary(df: pd.DataFrame, meta: Dict, poss_summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for seg_name, seg_df in {"First Half": df[df["period"] <= 2], "Second Half": df[(df["period"] >= 3) & (df["period"] <= 4)], "Overtime": df[df["period"] > 4]}.items():
        if seg_df.empty:
            continue
        seg_poss = poss_summary[poss_summary["period"].isin(seg_df["period"].unique())] if not poss_summary.empty else pd.DataFrame()
        rows.append({
            "segment": seg_name,
            meta["away_team"]: int(seg_df["away_points_added"].sum()),
            meta["home_team"]: int(seg_df["home_points_added"].sum()),
            "lead_changes": int(((seg_df["score_margin_home"] > 0).astype(int).diff().fillna(0).abs() == 1).sum()),
            "turnovers": int((seg_df["event_family"] == "Turnovers").sum()),
            "fouls": int((seg_df["event_family"] == "Fouls").sum()),
            "possessions": int(seg_poss["possession_id"].nunique()) if not seg_poss.empty else 0,
        })
    return pd.DataFrame(rows)


def compute_team_ratings(poss_summary: pd.DataFrame, meta: Dict) -> pd.DataFrame:
    if poss_summary.empty:
        return pd.DataFrame()
    rows = []
    for team in [meta["away_team"], meta["home_team"]]:
        team_poss = poss_summary[poss_summary["possession_team"] == team]
        opp_poss = poss_summary[poss_summary["possession_team"] != team]
        poss = max(len(team_poss), 1)
        opp_allowed = opp_poss["points"].sum() if not opp_poss.empty else 0
        rows.append({
            "team": team,
            "possessions": int(len(team_poss)),
            "points_scored": int(team_poss["points"].sum()),
            "points_allowed": int(opp_allowed),
            "off_rating": round(team_poss["points"].sum() / poss * 100, 1),
            "def_rating": round(opp_allowed / poss * 100, 1),
            "turnover_possessions": int((team_poss["turnovers"] > 0).sum()),
        })
    return pd.DataFrame(rows)


def parse_substitutions(df: pd.DataFrame) -> pd.DataFrame:
    subs = df[df["event_family"] == "Substitutions"].copy()
    if subs.empty:
        return pd.DataFrame(columns=["period_label", "clock_display", "team_name", "player_in", "player_out", "description"])
    player_in = []
    player_out = []
    for desc in subs["description"].astype(str):
        low = desc.lower()
        out_name = None
        in_name = None
        m = re.search(r"(.*?)\s+enters\s+for\s+(.*)", desc, flags=re.IGNORECASE)
        if m:
            in_name, out_name = m.group(1).strip(), m.group(2).strip()
        elif "sub:" in low:
            parts = re.split(r"sub:\s*", desc, flags=re.IGNORECASE)
            text = parts[-1]
            m2 = re.search(r"(.*?)\s+for\s+(.*)", text, flags=re.IGNORECASE)
            if m2:
                in_name, out_name = m2.group(1).strip(), m2.group(2).strip()
        player_in.append(in_name or "Unknown")
        player_out.append(out_name or "Unknown")
    subs["player_in"] = player_in
    subs["player_out"] = player_out
    return subs[["period_label", "clock_display", "team_name", "player_in", "player_out", "description"]]


def player_impact_during_runs(df: pd.DataFrame, runs_df: pd.DataFrame) -> pd.DataFrame:
    if runs_df.empty:
        return pd.DataFrame()
    scoring = df[df["points_added"] > 0].copy().reset_index(drop=True)
    segments = []
    for _, run in runs_df.head(8).iterrows():
        mask = (scoring["elapsed_game_seconds"] >= run["start_elapsed"]) & (scoring["elapsed_game_seconds"] <= run["end_elapsed"]) & (scoring["scoring_team"] == run["team"])
        slice_df = scoring.loc[mask].copy()
        if slice_df.empty:
            continue
        grouped = slice_df.groupby("player_name", dropna=True).agg(points=("points_added", "sum"), plays=("description", "count")).sort_values(["points", "plays"], ascending=False)
        for player, vals in grouped.head(4).iterrows():
            key_events = " ; ".join(slice_df.loc[slice_df["player_name"] == player, "description"].astype(str).head(3).tolist())
            segments.append({"run": run["run_label"], "team": run["team"], "player": player, "points": int(vals["points"]), "scoring_plays": int(vals["plays"]), "key_events": key_events})
    return pd.DataFrame(segments)


def shot_zone_summary(df: pd.DataFrame) -> pd.DataFrame:
    shots = df[df["event_family"].isin(["Scoring", "Misses"])].copy()
    if shots.empty:
        return pd.DataFrame()
    shots["made"] = ((shots["event_family"] == "Scoring") & (~shots["description"].str.contains("free throw", case=False, na=False) | shots["shot_zone"].eq("FT"))).astype(int)
    shots["attempt"] = shots["shot_zone"].ne("Unknown").astype(int)
    summary = shots[shots["shot_zone"] != "Unknown"].groupby(["team_name", "shot_zone"], dropna=False).agg(attempts=("attempt", "sum"), makes=("made", "sum"), points=("points_added", "sum")).reset_index()
    summary["fg_pct"] = np.where(summary["attempts"] > 0, (summary["makes"] / summary["attempts"] * 100).round(1), np.nan)
    return summary.sort_values(["team_name", "shot_zone"]).reset_index(drop=True)


def keys_to_game(df: pd.DataFrame, meta: Dict, runs_df: pd.DataFrame, poss_summary: pd.DataFrame, clutch: Dict) -> List[str]:
    notes = []
    if not runs_df.empty:
        top_run = runs_df.iloc[0]
        notes.append(f"Run of the game: {top_run['team']} went on a {top_run['run_label']} burst between {top_run['start_time']} and {top_run['end_time']} — that stretch changed the entire complexion of the game.")
    if not poss_summary.empty:
        explosive = poss_summary.sort_values(["points", "duration_seconds"], ascending=[False, True]).iloc[0]
        notes.append(f"Most lethal possession: {explosive['possession_team']} squeezed {int(explosive['points'])} points out of a single stretch, capped by '{explosive['last_description']}' — the kind of sequence the other bench just watches in silence.")
    top_margin_row = df.iloc[df["absolute_margin"].idxmax()] if not df.empty else None
    if top_margin_row is not None:
        leader = meta["home_team"] if top_margin_row["score_margin_home"] > 0 else meta["away_team"]
        notes.append(f"Peak separation hit at {top_margin_row['period_label']} {top_margin_row['clock_display']}, with {leader} up by {int(abs(top_margin_row['score_margin_home']))} — the moment the crowd either went home happy or went quiet.")
    if clutch.get("qualified"):
        notes.append(f"Clutch factor: the margin stayed inside five with five minutes left and the lead changed hands {clutch['lead_changes']} time(s) — this one had to be earned the hard way.")
    return notes[:4]


def game_story(meta: Dict, runs_df: pd.DataFrame, turning: Optional[Dict], clutch: Dict, impact_df: pd.DataFrame, ratings_df: pd.DataFrame, shot_df: pd.DataFrame, heatmaps_df: pd.DataFrame) -> str:
    winner = meta["winner"]
    loser = meta["away_team"] if winner == meta["home_team"] else meta["home_team"]
    winner_score = meta["home_score"] if winner == meta["home_team"] else meta["away_score"]
    loser_score = meta["away_score"] if winner == meta["home_team"] else meta["home_score"]
    margin = winner_score - loser_score

    # ── Lede: hook the reader with the final result ──────────────────────────
    if margin <= 3:
        lede = f"In a game that refused to be decided until the final possession, {winner} held on to beat {loser} {winner_score}-{loser_score}."
    elif margin <= 8:
        lede = f"{winner} made it look comfortable down the stretch, pulling away from {loser} for a {winner_score}-{loser_score} win."
    elif margin <= 18:
        lede = f"{winner} got out to business early and never really let {loser} back in, closing it out {winner_score}-{loser_score}."
    else:
        lede = f"This one was over before halftime. {winner} steamrolled {loser} {winner_score}-{loser_score} in a game that was never truly in doubt."
    parts = [lede]

    # ── Possession efficiency — only if the number is meaningful ────────────
    if not ratings_df.empty:
        winner_row = ratings_df[ratings_df["team"] == winner].iloc[0]
        off_rtg = winner_row["off_rating"]
        poss_count = winner_row["possessions"]
        if off_rtg >= 115:
            parts.append(f"{winner} was surgical offensively — their estimated offensive rating of {off_rtg} over {poss_count} tracked possessions is the kind of number that makes film-session prep miserable for the next opponent.")
        elif off_rtg >= 105:
            parts.append(f"Possession-by-possession, {winner} was efficient enough: an estimated offensive rating of {off_rtg} across {poss_count} possessions got the job done.")
        else:
            parts.append(f"{winner} won it despite a modest estimated offensive rating of {off_rtg} — this was more about defensive grit than offensive fireworks.")

    # ── Biggest run — the momentum story ────────────────────────────────────
    if not runs_df.empty:
        top_run = runs_df.iloc[0]
        run_team = top_run["team"]
        run_label = top_run["run_label"]
        run_start = top_run["start_time"]
        run_end = top_run["end_time"]
        if run_team == winner:
            parts.append(f"The {run_label} run by {run_team} between {run_start} and {run_end} was the turning of the tide — the stretch where the game stopped being a contest and started being a coronation.")
        else:
            parts.append(f"{run_team} mounted a {run_label} run from {run_start} to {run_end} and had the crowd briefly believing in a comeback, but {winner} had enough in the tank to weather it.")

    # ── Turning point ────────────────────────────────────────────────────────
    if turning:
        q_label = f"Q{turning['quarter']}" if turning["quarter"] <= 4 else f"OT{turning['quarter'] - 4}"
        parts.append(f"Circle {q_label} {turning['clock']} in your notebook — that's when {turning['team']} made the play that cracked this thing open: {turning['description']} Score at that moment: {turning['score']}.")

    # ── Shooting geography — only the sharpest insight ───────────────────────
    if not heatmaps_df.empty:
        top_hex = heatmaps_df.sort_values(["attempts", "points"], ascending=False).iloc[0]
        zone = top_hex["zone_label"]
        team_h = top_hex["team_name"]
        pts_h = int(top_hex["points"])
        att_h = int(top_hex["attempts"])
        parts.append(f"{team_h} made the {zone} their address all night — {att_h} attempts, {pts_h} points out of that spot. When a team hunts a zone that aggressively and gets production, the defense has real decisions to make.")
    elif not shot_df.empty:
        top_zone = shot_df.sort_values(["points", "attempts"], ascending=False).iloc[0]
        fg = top_zone.get("fg_pct", None)
        pct_str = f" at {fg}%" if pd.notna(fg) and fg > 0 else ""
        parts.append(f"{top_zone['team_name']} lived in the {top_zone['shot_zone']} — {int(top_zone['attempts'])} looks, {int(top_zone['points'])} points{pct_str}. That's a diet plan, and it worked.")

    # ── Clutch time ──────────────────────────────────────────────────────────
    if clutch.get("qualified"):
        if clutch["lead_changes"] >= 3:
            parts.append(f"And yes, it went to the clutch — final five minutes, margin inside five, {clutch['lead_changes']} lead changes. Both benches were burning timeouts and both fan bases were burning through antacids.")
        else:
            parts.append(f"The game got tight late — margin inside five with five to go, {clutch['plays']} scoring plays in the clutch window. {winner} made the right plays when it mattered.")

    # ── Star of the biggest run ──────────────────────────────────────────────
    if not impact_df.empty:
        top_player = impact_df.sort_values(["points", "scoring_plays"], ascending=False).iloc[0]
        player_name = top_player["player"]
        player_pts = int(top_player["points"])
        player_plays = int(top_player["scoring_plays"])
        parts.append(f"When the game needed someone to grab it by the collar, {player_name} answered — {player_pts} points across {player_plays} scoring plays in the most critical stretches. That's the type of performance you build a highlight reel around.")

    return " ".join(parts)


def format_axis_time(seconds: float) -> str:
    s = int(seconds)
    if s < 48 * 60:
        q = s // 720 + 1
        rem = 720 - (s % 720)
        return f"Q{q} {rem // 60:02d}:{rem % 60:02d}"
    ot_elapsed = s - 48 * 60
    ot = ot_elapsed // 300 + 1
    rem = 300 - (ot_elapsed % 300)
    return f"OT{ot} {rem // 60:02d}:{rem % 60:02d}"


def period_ticks(df: pd.DataFrame) -> List[float]:
    max_s = float(df["elapsed_game_seconds"].max()) if not df.empty else 2880
    ticks = [0, 720, 1440, 2160, 2880]
    extra = 3180
    while extra <= max_s + 1:
        ticks.append(extra)
        extra += 300
    return [t for t in ticks if t <= max_s]


def add_period_lines(fig: go.Figure, df: pd.DataFrame) -> None:
    for p in sorted(df["period"].dropna().unique().tolist()):
        boundary = 720 * min(p - 1, 4) + max(p - 4, 0) * 300
        if boundary > 0:
            fig.add_vline(x=boundary, line=dict(color="rgba(0,255,255,0.30)", dash="dot", width=1))


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return f"rgba(255,255,255,{alpha})"
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def filter_dataset(df: pd.DataFrame, selected_periods: List[int], event_filters: List[str], selected_run_idx: int, runs_df: pd.DataFrame) -> pd.DataFrame:
    out = df[df["period"].isin(selected_periods)].copy()
    if event_filters:
        out = out[out["event_family"].isin(event_filters)]
    if selected_run_idx >= 0 and not runs_df.empty and selected_run_idx < len(runs_df):
        run = runs_df.iloc[selected_run_idx]
        out = out[(out["elapsed_game_seconds"] >= run["start_elapsed"]) & (out["elapsed_game_seconds"] <= run["end_elapsed"])]
    return out


def _retro_chart_layout() -> dict:
    """Shared retro HUD layout defaults for all Plotly charts."""
    return dict(
        template="plotly_dark",
        paper_bgcolor="#040d1a",
        plot_bgcolor="#07152b",
        font=dict(family="'VT323', monospace", color="#e0f4ff", size=14),
        legend=dict(
            bgcolor="rgba(4,13,26,0.85)",
            bordercolor="rgba(0,255,255,0.35)",
            borderwidth=2,
            font=dict(family="'VT323', monospace", size=14, color="#e0f4ff"),
        ),
    )


def _retro_axis(title: str = "", is_time: bool = False, extra: dict = None) -> dict:
    """Retro HUD axis style."""
    base = dict(
        title=dict(text=title, font=dict(family="'Press Start 2P', monospace", size=9, color="#00ffff")),
        gridcolor="rgba(0,255,255,0.10)",
        gridwidth=1,
        griddash="dot",
        linecolor="rgba(0,255,255,0.35)",
        linewidth=2,
        tickcolor="#00ffff",
        tickfont=dict(family="'VT323', monospace", size=13, color="#7ab8d4"),
        zeroline=False,
    )
    if extra:
        base.update(extra)
    return base


def score_chart(df: pd.DataFrame, meta: Dict) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["elapsed_game_seconds"], y=df["score_home"],
        mode="lines+markers", name=meta["home_team"],
        line=dict(color=meta["home_colors"]["primary"], width=3),
        marker=dict(size=5, symbol="square"),
    ))
    fig.add_trace(go.Scatter(
        x=df["elapsed_game_seconds"], y=df["score_away"],
        mode="lines+markers", name=meta["away_team"],
        line=dict(color=meta["away_colors"]["primary"], width=3),
        marker=dict(size=5, symbol="square"),
    ))
    add_period_lines(fig, df)
    ticks = period_ticks(df)
    layout = _retro_chart_layout()
    layout.update(dict(
        height=380, margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(**layout["legend"], orientation="h", y=1.08),
        xaxis=_retro_axis("GAME CLOCK", extra=dict(tickmode="array", tickvals=ticks, ticktext=[format_axis_time(v) for v in ticks])),
        yaxis=_retro_axis("SCORE"),
    ))
    fig.update_layout(**layout)
    return fig


def momentum_chart(df: pd.DataFrame, meta: Dict, runs_df: pd.DataFrame, turning: Optional[Dict]) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["elapsed_game_seconds"], y=df["raw_momentum"],
        mode="lines", name="MOMENTUM",
        line=dict(color="#00ffff", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=df["elapsed_game_seconds"],
        y=np.where(df["raw_momentum"] >= 0, df["raw_momentum"], 0),
        fill="tozeroy", mode="none", name=meta["home_team"],
        fillcolor=hex_to_rgba(meta["home_colors"]["primary"], 0.32),
    ))
    fig.add_trace(go.Scatter(
        x=df["elapsed_game_seconds"],
        y=np.where(df["raw_momentum"] <= 0, df["raw_momentum"], 0),
        fill="tozeroy", mode="none", name=meta["away_team"],
        fillcolor=hex_to_rgba(meta["away_colors"]["primary"], 0.28),
    ))
    for _, run in runs_df.head(6).iterrows():
        color = meta["home_colors"]["primary"] if run["team"] == meta["home_team"] else meta["away_colors"]["primary"]
        fig.add_vrect(x0=run["start_elapsed"], x1=run["end_elapsed"], fillcolor=hex_to_rgba(color, 0.12), line_width=0)
        fig.add_annotation(
            x=(run["start_elapsed"] + run["end_elapsed"]) / 2,
            y=df["raw_momentum"].max() * 0.88 if run["team"] == meta["home_team"] else df["raw_momentum"].min() * 0.88,
            text=f"{run['team']} {run['run_label']}",
            showarrow=False,
            font=dict(family="'VT323', monospace", size=13, color="#ffd700"),
        )
    if turning and not df.empty:
        idx = (df["elapsed_game_seconds"] - turning["elapsed"]).abs().idxmin()
        yval = float(df.loc[idx, "raw_momentum"])
        fig.add_trace(go.Scatter(
            x=[turning["elapsed"]], y=[yval],
            mode="markers+text", text=[">>TURN<<"],
            textposition="top center",
            marker=dict(size=14, color="#ff00cc", symbol="diamond"),
            textfont=dict(family="'Press Start 2P', monospace", size=8, color="#ff00cc"),
            name="TURNING PT",
        ))
    add_period_lines(fig, df)
    ticks = period_ticks(df)
    fig.add_hline(y=0, line=dict(color="rgba(0,255,255,0.35)", dash="dash"))
    layout = _retro_chart_layout()
    layout.update(dict(
        height=420, margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False,
        xaxis=_retro_axis("GAME CLOCK", extra=dict(tickmode="array", tickvals=ticks, ticktext=[format_axis_time(v) for v in ticks])),
        yaxis=_retro_axis(f"MOMENTUM  {meta['away_team']}  |  {meta['home_team']}"),
    ))
    fig.update_layout(**layout)
    return fig


def possession_chart(poss_summary: pd.DataFrame, meta: Dict) -> go.Figure:
    fig = go.Figure()
    if poss_summary.empty:
        return fig
    temp_all = poss_summary.copy()
    temp_all["poss_index"] = range(1, len(temp_all) + 1)
    for team, color in [(meta["away_team"], meta["away_colors"]["primary"]), (meta["home_team"], meta["home_colors"]["primary"])]:
        temp = temp_all[temp_all["possession_team"] == team]
        fig.add_trace(go.Bar(
            x=temp["poss_index"], y=temp["points"], name=team,
            marker=dict(color=color, opacity=0.88, line=dict(color="rgba(0,255,255,0.25)", width=1)),
            customdata=temp[["start_clock", "last_description"]],
            hovertemplate="POSS %{x}<br>PTS: %{y}<br>START: %{customdata[0]}<br>%{customdata[1]}<extra></extra>",
        ))
    layout = _retro_chart_layout()
    layout.update(dict(
        barmode="group", height=350, margin=dict(l=20, r=20, t=20, b=20),
        xaxis=_retro_axis("POSSESSION #"),
        yaxis=_retro_axis("PTS / POSSESSION"),
    ))
    fig.update_layout(**layout)
    return fig


def shot_profile_figure(zone_summary: pd.DataFrame, meta: Dict) -> go.Figure:
    """Two-panel Shot Profile: left = Shooting Efficiency (FG%), right = Volume & Frequency (Attempts).

    Zones are ordered logically: 3PT, FT, Rim, Midrange, then any unknown categories appended.
    Each team gets its primary brand color.  Value labels are drawn above each marker.
    """
    ZONE_ORDER = ["3PT", "FT", "Rim", "Midrange"]

    if zone_summary.empty:
        return go.Figure()

    # Build canonical zone order — known first, then any extras alphabetically
    present = zone_summary["shot_zone"].dropna().unique().tolist()
    ordered_known = [z for z in ZONE_ORDER if z in present]
    extras = sorted([z for z in present if z not in ZONE_ORDER])
    zones = ordered_known + extras

    teams = zone_summary["team_name"].dropna().unique().tolist()
    # Map each team to its brand primary color
    fallback_colors = ["#2563eb", "#ef4444", "#16a34a", "#d97706"]
    team_colors: Dict[str, str] = {}
    for i, t in enumerate(teams):
        team_colors[t] = TEAM_META.get(t, {}).get("primary") or fallback_colors[i % len(fallback_colors)]

    # Slight horizontal offset so labels don't overlap when two teams share a zone x-position
    offsets: Dict[str, float] = {}
    if len(teams) == 2:
        offsets[teams[0]] = -0.18
        offsets[teams[1]] = 0.18
    else:
        for t in teams:
            offsets[t] = 0.0

    fig = make_subplots(
        rows=1, cols=2,
        horizontal_spacing=0.10,
        subplot_titles=("Shooting Efficiency (FG%)", "Volume & Frequency"),
    )

    for team in teams:
        tdf = zone_summary[zone_summary["team_name"] == team].set_index("shot_zone").reindex(zones)
        color = team_colors[team]
        x_pos = [i + offsets[team] for i in range(len(zones))]

        # ── Left panel: FG% ──────────────────────────────────────────────────
        fg_vals = tdf["fg_pct"].tolist()
        fg_labels = [
            f"{v:.1f}%" if pd.notna(v) and v > 0 else ""
            for v in fg_vals
        ]
        fig.add_trace(
            go.Scatter(
                x=x_pos,
                y=fg_vals,
                mode="markers+text",
                name=team,
                marker=dict(size=14, color=color, line=dict(color="rgba(255,255,255,0.6)", width=2)),
                text=fg_labels,
                textposition="top center",
                textfont=dict(size=11, color=color),
                legendgroup=team,
                showlegend=True,
                hovertemplate=f"{team}<br>Zone: %{{customdata}}<br>FG%%: %{{y:.1f}}<extra></extra>",
                customdata=zones,
            ),
            row=1, col=1,
        )

        # ── Right panel: Attempts ────────────────────────────────────────────
        att_vals = tdf["attempts"].tolist()
        att_labels = [
            str(int(v)) if pd.notna(v) and v > 0 else ""
            for v in att_vals
        ]
        fig.add_trace(
            go.Scatter(
                x=x_pos,
                y=att_vals,
                mode="markers+text",
                name=team,
                marker=dict(size=14, color=color, line=dict(color="rgba(255,255,255,0.6)", width=2)),
                text=att_labels,
                textposition="top center",
                textfont=dict(size=11, color=color),
                legendgroup=team,
                showlegend=False,
                hovertemplate=f"{team}<br>Zone: %{{customdata}}<br>Attempts: %{{y}}<extra></extra>",
                customdata=zones,
            ),
            row=1, col=2,
        )

    # ── Axis styling ─────────────────────────────────────────────────────────
    tick_vals = list(range(len(zones)))
    for col_idx in (1, 2):
        fig.update_xaxes(
            tickmode="array",
            tickvals=tick_vals,
            ticktext=zones,
            tickfont=dict(size=12),
            showgrid=False,
            zeroline=False,
            row=1, col=col_idx,
        )

    # ── Retro HUD look ──────────────────────────────────────────────────────
    layout = _retro_chart_layout()
    layout.update(dict(
        height=420,
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(
            **layout["legend"],
            orientation="h",
            y=1.14,
            x=0.5,
            xanchor="center",
        ),
    ))
    fig.update_layout(**layout)
    # Style subplot title annotations
    for ann in fig.layout.annotations:
        ann.font = dict(family="'Press Start 2P', monospace", size=9, color="#00ffff")
    # Style axes
    for col_idx in (1, 2):
        fig.update_xaxes(
            tickfont=dict(family="'VT323', monospace", size=13, color="#7ab8d4"),
            linecolor="rgba(0,255,255,0.35)",
            tickcolor="#00ffff",
            row=1, col=col_idx,
        )
    fig.update_yaxes(
        title_text="FG%",
        range=[0, 115],
        ticksuffix="%",
        gridcolor="rgba(0,255,255,0.10)",
        tickfont=dict(family="'VT323', monospace", size=13, color="#7ab8d4"),
        row=1, col=1,
    )
    fig.update_yaxes(
        title_text="ATTEMPTS",
        rangemode="tozero",
        gridcolor="rgba(0,255,255,0.10)",
        tickfont=dict(family="'VT323', monospace", size=13, color="#7ab8d4"),
        row=1, col=2,
    )
    return fig


def shot_zone_chart(shot_df: pd.DataFrame, meta: Dict) -> go.Figure:
    fig = go.Figure()
    if shot_df.empty:
        return fig
    zones = ["Rim", "Midrange", "3PT", "FT"]
    for team, color in [(meta["away_team"], meta["away_colors"]["primary"]), (meta["home_team"], meta["home_colors"]["primary"])]:
        temp = shot_df[shot_df["team_name"] == team].set_index("shot_zone").reindex(zones).fillna(0).reset_index()
        fig.add_trace(go.Bar(
            x=temp["shot_zone"], y=temp["points"], name=team,
            marker=dict(color=color, opacity=0.88, line=dict(color="rgba(0,255,255,0.3)", width=1)),
            customdata=temp[["attempts", "makes", "fg_pct"]],
            hovertemplate="ZONE: %{x}<br>PTS: %{y}<br>ATT: %{customdata[0]}<br>MAKES: %{customdata[1]}<br>FG%%: %{customdata[2]}<extra></extra>",
        ))
    layout = _retro_chart_layout()
    layout.update(dict(
        barmode="group", height=330, margin=dict(l=20, r=20, t=20, b=20),
        xaxis=_retro_axis("SHOT ZONE"),
        yaxis=_retro_axis("POINTS"),
    ))
    fig.update_layout(**layout)
    return fig


def normalize_shot_locations(shots: pd.DataFrame, team_name: str) -> Tuple[pd.DataFrame, str]:
    if shots.empty:
        return pd.DataFrame(), "Inferred Zone Map"
    out = shots.copy()
    out.columns = [str(c).strip().lower() for c in out.columns]
    required = ["loc_x", "loc_y", "shot_made_flag", "shot_type"]
    if any(c not in out.columns for c in required):
        return pd.DataFrame(), "Inferred Zone Map"
    out["loc_x"] = pd.to_numeric(out["loc_x"], errors="coerce")
    out["loc_y"] = pd.to_numeric(out["loc_y"], errors="coerce")
    out = out.dropna(subset=["loc_x", "loc_y"]).copy()
    if out.empty:
        return pd.DataFrame(), "Inferred Zone Map"
    out["made"] = pd.to_numeric(out["shot_made_flag"], errors="coerce").fillna(0).astype(int)
    out["team_name"] = team_name
    out["shot_type"] = out["shot_type"].fillna("2PT Field Goal")
    out["shot_value"] = np.where(out["shot_type"].str.contains("3PT", case=False, na=False), 3 * out["made"], 2 * out["made"])
    out["expected_value"] = np.where(out["shot_type"].str.contains("3PT", case=False, na=False), 1.08, 0.96)
    out["two_pt_make"] = ((~out["shot_type"].str.contains("3PT", case=False, na=False)) & (out["made"] == 1)).astype(int)
    out["two_pt_miss"] = ((~out["shot_type"].str.contains("3PT", case=False, na=False)) & (out["made"] == 0)).astype(int)
    out["three_pt_make"] = ((out["shot_type"].str.contains("3PT", case=False, na=False)) & (out["made"] == 1)).astype(int)
    out["three_pt_miss"] = ((out["shot_type"].str.contains("3PT", case=False, na=False)) & (out["made"] == 0)).astype(int)
    out["ft_ending"] = 0
    out["mode_label"] = "True Shot Coordinates"
    return out, "True Shot Coordinates"


def fallback_shot_map_from_pbp(df: pd.DataFrame, team_name: str) -> Tuple[pd.DataFrame, str]:
    shots = df[(df["team_name"] == team_name) & (df["event_family"].isin(["Scoring", "Misses"])) & (df["shot_zone"] != "Unknown")].copy()
    if shots.empty:
        return pd.DataFrame(), "Inferred Zone Map"
    rim = [(-12, 25), (0, 25), (12, 25), (-22, 52), (0, 55), (22, 52), (-10, 85), (10, 85)]
    mid = [(-115, 145), (-85, 185), (-50, 165), (50, 165), (85, 185), (115, 145), (-5, 170)]
    arc = [(-218, 72), (218, 72), (-210, 118), (210, 118), (-160, 255), (-110, 275), (-60, 285), (0, 292), (60, 285), (110, 275), (160, 255)]
    ft = [(-18, 150), (0, 150), (18, 150)]
    zone_map = {"Rim": rim, "Midrange": mid, "3PT": arc, "FT": ft}
    coords_x, coords_y = [], []
    for idx, zone in enumerate(shots["shot_zone"].tolist()):
        pts = zone_map.get(zone, [(0, 190)])
        base_x, base_y = pts[idx % len(pts)]
        spread_x = ((idx % 3) - 1) * 6 if zone != "3PT" else ((idx % 2) - 0.5) * 8
        spread_y = ((idx % 4) - 1.5) * 5
        coords_x.append(base_x + spread_x)
        coords_y.append(base_y + spread_y)
    out = pd.DataFrame({
        "loc_x": coords_x,
        "loc_y": coords_y,
        "made": (shots["event_family"] == "Scoring").astype(int).values,
        "shot_type": np.where(shots["shot_zone"].eq("3PT"), "3PT Field Goal", np.where(shots["shot_zone"].eq("FT"), "Free Throw", "2PT Field Goal")),
        "team_name": team_name,
        "source_zone": shots["shot_zone"].values,
    })
    out["shot_value"] = np.where(out["shot_type"].str.contains("3PT", case=False), 3 * out["made"], np.where(out["shot_type"].str.contains("Free Throw", case=False), 1 * out["made"], 2 * out["made"]))
    out["expected_value"] = np.where(out["shot_type"].str.contains("3PT", case=False), 1.02, np.where(out["shot_type"].str.contains("Free Throw", case=False), 0.78, 0.94))
    out["two_pt_make"] = ((~out["shot_type"].str.contains("3PT|Free Throw", case=False, regex=True)) & (out["made"] == 1)).astype(int)
    out["two_pt_miss"] = ((~out["shot_type"].str.contains("3PT|Free Throw", case=False, regex=True)) & (out["made"] == 0)).astype(int)
    out["three_pt_make"] = ((out["shot_type"].str.contains("3PT", case=False)) & (out["made"] == 1)).astype(int)
    out["three_pt_miss"] = ((out["shot_type"].str.contains("3PT", case=False)) & (out["made"] == 0)).astype(int)
    out["ft_ending"] = (out["shot_type"].str.contains("Free Throw", case=False)).astype(int)
    out["mode_label"] = "Inferred Zone Map"
    return out, "Inferred Zone Map"


def build_team_shot_points(game_id: Optional[str], team_name: str, team_id: Optional[int], pbp_df: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
    if game_id and team_id and NBA_API_AVAILABLE:
        exact_df, mode = normalize_shot_locations(load_shot_locations(game_id, int(team_id)), team_name)
        if not exact_df.empty:
            return exact_df, mode
    return fallback_shot_map_from_pbp(pbp_df, team_name)


def build_hexbin(points_df: pd.DataFrame, hex_size: int = 26) -> pd.DataFrame:
    if points_df.empty:
        return pd.DataFrame()
    tmp = points_df.copy()
    for col in ["made", "shot_value", "expected_value", "two_pt_make", "two_pt_miss", "three_pt_make", "three_pt_miss", "ft_ending"]:
        if col not in tmp.columns:
            tmp[col] = 0
    tmp["q"] = np.round(tmp["loc_x"] / hex_size).astype(int)
    tmp["r"] = np.round(tmp["loc_y"] / (hex_size * 0.865)).astype(int)
    grouped = tmp.groupby(["q", "r", "team_name"], dropna=False).agg(
        attempts=("made", "size"),
        makes=("made", "sum"),
        points=("shot_value", "sum"),
        expected_value=("expected_value", "mean"),
        two_pt_make=("two_pt_make", "sum"),
        two_pt_miss=("two_pt_miss", "sum"),
        three_pt_make=("three_pt_make", "sum"),
        three_pt_miss=("three_pt_miss", "sum"),
        ft_endings=("ft_ending", "sum"),
    ).reset_index()
    grouped["x"] = grouped["q"] * hex_size
    grouped["y"] = grouped["r"] * (hex_size * 0.865)
    grouped["fg_pct"] = np.where(grouped["attempts"] > 0, grouped["makes"] / grouped["attempts"] * 100, np.nan)
    grouped["zone_label"] = np.select(
        [grouped["y"] < 45, grouped["y"] < 140, grouped["y"] < 255, grouped["x"].abs() >= 210],
        ["Restricted area", "Paint touch", "Arc zone", "Corner three"],
        default="Deep perimeter",
    )
    grouped["value_label"] = grouped["points"]
    return grouped


def heatmap_summary_table(hex_frames: List[pd.DataFrame]) -> pd.DataFrame:
    valid = [df for df in hex_frames if not df.empty]
    if not valid:
        return pd.DataFrame()
    combo = pd.concat(valid, ignore_index=True)
    return combo.groupby(["team_name", "zone_label"], dropna=False).agg(
        attempts=("attempts", "sum"),
        makes=("makes", "sum"),
        points=("points", "sum"),
        avg_expected_value=("expected_value", "mean"),
    ).reset_index().sort_values(["team_name", "attempts"], ascending=[True, False])


def team_heatmap_insight(hex_df: pd.DataFrame, team_name: str, mode_label: str) -> str:
    if hex_df.empty:
        return f"Not enough shot-location data for {team_name} in this feed — check back with the full API pull."
    top_zone = hex_df.groupby("zone_label", dropna=False).agg(attempts=("attempts", "sum"), points=("points", "sum"), makes=("makes", "sum")).reset_index().sort_values(["attempts", "points"], ascending=False).iloc[0]
    fg_pct = round((top_zone["makes"] / max(top_zone["attempts"], 1)) * 100, 1)
    src = "Exact coordinates" if mode_label == "True Shot Coordinates" else "Estimated from play-by-play"
    if top_zone["zone_label"] == "Corner three":
        return f"{src}: {team_name} camped out in the corners all night — serious floor-spacing intent that forces defenses to make hard rotations."
    if top_zone["zone_label"] == "Restricted area":
        return f"{src}: {team_name} attacked the rim relentlessly — {int(top_zone['points'])} points on {int(top_zone['attempts'])} attempts in the restricted area. That's a bully-ball blueprint."
    if fg_pct >= 50:
        return f"{src}: {team_name} found its sweet spot in the {top_zone['zone_label'].lower()}, knocking down {fg_pct}% there. When a team shoots that well from a single zone, opponents have to pick their poison."
    return f"{src}: {team_name} volume-hunted from the {top_zone['zone_label'].lower()}. The conversion rate was modest, but the aggression kept the defense honest."


def draw_half_court_shapes(col_index: int) -> List[Dict]:
    xref = f"x{'' if col_index == 1 else col_index}"
    yref = f"y{'' if col_index == 1 else col_index}"
    shapes = []
    line = dict(color="rgba(255,255,255,0.32)", width=2)
    light = dict(color="rgba(255,255,255,0.18)", width=1.3)
    shapes.append(dict(type="circle", xref=xref, yref=yref, x0=-7.5, y0=7.5, x1=7.5, y1=22.5, line=line))
    shapes.append(dict(type="rect", xref=xref, yref=yref, x0=-30, y0=-7.5, x1=30, y1=-12.5, line=dict(color="rgba(255,255,255,0.92)", width=3), fillcolor="rgba(0,0,0,0)"))
    shapes.append(dict(type="rect", xref=xref, yref=yref, x0=-80, y0=-47.5, x1=80, y1=142.5, line=line))
    shapes.append(dict(type="rect", xref=xref, yref=yref, x0=-60, y0=-47.5, x1=60, y1=142.5, line=line))
    shapes.append(dict(type="circle", xref=xref, yref=yref, x0=-60, y0=82.5, x1=60, y1=202.5, line=line))
    shapes.append(dict(type="path", xref=xref, yref=yref, path="M -220 -47.5 L -220 92.5", line=line))
    shapes.append(dict(type="path", xref=xref, yref=yref, path="M 220 -47.5 L 220 92.5", line=line))
    shapes.append(dict(type="path", xref=xref, yref=yref, path="M -220 92.5 Q 0 300 220 92.5", line=line))
    shapes.append(dict(type="path", xref=xref, yref=yref, path="M -250 -47.5 L -250 422.5", line=light))
    shapes.append(dict(type="path", xref=xref, yref=yref, path="M 250 -47.5 L 250 422.5", line=light))
    shapes.append(dict(type="path", xref=xref, yref=yref, path="M -250 422.5 L 250 422.5", line=light))
    shapes.append(dict(type="path", xref=xref, yref=yref, path="M -210 -47.5 L -210 92.5", line=dict(color="rgba(91,141,225,0.18)", width=1)))
    shapes.append(dict(type="path", xref=xref, yref=yref, path="M 210 -47.5 L 210 92.5", line=dict(color="rgba(91,141,225,0.18)", width=1)))
    return shapes


def metric_spec(metric: str) -> Tuple[str, str, str]:
    mapping = {
        "Attempts": ("attempts", "Blues", "Attempts"),
        "Makes": ("makes", "Greens", "Makes"),
        "FG%": ("fg_pct", "YlGn", "FG%"),
        "Points": ("points", "Oranges", "Points"),
        "Expected Value": ("expected_value", "Purples", "Expected value"),
    }
    return mapping[metric]


def shot_heatmap_figure(away_hex: pd.DataFrame, home_hex: pd.DataFrame, meta: Dict, heat_metric: str) -> go.Figure:
    metric_col, colorscale, label = metric_spec(heat_metric)
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.06, subplot_titles=(f"{meta['away_team']} shot chart heatmap", f"{meta['home_team']} shot chart heatmap"))
    panels = [(meta['away_team'], away_hex, 1), (meta['home_team'], home_hex, 2)]
    max_val = 0
    for _, hex_df, _ in panels:
        if not hex_df.empty and metric_col in hex_df.columns:
            max_val = max(max_val, float(pd.to_numeric(hex_df[metric_col], errors="coerce").fillna(0).max()))
    max_val = max(max_val, 1.0)

    for team_name, hex_df, col in panels:
        if not hex_df.empty:
            metric_values = pd.to_numeric(hex_df[metric_col], errors="coerce").fillna(0)
            size_values = 14 + np.sqrt(hex_df["attempts"].clip(lower=1)) * 9
            fig.add_trace(go.Scatter(
                x=hex_df["x"], y=hex_df["y"], mode="markers", name=team_name,
                marker=dict(
                    size=size_values,
                    color=metric_values,
                    colorscale=colorscale,
                    cmin=0,
                    cmax=max_val,
                    opacity=0.90,
                    symbol="hexagon",
                    line=dict(color="rgba(255,255,255,0.18)", width=1),
                    colorbar=dict(title=label, x=1.02) if col == 2 else None,
                ),
                customdata=np.stack([
                    hex_df["attempts"],
                    hex_df["makes"],
                    hex_df["points"],
                    hex_df["fg_pct"].round(1),
                    hex_df["expected_value"].round(2),
                    hex_df["zone_label"],
                ], axis=1),
                hovertemplate="Zone: %{customdata[5]}<br>Attempts: %{customdata[0]}<br>Makes: %{customdata[1]}<br>Points: %{customdata[2]}<br>FG%: %{customdata[3]}<br>Expected value: %{customdata[4]}<extra></extra>",
                showlegend=False,
            ), row=1, col=col)
        for shape in draw_half_court_shapes(col):
            fig.add_shape(shape)
        fig.update_xaxes(range=[-255, 255], showgrid=False, zeroline=False, visible=False, row=1, col=col)
        fig.update_yaxes(range=[-55, 425], showgrid=False, zeroline=False, visible=False, row=1, col=col, scaleanchor=f"x{'' if col == 1 else col}", scaleratio=1)
    layout = _retro_chart_layout()
    layout.update(dict(
        height=700, margin=dict(l=10, r=30, t=70, b=10),
        plot_bgcolor="#07152b",
    ))
    fig.update_layout(**layout)
    for ann in fig.layout.annotations:
        ann.font = dict(family="'Press Start 2P', monospace", size=9, color="#00ffff")
    return fig


def render_header(meta: Dict) -> None:
    away_abbr = TEAM_META.get(meta['away_team'], {}).get('abbr', 'AWY')
    home_abbr = TEAM_META.get(meta['home_team'], {}).get('abbr', 'HME')
    winner_flag = ' ▶ W' if meta['winner'] == meta['away_team'] else ''
    winner_flag_h = ' ▶ W' if meta['winner'] == meta['home_team'] else ''
    st.markdown('<div class="header-shell">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.25, 0.8, 1.25])
    with c1:
        st.markdown(f'''
        <div class="team-band" style="background: linear-gradient(135deg, {meta['away_colors']['primary']}cc, {meta['away_colors']['secondary']}55); position:relative;">
          <div class="small-label" style="color:rgba(0,255,255,0.8)">&#9658; AWAY TEAM</div>
          <div class="kpi" style="color:#ffd700; font-size:1rem; margin:0.3rem 0;">{away_abbr}{winner_flag}</div>
          <div style="font-family:\'VT323\',monospace; color:rgba(224,244,255,0.85); font-size:1rem;">{meta['away_team']}</div>
          <div style="font-family:\'Press Start 2P\',monospace; font-size:1.5rem; color:#ffd700; text-shadow:0 0 16px rgba(255,215,0,0.8); margin-top:0.4rem;">{meta['away_score']}</div>
        </div>''', unsafe_allow_html=True)
    with c2:
        date_str = meta.get('date') or ''
        st.markdown(f'''
        <div class="score-center" style="text-align:center;">
          <div style="font-family:\'Press Start 2P\',monospace; font-size:0.4rem; color:#00ffff; text-shadow:0 0 8px #00ffff; letter-spacing:0.1em; margin-bottom:0.4rem;">FINAL SCORE</div>
          <div style="font-family:\'Press Start 2P\',monospace; font-size:1.4rem; color:#ffd700; text-shadow:0 0 20px rgba(255,215,0,0.9);">{meta['away_score']}&nbsp;-&nbsp;{meta['home_score']}</div>
          <div style="font-family:\'VT323\',monospace; color:#7ab8d4; font-size:1rem; margin-top:0.3rem;">{date_str}</div>
          <div style="font-family:\'Press Start 2P\',monospace; font-size:0.38rem; color:#ff00cc; text-shadow:0 0 8px #ff00cc; margin-top:0.3rem; letter-spacing:0.08em;">&#9670; {meta['winner']} WINS &#9670;</div>
        </div>''', unsafe_allow_html=True)
    with c3:
        st.markdown(f'''
        <div class="team-band" style="background: linear-gradient(135deg, {meta['home_colors']['primary']}cc, {meta['home_colors']['secondary']}55);">
          <div class="small-label" style="color:rgba(0,255,255,0.8)">&#9658; HOME TEAM</div>
          <div class="kpi" style="color:#ffd700; font-size:1rem; margin:0.3rem 0;">{home_abbr}{winner_flag_h}</div>
          <div style="font-family:\'VT323\',monospace; color:rgba(224,244,255,0.85); font-size:1rem;">{meta['home_team']}</div>
          <div style="font-family:\'Press Start 2P\',monospace; font-size:1.5rem; color:#ffd700; text-shadow:0 0 16px rgba(255,215,0,0.8); margin-top:0.4rem;">{meta['home_score']}</div>
        </div>''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def read_uploaded_csv(uploaded_file) -> pd.DataFrame:
    try:
        return pd.read_csv(uploaded_file)
    except Exception:
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file, encoding="latin1")


def to_csv_download(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def installation_and_notes() -> str:
    return """
Required installation commands:

```bash
pip install streamlit pandas plotly nba_api numpy requests
```

Run command:

```bash
streamlit run app.py
```

Version 0.6.0 — Retro 16-bit arcade reskin:
- Full dark navy/black background with CRT scanline overlay (CSS-only).
- Neon cyan, magenta, gold, and green accent palette throughout.
- Press Start 2P font for headings/labels, VT323 for body text (Google Fonts via CSS import).
- Chunky pixel borders, neon box-shadow glow on all panels and buttons.
- Section headers renamed: POSTGAME STORY MODE, SHOT PROFILE ARENA, KEYS TO VICTORY,
  MOMENTUM METER, PLAYER POWER-UPS, TURNING POINT, SCORING RUNS, CLUTCH TIME, etc.
- Arcade scoreboard header with WINNER WINS badge, neon score display, and SCOREBOARD label.
- Retro arcade banner on app title with blinking INSERT COIN prompt.
- Buttons styled as console menu actions (chunky gold border, glow hover effect).
- Plotly charts updated to dark HUD theme: dark navy bg, cyan grid dots, VT323 axis fonts,
  neon period lines, diamond turning-point marker.
- _retro_chart_layout() and _retro_axis() helpers for consistent chart theming.
- Keys-to-victory bullets styled with gold left-border and VT323 font.
- Scrollbars, expanders, dataframes, and alerts all themed to match retro palette.
- No new dependencies; preserves all existing functionality and CSV fallback.

Version 0.5.0 — Shot Profile visual:
- Replaced inline shot-zone raw table with a two-panel Shot Profile chart.
- Left panel: Shooting Efficiency (FG%) — markers per team at each shot zone with
  percentage labels above (e.g. "63.6%"). Y-axis fixed 0–115%.
- Right panel: Volume & Frequency — attempt counts per zone with numeric labels.
  Y-axis auto-ranged from zero.
- Zones ordered logically: 3PT, FT, Rim, Midrange; unknown categories appended.
- Team colors sourced from the TEAM_META palette; fallback two-color palette when
  a team is not in the lookup.
- Dark rounded-card wrapper (heat-shell class) consistent with the heatmap section.
- Raw shot zone data preserved in a collapsible "View raw shot zone data" expander.
- shot_profile_figure() helper added; existing shot_zone_chart() and all
  downstream data references are untouched.
- CSV upload compatibility unchanged.

Version 0.4.4 — Game Story voice overhaul:
- Replaced robotic stat-dump Game Story language with energetic NBA TV analyst prose.
- Story now opens with a context-aware lede (blowout vs. nail-biter vs. comfortable win).
- Momentum runs are framed as narrative turning points, not data dumps.
- Turning point uses punchy, scene-setting language ("Circle Q4 7:39 in your notebook...").
- Shooting geography phrasing tightened — zone stats only when they drive the story.
- Clutch-time copy scaled by number of lead changes.
- Player impact closes the story with highlight-reel framing.
- Keys-to-game bullets rewritten for sharper, more conversational flow.
- Heatmap insight text updated with more vivid positional language.
- No new dependencies or UI changes; no dropdown added.

Version 0.4.3 — Basketball clock formatting:
- Game clock/time values now display in normal basketball format (e.g. "Q4 7:39",
  "Q1 12:00", "OT 3:05") instead of raw NBA API ISO duration strings like
  "PT07M39.00S".
- Added format_clock() helper that handles PT##M##.##S, PT##S, plain M:SS, and
  already-normalised strings robustly.
- Added format_period_clock() helper to combine period + clock into Q1–Q4 / OT / OT2…
  labels for display.
- clock_display column in the enriched DataFrame is now always human-readable.
- Raw "clock" column is preserved internally for all second-based calculations.
- CSV upload compatibility is unchanged.

Version 0.4.2 — Season-type dropdown:
- Added a "Season type" dropdown in the sidebar (Regular Season / Playoffs).
- Selecting Playoffs passes season_type_nullable="Playoffs" to LeagueGameFinder,
  so the game list shows only playoff matchups for the selected season.
- The season type is included in the fetch_games cache key, so switching between
  Regular Season and Playoffs loads the correct game list without clearing other state.
- CSV upload fallback is unaffected.

Version 0.4.1 heatmap upgrades:
- Explicit mode labeling: True Shot Coordinates vs Inferred Zone Map
- Heatmap metric toggle for Attempts, Makes, FG%, Points, and Expected Value
- Cleaner half-court geometry with clearer corner-three boundaries
- Better inferred placement logic for fallback shot maps
- More transparent heatmap storytelling and metric encoding

Known limitations:
- True-coordinate maps still depend on ShotChartDetail availability.
- Fallback mode is intentionally labeled as inferred, not exact.
- Expected Value is a lightweight heuristic, not a learned shot-quality model.
- If a season has no playoff data yet (e.g. current season before playoffs start),
  the game list will be empty when Playoffs is selected.
"""


def main() -> None:
    # ── Arcade title banner ──
    st.markdown(
        f'<div class="arcade-banner">'
        f'<span class="arcade-banner-title">🕹️ NBA ARCADE DASHBOARD 🕹️</span>'
        f'<span class="arcade-banner-sub">POSSESSION-AWARE GAME STORYTELLING ENGINE</span>'
        f'<span class="arcade-insert">► SELECT GAME AND PRESS START ◄</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.caption(f"v{APP_VERSION} — retro 16-bit arcade basketball dashboard")

    with st.sidebar:
        st.markdown("### 🕹️ GAME SELECT")
        source = st.radio("Data source", ["NBA API", "Local CSV backup"], index=0 if NBA_API_AVAILABLE else 1)
        season = st.selectbox("Season", ["2025-26", "2024-25", "2023-24"], index=0)
        season_type = st.selectbox(
            "Season type",
            SEASON_TYPE_OPTIONS,
            index=0,
            help="Switch between Regular Season and Playoffs game lists.",
        )
        uploaded = None
        games_df = pd.DataFrame()
        selected_game_id = None
        selected_game_date = None
        if source == "NBA API":
            if not NBA_API_AVAILABLE:
                st.error("nba_api is unavailable in this environment. Use the local CSV option.")
            else:
                with st.spinner("LOADING GAME ROSTER..."):
                    games_df = fetch_games(season=season, season_type=season_type, limit=120)
                if games_df.empty:
                    st.warning("No games returned for this season.")
                else:
                    label_to_id = dict(zip(games_df["LABEL"], games_df["GAME_ID"]))
                    selected_label = st.selectbox("Select game", list(label_to_id.keys()))
                    selected_game_id = label_to_id[selected_label]
                    selected_game_date = str(games_df.loc[games_df["GAME_ID"] == selected_game_id, "GAME_DATE"].iloc[0])
        else:
            uploaded = st.file_uploader("Upload play-by-play CSV", type=["csv"])
            st.caption("Use this when API access fails or for custom datasets.")
        load_clicked = st.button("PRESS START", use_container_width=True)
        st.markdown("---")
        st.markdown("### 🎨 HUD OPTIONS")
        heat_metric = st.selectbox("Heatmap metric", ["Attempts", "Makes", "FG%", "Points", "Expected Value"], index=0)
        st.caption("Changes the color scale on both team shot maps.")

    if not load_clicked:
        st.info("INSERT COIN: Choose a source, select a game or upload a CSV, then press START.")
        with st.expander("SETUP & PATCH NOTES"):
            st.code(installation_and_notes())
        return

    try:
        if source == "NBA API":
            raw = load_pbp_from_api(selected_game_id)
        else:
            if uploaded is None:
                st.error("Please upload a CSV file.")
                return
            raw = read_uploaded_csv(uploaded)
            selected_game_date = None
            selected_game_id = None
        if raw.empty:
            raise RuntimeError("The loaded play-by-play dataset is empty for this game.")
    except Exception as exc:
        st.exception(exc)
        return

    df = normalize_columns(raw)
    df, meta = enrich_game(df, game_date=selected_game_date)
    team_ids = {
        meta["away_team"]: int(df.loc[df["team_name"] == meta["away_team"], "team_id"].dropna().mode().iloc[0]) if not df.loc[df["team_name"] == meta["away_team"], "team_id"].dropna().empty else None,
        meta["home_team"]: int(df.loc[df["team_name"] == meta["home_team"], "team_id"].dropna().mode().iloc[0]) if not df.loc[df["team_name"] == meta["home_team"], "team_id"].dropna().empty else None,
    }
    df = compute_momentum(df, meta)
    df, poss_summary = compute_possessions(df, meta)
    runs_df = detect_runs(df, meta)
    turning = detect_turning_point(df, runs_df, meta)
    clutch = detect_clutch(df, meta)
    impact_df = player_impact_during_runs(df, runs_df)
    seg_df = segment_summary(df, meta, poss_summary)
    ratings_df = compute_team_ratings(poss_summary, meta)
    subs_df = parse_substitutions(df)
    shot_df = shot_zone_summary(df)

    away_points_df, away_mode = build_team_shot_points(selected_game_id, meta["away_team"], team_ids.get(meta["away_team"]), df)
    home_points_df, home_mode = build_team_shot_points(selected_game_id, meta["home_team"], team_ids.get(meta["home_team"]), df)
    away_hex = build_hexbin(away_points_df)
    home_hex = build_hexbin(home_points_df)
    heatmap_summary = heatmap_summary_table([away_hex, home_hex])

    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🎮 GAME FILTERS")
        period_choices = sorted([int(p) for p in df["period"].dropna().unique().tolist()])
        selected_periods = st.multiselect("Quarters", period_choices, default=period_choices)
        event_choices = sorted(df["event_family"].dropna().unique().tolist())
        default_events = [e for e in event_choices if e != "Other"] or event_choices
        selected_events = st.multiselect("Event groups", event_choices, default=default_events)
        run_options = ["All game"] + ([f"{row.team} {row.run_label} ({row.start_time} → {row.end_time})" for row in runs_df.itertuples()] if not runs_df.empty else [])
        selected_run = st.selectbox("Focus on run", run_options, index=0)
        selected_run_idx = run_options.index(selected_run) - 1
        st.markdown("---")
        st.download_button("EXPORT EVENTS CSV", data=to_csv_download(df), file_name="events.csv", mime="text/csv", use_container_width=True)
        if not poss_summary.empty:
            st.download_button("EXPORT POSSESSIONS CSV", data=to_csv_download(poss_summary), file_name="possessions.csv", mime="text/csv", use_container_width=True)
        if not shot_df.empty:
            st.download_button("EXPORT SHOT ZONES CSV", data=to_csv_download(shot_df), file_name="shot_zones.csv", mime="text/csv", use_container_width=True)
        if not heatmap_summary.empty:
            st.download_button("EXPORT HEATMAP CSV", data=to_csv_download(heatmap_summary), file_name="shot_heatmap_summary.csv", mime="text/csv", use_container_width=True)

    filtered_df = filter_dataset(df, selected_periods, selected_events, selected_run_idx, runs_df)
    if filtered_df.empty:
        st.warning("The current filters removed all events. Adjust the sidebar filters to restore the game view.")
        return

    filtered_runs = runs_df.copy()
    if selected_run_idx >= 0 and not runs_df.empty:
        filtered_runs = runs_df.iloc[[selected_run_idx]].copy()

    poss_filtered = poss_summary[poss_summary["period"].isin(selected_periods)].copy() if not poss_summary.empty else poss_summary
    if selected_run_idx >= 0 and not filtered_runs.empty:
        run = filtered_runs.iloc[0]
        poss_filtered = poss_filtered[(poss_filtered["start_elapsed"] >= run["start_elapsed"]) & (poss_filtered["end_elapsed"] <= run["end_elapsed"])]

    story = game_story(meta, filtered_runs if not filtered_runs.empty else runs_df, turning, clutch, impact_df, ratings_df, shot_df, heatmap_summary)
    keys = keys_to_game(filtered_df, meta, filtered_runs if not filtered_runs.empty else runs_df, poss_filtered, clutch)

    render_header(meta)

    # ── ARCADE STAT CARDS ──
    row1 = st.columns([0.8, 0.8, 0.8, 0.9, 1.0])
    with row1[0]:
        st.markdown(f'<div class="metric-card retro-panel-gold"><div class="small-label">WINNER</div><div class="kpi">{meta["winner"]}</div><div class="subtle">MARGIN: {abs(meta["home_score"] - meta["away_score"])} PTS</div></div>', unsafe_allow_html=True)
    with row1[1]:
        st.markdown(f'<div class="metric-card"><div class="small-label">POSSESSIONS</div><div class="kpi">{poss_summary["possession_id"].nunique() if not poss_summary.empty else 0}</div><div class="subtle">TRACKED BY ENGINE</div></div>', unsafe_allow_html=True)
    with row1[2]:
        st.markdown(f'<div class="metric-card"><div class="small-label">SHOT ZONES</div><div class="kpi">{shot_df["shot_zone"].nunique() if not shot_df.empty else 0}</div><div class="subtle">RIM / MID / 3PT / FT</div></div>', unsafe_allow_html=True)
    with row1[3]:
        clutch_text = "CLUTCH" if clutch.get("qualified") else "NO CLUTCH"
        clutch_color = "#ff00cc" if clutch.get("qualified") else "rgba(0,255,255,0.25)"
        st.markdown(f'<div class="metric-card" style="border-color:{clutch_color}"><div class="small-label">CLUTCH TIME</div><div class="kpi">{clutch_text}</div><div class="subtle">LAST 5:00 &lt;=5 PTS</div></div>', unsafe_allow_html=True)
    with row1[4]:
        shot_count = len(away_points_df) + len(home_points_df)
        st.markdown(f'<div class="metric-card"><div class="small-label">MAPPED SHOTS</div><div class="kpi">{shot_count}</div><div class="subtle">COORD OR INFERRED</div></div>', unsafe_allow_html=True)

    # ── KEYS TO VICTORY ──
    st.markdown("## KEYS TO VICTORY")
    for note in keys:
        st.markdown(
            f'<div style="font-family: VT323,monospace; font-size:1.1rem; color:#e0f4ff; border-left:3px solid #ffd700; padding-left:0.8rem; margin-bottom:0.5rem;">&#9658; {note}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("## SCORE PROGRESSION")
    st.plotly_chart(score_chart(filtered_df, meta), use_container_width=True)

    st.markdown("## MOMENTUM METER")
    st.plotly_chart(momentum_chart(filtered_df, meta, filtered_runs if not filtered_runs.empty else runs_df, turning), use_container_width=True)

    st.markdown("## POSSESSION VIEW")
    st.plotly_chart(possession_chart(poss_filtered, meta), use_container_width=True)

    c1, c2 = st.columns([1.05, 0.95])
    with c1:
        st.markdown("## PLAYER POWER-UPS")
        if ratings_df.empty:
            st.info("Team possession ratings unavailable.")
        else:
            st.dataframe(ratings_df, use_container_width=True, hide_index=True)
    with c2:
        st.markdown("## HALFTIME STATS")
        if seg_df.empty:
            st.info("No segment summary available.")
        else:
            st.dataframe(seg_df, use_container_width=True, hide_index=True)

    st.markdown("## SHOT PROFILE ARENA")
    st.plotly_chart(shot_zone_chart(shot_df, meta), use_container_width=True)
    # ── Shot Profile visual ──────────────────────────────────────────
    if not shot_df.empty:
        st.markdown(
            '<div class="heat-shell" style="margin-top:0.6rem; margin-bottom:0.6rem;">'
            '<div class="heat-title">SHOT PROFILE ARENA</div>'
            '<div class="heat-subtle">Shooting efficiency and volume by zone — markers colored by team.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(shot_profile_figure(shot_df, meta), use_container_width=True)
    with st.expander("RAW SHOT ZONE DATA", expanded=False):
        if shot_df.empty:
            st.info("No shot zone data available.")
        else:
            st.dataframe(shot_df, use_container_width=True, hide_index=True)

    st.markdown("## SHOT CHART HEATMAPS")
    st.markdown('<div class="heat-shell">', unsafe_allow_html=True)
    h1, h2 = st.columns([1.5, 0.5])
    with h1:
        st.markdown(
            '<div class="heat-title">SHOT CHART HEATMAPS</div>'
            '<div class="heat-subtle">Maps separate exact coordinate views from inferred zone maps. Toggle metric to compare attempts, makes, FG%, points, and expected value.</div>',
            unsafe_allow_html=True,
        )
    with h2:
        st.markdown(
            '<div class="heat-note"><b>INTEGRITY NOTE:</b> True-coordinate heatmaps from NBA coordinates. Inferred maps are approximations from play-by-play zones.</div>',
            unsafe_allow_html=True,
        )
    mode1, mode2, mode3 = st.columns([0.8, 0.8, 0.8])
    with mode1:
        st.markdown(
            f'<div class="card"><div class="small-label">{meta["away_team"]}</div>'
            f'<div class="story">MODE: {away_mode}</div>'
            f'<div class="heat-subtle">{team_heatmap_insight(away_hex, meta["away_team"], away_mode)}</div></div>',
            unsafe_allow_html=True,
        )
    with mode2:
        st.markdown(
            f'<div class="card"><div class="small-label">{meta["home_team"]}</div>'
            f'<div class="story">MODE: {home_mode}</div>'
            f'<div class="heat-subtle">{team_heatmap_insight(home_hex, meta["home_team"], home_mode)}</div></div>',
            unsafe_allow_html=True,
        )
    with mode3:
        st.markdown(
            f'<div class="card"><div class="small-label">HUD METRIC</div>'
            f'<div class="story">{heat_metric}</div>'
            '<div class="heat-subtle">Both panels share the same metric and color scale.</div></div>',
            unsafe_allow_html=True,
        )
    st.plotly_chart(shot_heatmap_figure(away_hex, home_hex, meta, heat_metric), use_container_width=True)
    l1, l2, l3 = st.columns([0.95, 0.95, 0.6])
    with l1:
        away_points_mapped = int(away_hex["points"].sum()) if not away_hex.empty else 0
        away_ppp = round(away_points_mapped / max(len(poss_summary[poss_summary["possession_team"] == meta["away_team"]]), 1), 2) if not poss_summary.empty else 0
        st.markdown(
            f'<div class="card"><div class="small-label">{meta["away_team"]}</div>'
            f'<div class="kpi">PTS MAPPED: {away_points_mapped}</div>'
            f'<div class="story">PPP: {away_ppp}</div>'
            '<div class="heat-subtle">Corner-three and rim clusters separated in geometry.</div></div>',
            unsafe_allow_html=True,
        )
    with l2:
        home_points_mapped = int(home_hex["points"].sum()) if not home_hex.empty else 0
        home_ppp = round(home_points_mapped / max(len(poss_summary[poss_summary["possession_team"] == meta["home_team"]]), 1), 2) if not poss_summary.empty else 0
        st.markdown(
            f'<div class="card"><div class="small-label">{meta["home_team"]}</div>'
            f'<div class="kpi">PTS MAPPED: {home_points_mapped}</div>'
            f'<div class="story">PPP: {home_ppp}</div>'
            '<div class="heat-subtle">Use metric toggle for different color encodings.</div></div>',
            unsafe_allow_html=True,
        )
    with l3:
        st.markdown(
            '<div class="card"><div class="small-label">HUD MODES</div>'
            '<div class="heat-subtle">&#9658; Explicit mode labels<br>&#9658; Metric toggle<br>&#9658; Corner-three geometry<br>&#9658; Inferred fallback label</div></div>',
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)
    if not heatmap_summary.empty:
        st.dataframe(heatmap_summary, use_container_width=True, hide_index=True)

    c3, c4 = st.columns([1.1, 0.9])
    with c3:
        st.markdown("## SCORING RUNS")
        if runs_df.empty:
            st.warning("No qualifying scoring runs were detected with the default thresholds.")
        else:
            display_runs = (filtered_runs if not filtered_runs.empty else runs_df)[["team", "run_label", "start_time", "end_time", "quarter", "score_before", "score_after", "top_players", "key_plays"]].copy()
            st.dataframe(display_runs, use_container_width=True, hide_index=True)
    with c4:
        st.markdown("## TURNING POINT")
        if turning:
            st.markdown(
                f'<div class="card turning">'
                '<div class="small-label">TURNING POINT DETECTED</div>'
                f'<div class="kpi">&#9658; {turning["team"]}</div>'
                f'<div class="story">{turning["description"]}</div>'
                f'<div class="subtle">Q{turning["quarter"]} &bull; {turning["clock"]} &bull; {turning["score"]}</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("No turning point could be inferred.")

    with st.expander("ROTATION LOG", expanded=False):
        if subs_df.empty:
            st.info("No substitutions were parsed from the available feed.")
        else:
            st.dataframe(subs_df.head(40), use_container_width=True, hide_index=True)

    with st.expander("PLAYER IMPACT STATS", expanded=False):
        if impact_df.empty:
            st.info("Player impact during runs could not be fully extracted from the available event structure.")
        else:
            st.dataframe(impact_df, use_container_width=True, hide_index=True)

    st.markdown("## CLUTCH TIME")
    if clutch.get("qualified"):
        c7, c8 = st.columns([0.85, 1.35])
        with c7:
            st.markdown(
                f'<div class="card" style="border-color:#ff00cc; box-shadow:0 0 12px rgba(255,0,204,0.4)">'
                '<div class="small-label">CLUTCH SUMMARY</div>'
                f'<div class="kpi">{clutch["plays"]} SCORING PLAYS</div>'
                f'<div class="subtle">LEAD CHANGES: {clutch["lead_changes"]} &bull; '
                f'{meta["away_team"]}: {clutch["away_points"]} &bull; {meta["home_team"]}: {clutch["home_points"]}</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        with c8:
            st.dataframe(clutch["key_plays"], use_container_width=True, hide_index=True)
    else:
        st.info("This game did not enter the defined clutch window.")

    with st.expander("EVENT LOG", expanded=False):
        event_log = filtered_df[["period_label", "clock_display", "team_name", "player_name", "event_family", "shot_zone", "description", "score_away", "score_home"]].copy()
        st.dataframe(event_log, use_container_width=True, hide_index=True)

    st.markdown("## POSTGAME STORY MODE")
    st.markdown(f'<div class="card retro-panel"><div class="story">{story}</div></div>', unsafe_allow_html=True)

    with st.expander("SETUP, COMMANDS & PATCH NOTES"):
        st.code(installation_and_notes())


if __name__ == "__main__":
    main()
