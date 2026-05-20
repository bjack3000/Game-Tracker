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

APP_VERSION = "0.4.3"

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


st.set_page_config(page_title="NBA Game Storyboard", page_icon="🏀", layout="wide")

CUSTOM_CSS = """
<style>
:root {
    --bg:#f6f8fc; --surface:#ffffff; --surface-2:#eef3fb; --text:#142033; --muted:#66758a;
    --border:rgba(20,32,51,0.10); --shadow:0 10px 28px rgba(17,24,39,0.08); --accent:#f97316;
}
.stApp {
    background:
      radial-gradient(circle at top right, rgba(249,115,22,0.10), transparent 20%),
      radial-gradient(circle at top left, rgba(59,130,246,0.10), transparent 22%),
      linear-gradient(180deg, #f9fbff 0%, #f4f7fb 100%);
    color: var(--text);
}
.block-container {max-width:1500px; padding-top:1.2rem; padding-bottom:3rem;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#f8fbff 0%,#eef4fb 100%); border-right:1px solid var(--border);}
.card,.metric-card {background:var(--surface); border:1px solid var(--border); border-radius:18px; padding:1rem 1.1rem; box-shadow:var(--shadow);}
.header-shell {border-radius:24px; padding:1.2rem; margin-bottom:1rem; background:linear-gradient(180deg,#ffffff 0%,#f8fbff 100%); border:1px solid var(--border); box-shadow:var(--shadow);}
.team-band {border-radius:18px; padding:1rem; color:white; min-height:118px; box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08);}
.score-center {display:flex; flex-direction:column; justify-content:center; align-items:center; min-height:118px;}
.kpi {font-size:2rem; font-weight:800; line-height:1.05; color:var(--text);}
.subtle {color:var(--muted); font-size:.9rem;}
.story {font-size:1.01rem; line-height:1.68; color:#273548;}
.turning {border-left:4px solid var(--accent);}
.small-label {font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; color:#78879b;}
.heat-shell {background: radial-gradient(circle at top, rgba(255,255,255,0.06), transparent 28%), linear-gradient(180deg,#111827 0%,#0f1723 100%); border-radius:24px; border:1px solid rgba(255,255,255,0.08); box-shadow:0 16px 40px rgba(15,23,35,0.22); padding:1rem 1rem 1.2rem 1rem;}
.heat-title {color:#eef4ff; font-size:1.8rem; font-weight:800; margin-bottom:.2rem;}
.heat-subtle {color:rgba(238,244,255,.74); font-size:.95rem;}
.heat-note {background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.08); color:rgba(238,244,255,.88); border-radius:14px; padding:.8rem .9rem;}
.legend-item {display:flex; align-items:center; gap:.55rem; color:#eef4ff; margin-bottom:.45rem;}
.legend-dot {width:12px; height:12px; border-radius:3px; display:inline-block;}
div[data-testid="stMetricValue"] {color:var(--text);}
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
        notes.append(f"Biggest burst: {top_run['team']} authored a {top_run['run_label']} run from {top_run['start_time']} to {top_run['end_time']}.")
    if not poss_summary.empty:
        explosive = poss_summary.sort_values(["points", "duration_seconds"], ascending=[False, True]).iloc[0]
        notes.append(f"Fastest damaging possession stretch: {explosive['possession_team']} posted {int(explosive['points'])} points in a possession ending with '{explosive['last_description']}'.")
    top_margin_row = df.iloc[df["absolute_margin"].idxmax()] if not df.empty else None
    if top_margin_row is not None:
        leader = meta["home_team"] if top_margin_row["score_margin_home"] > 0 else meta["away_team"]
        notes.append(f"Maximum separation came at {top_margin_row['period_label']} {top_margin_row['clock_display']}, when {leader} led by {int(abs(top_margin_row['score_margin_home']))}.")
    if clutch.get("qualified"):
        notes.append(f"Clutch factor: the game stayed within five in the last five minutes and featured {clutch['lead_changes']} late lead changes.")
    return notes[:4]


def game_story(meta: Dict, runs_df: pd.DataFrame, turning: Optional[Dict], clutch: Dict, impact_df: pd.DataFrame, ratings_df: pd.DataFrame, shot_df: pd.DataFrame, heatmaps_df: pd.DataFrame) -> str:
    winner = meta["winner"]
    loser = meta["away_team"] if winner == meta["home_team"] else meta["home_team"]
    winner_score = meta["home_score"] if winner == meta["home_team"] else meta["away_score"]
    loser_score = meta["away_score"] if winner == meta["home_team"] else meta["home_score"]
    parts = [f"{winner} beat {loser} {winner_score}-{loser_score}, and the Version 0.4.1 profile now separates true-coordinate shot maps from inferred zone maps so the shot story is clearer about what is measured and what is estimated."]
    if not ratings_df.empty:
        winner_row = ratings_df[ratings_df["team"] == winner].iloc[0]
        parts.append(f"At the possession level, {winner} posted an estimated offensive rating of {winner_row['off_rating']} while controlling {winner_row['possessions']} possessions in the tracked feed.")
    if not runs_df.empty:
        top_run = runs_df.iloc[0]
        parts.append(f"The biggest run was a {top_run['run_label']} surge by {top_run['team']} from {top_run['start_time']} to {top_run['end_time']}.")
    if turning:
        q_label = f"Q{turning['quarter']}" if turning['quarter'] <= 4 else f"OT{turning['quarter'] - 4}"
        parts.append(f"The likely turning point came in {q_label} at {turning['clock']}, when {turning['team']} produced this sequence: {turning['description']} The score was {turning['score']}.")
    if not heatmaps_df.empty:
        top_hex = heatmaps_df.sort_values(["attempts", "points"], ascending=False).iloc[0]
        parts.append(f"Spatially, the heaviest shot concentration came from the {top_hex['zone_label']} lane for {top_hex['team_name']}, where the team logged {int(top_hex['attempts'])} attempts and {int(top_hex['points'])} points.")
    elif not shot_df.empty:
        top_zone = shot_df.sort_values(["points", "attempts"], ascending=False).iloc[0]
        parts.append(f"The most productive scoring zone in the tracked data was {top_zone['shot_zone']} for {top_zone['team_name']}, yielding {int(top_zone['points'])} points across {int(top_zone['attempts'])} attempts.")
    if clutch.get("qualified"):
        parts.append(f"It also qualified as a clutch game, with {clutch['plays']} scoring plays in the final five minutes while the margin stayed within five.")
    if not impact_df.empty:
        top_player = impact_df.sort_values(["points", "scoring_plays"], ascending=False).iloc[0]
        parts.append(f"Within the biggest swing segments, {top_player['player']} stood out most, delivering {int(top_player['points'])} points across {int(top_player['scoring_plays'])} scoring plays.")
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
            fig.add_vline(x=boundary, line=dict(color="rgba(20,32,51,0.12)", dash="dot"))


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


def score_chart(df: pd.DataFrame, meta: Dict) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["elapsed_game_seconds"], y=df["score_home"], mode="lines+markers", name=meta["home_team"], line=dict(color=meta["home_colors"]["primary"], width=3), marker=dict(size=5)))
    fig.add_trace(go.Scatter(x=df["elapsed_game_seconds"], y=df["score_away"], mode="lines+markers", name=meta["away_team"], line=dict(color=meta["away_colors"]["primary"], width=3), marker=dict(size=5)))
    add_period_lines(fig, df)
    ticks = period_ticks(df)
    fig.update_layout(template="plotly_white", height=380, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", y=1.08), xaxis=dict(title="Game clock", tickmode="array", tickvals=ticks, ticktext=[format_axis_time(v) for v in ticks], gridcolor="rgba(20,32,51,0.06)"), yaxis=dict(title="Score", gridcolor="rgba(20,32,51,0.06)"))
    return fig


def momentum_chart(df: pd.DataFrame, meta: Dict, runs_df: pd.DataFrame, turning: Optional[Dict]) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["elapsed_game_seconds"], y=df["raw_momentum"], mode="lines", name="Raw momentum", line=dict(color="#243447", width=2)))
    fig.add_trace(go.Scatter(x=df["elapsed_game_seconds"], y=np.where(df["raw_momentum"] >= 0, df["raw_momentum"], 0), fill="tozeroy", mode="none", name=meta["home_team"], fillcolor=hex_to_rgba(meta["home_colors"]["primary"], 0.28)))
    fig.add_trace(go.Scatter(x=df["elapsed_game_seconds"], y=np.where(df["raw_momentum"] <= 0, df["raw_momentum"], 0), fill="tozeroy", mode="none", name=meta["away_team"], fillcolor=hex_to_rgba(meta["away_colors"]["primary"], 0.24)))
    for _, run in runs_df.head(6).iterrows():
        color = meta["home_colors"]["primary"] if run["team"] == meta["home_team"] else meta["away_colors"]["primary"]
        fig.add_vrect(x0=run["start_elapsed"], x1=run["end_elapsed"], fillcolor=hex_to_rgba(color, 0.10), line_width=0)
        fig.add_annotation(x=(run["start_elapsed"] + run["end_elapsed"]) / 2, y=df["raw_momentum"].max() * 0.88 if run["team"] == meta["home_team"] else df["raw_momentum"].min() * 0.88, text=f"{run['team']} {run['run_label']}", showarrow=False, font=dict(size=11, color="#334155"))
    if turning and not df.empty:
        idx = (df["elapsed_game_seconds"] - turning["elapsed"]).abs().idxmin()
        yval = float(df.loc[idx, "raw_momentum"])
        fig.add_trace(go.Scatter(x=[turning["elapsed"]], y=[yval], mode="markers+text", text=["🏀"], textposition="top center", marker=dict(size=18, color="#f97316", symbol="circle"), name="Turning point"))
    add_period_lines(fig, df)
    ticks = period_ticks(df)
    fig.add_hline(y=0, line=dict(color="rgba(20,32,51,0.25)", dash="dash"))
    fig.update_layout(template="plotly_white", height=420, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False, xaxis=dict(title="Game clock", tickmode="array", tickvals=ticks, ticktext=[format_axis_time(v) for v in ticks], gridcolor="rgba(20,32,51,0.06)"), yaxis=dict(title=f"Momentum ← {meta['away_team']} | {meta['home_team']} →", gridcolor="rgba(20,32,51,0.06)"))
    return fig


def possession_chart(poss_summary: pd.DataFrame, meta: Dict) -> go.Figure:
    fig = go.Figure()
    if poss_summary.empty:
        return fig
    temp_all = poss_summary.copy()
    temp_all["poss_index"] = range(1, len(temp_all) + 1)
    for team, color in [(meta["away_team"], meta["away_colors"]["primary"]), (meta["home_team"], meta["home_colors"]["primary"] )]:
        temp = temp_all[temp_all["possession_team"] == team]
        fig.add_trace(go.Bar(x=temp["poss_index"], y=temp["points"], name=team, marker_color=color, opacity=0.85, customdata=temp[["start_clock", "last_description"]], hovertemplate="Possession %{x}<br>Points: %{y}<br>Start: %{customdata[0]}<br>%{customdata[1]}<extra></extra>"))
    fig.update_layout(template="plotly_white", barmode="group", height=350, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(title="Possession number", gridcolor="rgba(20,32,51,0.06)"), yaxis=dict(title="Points on possession", gridcolor="rgba(20,32,51,0.06)"))
    return fig


def shot_zone_chart(shot_df: pd.DataFrame, meta: Dict) -> go.Figure:
    fig = go.Figure()
    if shot_df.empty:
        return fig
    zones = ["Rim", "Midrange", "3PT", "FT"]
    for team, color in [(meta["away_team"], meta["away_colors"]["primary"]), (meta["home_team"], meta["home_colors"]["primary"] )]:
        temp = shot_df[shot_df["team_name"] == team].set_index("shot_zone").reindex(zones).fillna(0).reset_index()
        fig.add_trace(go.Bar(x=temp["shot_zone"], y=temp["points"], name=team, marker_color=color, opacity=0.85, customdata=temp[["attempts", "makes", "fg_pct"]], hovertemplate="%{x}<br>Points: %{y}<br>Attempts: %{customdata[0]}<br>Makes: %{customdata[1]}<br>FG%: %{customdata[2]}<extra></extra>"))
    fig.update_layout(template="plotly_white", barmode="group", height=330, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(title="Shot zone", gridcolor="rgba(20,32,51,0.06)"), yaxis=dict(title="Points", gridcolor="rgba(20,32,51,0.06)"))
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
        return f"{team_name} does not have enough shot-location detail in the current feed."
    top_zone = hex_df.groupby("zone_label", dropna=False).agg(attempts=("attempts", "sum"), points=("points", "sum"), makes=("makes", "sum")).reset_index().sort_values(["attempts", "points"], ascending=False).iloc[0]
    fg_pct = round((top_zone["makes"] / max(top_zone["attempts"], 1)) * 100, 1)
    prefix = "Measured" if mode_label == "True Shot Coordinates" else "Estimated"
    if top_zone["zone_label"] == "Corner three":
        return f"{prefix} corner pressure: {team_name} showed notable volume along the corners, giving the shot map a strong spacing signature."
    if top_zone["zone_label"] == "Restricted area":
        return f"{prefix} rim pressure: {team_name} concentrated touches near the basket and turned that zone into {int(top_zone['points'])} points on {int(top_zone['attempts'])} attempts."
    if fg_pct >= 50:
        return f"{prefix} efficiency pocket: {team_name} found its best volume-efficiency mix in the {top_zone['zone_label'].lower()}, shooting {fg_pct}% there in the mapped sample."
    return f"{prefix} volume pocket: {team_name} worked most often from the {top_zone['zone_label'].lower()}, though the conversion rate there was more moderate than dominant."


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
    fig.update_layout(template="plotly_white", height=700, margin=dict(l=10, r=30, t=70, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#111827", font=dict(color="#eef4ff"))
    for ann in fig.layout.annotations:
        ann.font = dict(size=16, color="#f8fbff")
    return fig


def render_header(meta: Dict) -> None:
    st.markdown('<div class="header-shell">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.25, 0.8, 1.25])
    with c1:
        st.markdown(f'''<div class="team-band" style="background: linear-gradient(135deg, {meta['away_colors']['primary']}, {meta['away_colors']['secondary']});"><div class="small-label" style="color:rgba(255,255,255,.78)">Away</div><div class="kpi" style="color:white">{meta['away_team']}</div><div class="subtle" style="color:rgba(255,255,255,.78)">{TEAM_META.get(meta['away_team'], {}).get('abbr', '')}</div></div>''', unsafe_allow_html=True)
    with c2:
        st.markdown(f'''<div class="score-center"><div class="small-label">Final</div><div class="kpi">{meta['away_score']} - {meta['home_score']}</div><div class="subtle">{meta.get('date') or 'Game date unavailable'}</div></div>''', unsafe_allow_html=True)
    with c3:
        st.markdown(f'''<div class="team-band" style="background: linear-gradient(135deg, {meta['home_colors']['primary']}, {meta['home_colors']['secondary']});"><div class="small-label" style="color:rgba(255,255,255,.78)">Home</div><div class="kpi" style="color:white">{meta['home_team']}</div><div class="subtle" style="color:rgba(255,255,255,.78)">{TEAM_META.get(meta['home_team'], {}).get('abbr', '')}</div></div>''', unsafe_allow_html=True)
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
    st.title("🏀 NBA Game Storyboard")
    st.caption(f"Version {APP_VERSION} — possession-aware game storytelling dashboard with Regular Season / Playoffs support")

    with st.sidebar:
        st.markdown("### Controls")
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
                with st.spinner("Loading recent games..."):
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
        load_clicked = st.button("Load Game Data", use_container_width=True)
        st.markdown("---")
        st.markdown("### Heatmap options")
        heat_metric = st.selectbox("Heatmap metric", ["Attempts", "Makes", "FG%", "Points", "Expected Value"], index=0)
        st.caption("This changes the color scale on both team shot maps.")

    if not load_clicked:
        st.info("Choose a source, select a game or upload a CSV, then click Load Game Data.")
        with st.expander("Setup and notes"):
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
        st.markdown("### Filters")
        period_choices = sorted([int(p) for p in df["period"].dropna().unique().tolist()])
        selected_periods = st.multiselect("Periods", period_choices, default=period_choices)
        event_choices = sorted(df["event_family"].dropna().unique().tolist())
        default_events = [e for e in event_choices if e != "Other"] or event_choices
        selected_events = st.multiselect("Event groups", event_choices, default=default_events)
        run_options = ["All game"] + ([f"{row.team} {row.run_label} ({row.start_time} → {row.end_time})" for row in runs_df.itertuples()] if not runs_df.empty else [])
        selected_run = st.selectbox("Focus on run", run_options, index=0)
        selected_run_idx = run_options.index(selected_run) - 1
        st.markdown("---")
        st.download_button("Download events CSV", data=to_csv_download(df), file_name="events.csv", mime="text/csv", use_container_width=True)
        if not poss_summary.empty:
            st.download_button("Download possessions CSV", data=to_csv_download(poss_summary), file_name="possessions.csv", mime="text/csv", use_container_width=True)
        if not shot_df.empty:
            st.download_button("Download shot zones CSV", data=to_csv_download(shot_df), file_name="shot_zones.csv", mime="text/csv", use_container_width=True)
        if not heatmap_summary.empty:
            st.download_button("Download heatmap summary CSV", data=to_csv_download(heatmap_summary), file_name="shot_heatmap_summary.csv", mime="text/csv", use_container_width=True)

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

    row1 = st.columns([0.8, 0.8, 0.8, 0.9, 1.0])
    with row1[0]:
        st.markdown(f'<div class="metric-card"><div class="small-label">Winner</div><div class="kpi">{meta["winner"]}</div><div class="subtle">Final margin: {abs(meta["home_score"] - meta["away_score"])} points</div></div>', unsafe_allow_html=True)
    with row1[1]:
        st.markdown(f'<div class="metric-card"><div class="small-label">Tracked possessions</div><div class="kpi">{poss_summary["possession_id"].nunique() if not poss_summary.empty else 0}</div><div class="subtle">Heuristic possession parser</div></div>', unsafe_allow_html=True)
    with row1[2]:
        st.markdown(f'<div class="metric-card"><div class="small-label">Shot zones</div><div class="kpi">{shot_df["shot_zone"].nunique() if not shot_df.empty else 0}</div><div class="subtle">Rim, midrange, 3PT, FT</div></div>', unsafe_allow_html=True)
    with row1[3]:
        clutch_text = "Qualified" if clutch.get("qualified") else "Did not qualify"
        st.markdown(f'<div class="metric-card"><div class="small-label">Clutch time</div><div class="kpi">{clutch_text}</div><div class="subtle">Last 5:00, margin within 5</div></div>', unsafe_allow_html=True)
    with row1[4]:
        shot_count = len(away_points_df) + len(home_points_df)
        st.markdown(f'<div class="metric-card"><div class="small-label">Mapped shots</div><div class="kpi">{shot_count}</div><div class="subtle">Coordinate or inferred heatmap points</div></div>', unsafe_allow_html=True)

    st.markdown("## Keys to game")
    for note in keys:
        st.markdown(f"- {note}")

    st.markdown("## Score progression")
    st.plotly_chart(score_chart(filtered_df, meta), use_container_width=True)

    st.markdown("## Momentum")
    st.plotly_chart(momentum_chart(filtered_df, meta, filtered_runs if not filtered_runs.empty else runs_df, turning), use_container_width=True)

    st.markdown("## Possession view")
    st.plotly_chart(possession_chart(poss_filtered, meta), use_container_width=True)

    c1, c2 = st.columns([1.05, 0.95])
    with c1:
        st.markdown("## Team ratings")
        if ratings_df.empty:
            st.info("Team possession ratings unavailable.")
        else:
            st.dataframe(ratings_df, use_container_width=True, hide_index=True)
    with c2:
        st.markdown("## Segment summary")
        if seg_df.empty:
            st.info("No segment summary available.")
        else:
            st.dataframe(seg_df, use_container_width=True, hide_index=True)

    st.markdown("## Shot zones")
    st.plotly_chart(shot_zone_chart(shot_df, meta), use_container_width=True)
    if not shot_df.empty:
        st.dataframe(shot_df, use_container_width=True, hide_index=True)

    st.markdown("## Game possession analysis: shot chart heatmaps")
    st.markdown('<div class="heat-shell">', unsafe_allow_html=True)
    h1, h2 = st.columns([1.5, 0.5])
    with h1:
        st.markdown('<div class="heat-title">Game Possession Analysis: Shot Chart Heatmaps</div><div class="heat-subtle">The maps now clearly separate exact coordinate-based views from inferred zone maps, and the color scale can switch between attempts, makes, FG%, points, and expected value.</div>', unsafe_allow_html=True)
    with h2:
        st.markdown('<div class="heat-note"><b>Integrity note:</b> true-coordinate heatmaps come from NBA shot coordinates, while inferred maps are stylized approximations based on play-by-play shot zones.</div>', unsafe_allow_html=True)
    mode1, mode2, mode3 = st.columns([0.8, 0.8, 0.8])
    with mode1:
        st.markdown(f'<div class="card" style="background:#111827; color:#eef4ff; border:1px solid rgba(255,255,255,0.08)"><div class="small-label" style="color:rgba(238,244,255,.72)">{meta["away_team"]}</div><div class="story" style="color:#eef4ff">Mode: {away_mode}</div><div class="heat-subtle">{team_heatmap_insight(away_hex, meta["away_team"], away_mode)}</div></div>', unsafe_allow_html=True)
    with mode2:
        st.markdown(f'<div class="card" style="background:#111827; color:#eef4ff; border:1px solid rgba(255,255,255,0.08)"><div class="small-label" style="color:rgba(238,244,255,.72)">{meta["home_team"]}</div><div class="story" style="color:#eef4ff">Mode: {home_mode}</div><div class="heat-subtle">{team_heatmap_insight(home_hex, meta["home_team"], home_mode)}</div></div>', unsafe_allow_html=True)
    with mode3:
        st.markdown(f'<div class="card" style="background:#111827; color:#eef4ff; border:1px solid rgba(255,255,255,0.08)"><div class="small-label" style="color:rgba(238,244,255,.72)">Heat metric</div><div class="story" style="color:#eef4ff">{heat_metric}</div><div class="heat-subtle">Both panels use the same metric and color scale for fair visual comparison.</div></div>', unsafe_allow_html=True)
    st.plotly_chart(shot_heatmap_figure(away_hex, home_hex, meta, heat_metric), use_container_width=True)
    l1, l2, l3 = st.columns([0.95, 0.95, 0.6])
    with l1:
        away_points = int(away_hex["points"].sum()) if not away_hex.empty else 0
        away_ppp = round(away_points / max(len(poss_summary[poss_summary["possession_team"] == meta["away_team"]]), 1), 2) if not poss_summary.empty else 0
        st.markdown(f'<div class="card" style="background:#111827; color:#eef4ff; border:1px solid rgba(255,255,255,0.08)"><div class="small-label" style="color:rgba(238,244,255,.72)">{meta["away_team"]}</div><div class="kpi" style="color:#eef4ff">Total mapped points: {away_points}</div><div class="story" style="color:#d7e0ef">PPP: {away_ppp}</div><div class="heat-subtle">Corner-three and rim clusters are now more clearly separated in the geometry.</div></div>', unsafe_allow_html=True)
    with l2:
        home_points = int(home_hex["points"].sum()) if not home_hex.empty else 0
        home_ppp = round(home_points / max(len(poss_summary[poss_summary["possession_team"] == meta["home_team"]]), 1), 2) if not poss_summary.empty else 0
        st.markdown(f'<div class="card" style="background:#111827; color:#eef4ff; border:1px solid rgba(255,255,255,0.08)"><div class="small-label" style="color:rgba(238,244,255,.72)">{meta["home_team"]}</div><div class="kpi" style="color:#eef4ff">Total mapped points: {home_points}</div><div class="story" style="color:#d7e0ef">PPP: {home_ppp}</div><div class="heat-subtle">Use the metric toggle to compare shot volume, efficiency, and value from the same shape map.</div></div>', unsafe_allow_html=True)
    with l3:
        st.markdown('''<div class="card" style="background:#111827; color:#eef4ff; border:1px solid rgba(255,255,255,0.08)">
        <div class="small-label" style="color:rgba(238,244,255,.72)">What changed</div>
        <div class="heat-subtle">• Explicit mode labels<br>• Metric toggle<br>• Clearer corner-three geometry<br>• Better inferred fallback honesty</div>
        </div>''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    if not heatmap_summary.empty:
        st.dataframe(heatmap_summary, use_container_width=True, hide_index=True)

    c3, c4 = st.columns([1.1, 0.9])
    with c3:
        st.markdown("## Runs and swings")
        if runs_df.empty:
            st.warning("No qualifying scoring runs were detected with the default thresholds.")
        else:
            display_runs = (filtered_runs if not filtered_runs.empty else runs_df)[["team", "run_label", "start_time", "end_time", "quarter", "score_before", "score_after", "top_players", "key_plays"]].copy()
            st.dataframe(display_runs, use_container_width=True, hide_index=True)
    with c4:
        st.markdown("## Turning point")
        if turning:
            st.markdown(f'''<div class="card turning"><div class="small-label">Likely turning point</div><div class="kpi">🏀 {turning['team']}</div><div class="story">{turning['description']}</div><div class="subtle">Quarter {turning['quarter']} • {turning['clock']} • {turning['score']}</div></div>''', unsafe_allow_html=True)
        else:
            st.info("No turning point could be inferred.")

    with st.expander("Rotation Summary", expanded=False):
        if subs_df.empty:
            st.info("No substitutions were parsed from the available feed.")
        else:
            st.dataframe(subs_df.head(40), use_container_width=True, hide_index=True)

    with st.expander("Player Impact", expanded=False):
        if impact_df.empty:
            st.info("Player impact during runs could not be fully extracted from the available event structure.")
        else:
            st.dataframe(impact_df, use_container_width=True, hide_index=True)

    st.markdown("## Clutch time")
    if clutch.get("qualified"):
        c7, c8 = st.columns([0.85, 1.35])
        with c7:
            st.markdown(f'''<div class="card"><div class="small-label">Clutch summary</div><div class="kpi">{clutch['plays']} scoring plays</div><div class="subtle">Lead changes: {clutch['lead_changes']} • {meta['away_team']}: {clutch['away_points']} • {meta['home_team']}: {clutch['home_points']}</div></div>''', unsafe_allow_html=True)
        with c8:
            st.dataframe(clutch["key_plays"], use_container_width=True, hide_index=True)
    else:
        st.info("This game did not enter the defined clutch window.")

    with st.expander("Event Log", expanded=False):
        event_log = filtered_df[["period_label", "clock_display", "team_name", "player_name", "event_family", "shot_zone", "description", "score_away", "score_home"]].copy()
        st.dataframe(event_log, use_container_width=True, hide_index=True)

    st.markdown("## Game story")
    st.markdown(f'<div class="card"><div class="story">{story}</div></div>', unsafe_allow_html=True)

    with st.expander("Setup, commands, assumptions, and limitations"):
        st.code(installation_and_notes())


if __name__ == "__main__":
    main()
