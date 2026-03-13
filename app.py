import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path
from datetime import date, timedelta, datetime

from modules.ticket_dashboard import render_ticket_dashboard
from modules.sales_dashboard import render_sales_dashboard
from modules.social_dashboard import render_social_dashboard
from modules.operation_dashboard import render_operation_dashboard

st.set_page_config(page_title="AllCall BI Dashboard", page_icon="📊", layout="wide")

# =========================
# BRAND COLORS
# =========================
NAVY = "#02013B"
NAVY_2 = "#060658"
BLUE = "#0D1691"
ACCENT = "#0ACAF9"
WHITE = "#C9CED6"
MUTED = "rgba(241,241,245,0.72)"
CARD_BG = "rgba(255,255,255,0.10)"
CARD_BORDER = "rgba(255,255,255,0.10)"

# =========================
# PATH HELPERS
# =========================
def resolve_excel_path() -> str:
    candidates = [
        Path("allcall_bi_data.xlsx"),
        Path("data/allcall_bi_data.xlsx"),
        Path.home() / "Documents" / "allcall_bi_data.xlsx",
    ]
    for p in candidates:
        if p.exists():
            return str(p)

    raise FileNotFoundError(
        "Excel файл олдсонгүй.\n"
        "Checked:\n"
        "- allcall_bi_data.xlsx\n"
        "- data/allcall_bi_data.xlsx\n"
        "- ~/Documents/allcall_bi_data.xlsx"
    )


def resolve_logo_path() -> str | None:
    candidates = [
        Path("logo.png"),
        Path("assets/logo.png"),
        Path("/mnt/data/logo.png"),
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return None


EXCEL_PATH = resolve_excel_path()
LOGO_PATH = resolve_logo_path()

# =========================
# CSS
# =========================
st.markdown(
    f"""
    <style>
    .stApp {{
        background:
            radial-gradient(900px 500px at 88% 20%, rgba(13,22,145,.45) 0%, rgba(2,1,59,0) 60%),
            linear-gradient(135deg, {NAVY} 0%, {NAVY_2} 42%, {BLUE} 100%);
        color: {WHITE};
    }}

    .block-container {{
        padding-top: 1.3rem;
        padding-bottom: 2rem;
    }}

    h1, h2, h3, h4, p, label, div, span {{
        color: {WHITE} !important;
    }}

    section[data-testid="stSidebar"] {{
        background: rgba(1, 3, 45, 0.94);
        border-right: 1px solid rgba(255,255,255,0.08);
    }}

    .hero {{
        background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(10,202,249,0.05));
        border: 1px solid rgba(10,202,249,0.18);
        border-radius: 22px;
        padding: 18px 20px;
        box-shadow: 0 16px 40px rgba(0,0,0,0.25);
        backdrop-filter: blur(10px);
    }}

    .hero-title {{
        font-size: 1.8rem;
        font-weight: 900;
        margin-bottom: 4px;
    }}

    .hero-sub {{
        color: {MUTED} !important;
        font-size: .95rem;
    }}

    .hero-badge {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(10,202,249,0.12);
        border: 1px solid rgba(10,202,249,0.22);
        font-size: 0.85rem;
        margin-bottom: 10px;
    }}

    .glass {{
        background: {CARD_BG};
        border: 1px solid {CARD_BORDER};
        border-radius: 18px;
        padding: 14px 16px;
        backdrop-filter: blur(10px);
        box-shadow: 0 10px 28px rgba(0,0,0,0.18);
    }}

    .section-title {{
        font-size: 1.08rem;
        font-weight: 800;
        margin-bottom: 10px;
    }}

    .kpi-card {{
        background: {CARD_BG};
        border: 1px solid {CARD_BORDER};
        border-radius: 18px;
        padding: 15px 16px;
        min-height: 118px;
        box-shadow: 0 10px 24px rgba(0,0,0,0.18);
    }}

    .kpi-top {{
        display:flex;
        justify-content:space-between;
        align-items:center;
        margin-bottom:8px;
    }}

    .kpi-title {{
        font-size:.92rem;
        color:{MUTED} !important;
        font-weight:600;
    }}

    .kpi-icon {{
        width: 34px;
        height: 34px;
        border-radius: 10px;
        display:flex;
        align-items:center;
        justify-content:center;
        background: rgba(10,202,249,0.14);
        border: 1px solid rgba(10,202,249,0.24);
        font-size: 1rem;
    }}

    .kpi-value {{
        font-size: 2rem;
        font-weight: 900;
        line-height: 1.1;
        word-break: break-word;
    }}

    .kpi-sub {{
        margin-top: 5px;
        font-size: .84rem;
        color: {MUTED} !important;
    }}

    .mini-note {{
        color: {MUTED} !important;
        font-size: .88rem;
    }}

    .divider {{
        height: 1px;
        background: rgba(255,255,255,0.10);
        margin: 14px 0 18px 0;
    }}

    .stButton > button,
    .stDownloadButton > button {{
        background: linear-gradient(90deg, {ACCENT}, #68ddff) !important;
        color: {NAVY} !important;
        border: 0 !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
    }}

    .stButton > button:hover,
    .stDownloadButton > button:hover {{
        background: {BLUE} !important;
        color: {WHITE} !important;
    }}

    div[data-baseweb="select"] > div,
    .stDateInput > div > div,
    .stTextInput > div > div > input {{
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        color: {WHITE} !important;
        border-radius: 12px !important;
    }}

    [data-testid="stDataFrame"] {{
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        overflow: hidden;
    }}

    .footer {{
        text-align:center;
        color:{MUTED} !important;
        margin-top:20px;
        font-size:.88rem;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# COMMON HELPERS
# =========================
def _norm_str(x) -> str:
    return "" if pd.isna(x) else str(x).strip()


def _parse_money(x):
    if pd.isna(x):
        return 0.0
    s = str(x).strip().replace("₮", "").replace("$", "").replace(",", "")
    try:
        return float(s)
    except Exception:
        return 0.0


def _parse_percent(x):
    if pd.isna(x):
        return 0.0
    s = str(x).strip().replace("%", "").replace(",", "")
    try:
        return float(s)
    except Exception:
        return 0.0


def render_kpi_card(title: str, value: str, subtitle: str, icon: str):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-top">
                <div class="kpi-title">{title}</div>
                <div class="kpi-icon">{icon}</div>
            </div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _filter_by_date(df: pd.DataFrame, date_col: str, dfrom: date, dto: date) -> pd.DataFrame:
    if date_col not in df.columns:
        return df.copy()
    start_dt = pd.Timestamp(dfrom)
    end_dt = pd.Timestamp(dto) + pd.Timedelta(days=1)
    return df[(df[date_col] >= start_dt) & (df[date_col] < end_dt)].copy()

# =========================
# PREP FUNCTIONS FOR OVERVIEW
# =========================
def _prep_ticket(df: pd.DataFrame) -> pd.DataFrame:
    dfx = df.copy()
    rename_map = {
        "Огноо": "date",
        "Суваг": "channel",
        "Төрөл": "issue_type",
        "Санал, гомдол": "issue_detail",
        "Төлөв": "status",
        "Оператор": "operator",
    }
    dfx = dfx.rename(columns=rename_map)

    if "date" in dfx.columns:
        dfx["date"] = pd.to_datetime(dfx["date"], errors="coerce")

    for c in ["channel", "issue_type", "issue_detail", "status", "operator"]:
        if c in dfx.columns:
            dfx[c] = dfx[c].apply(_norm_str)

    return dfx


def _prep_sales(df: pd.DataFrame) -> pd.DataFrame:
    dfx = df.copy()
    rename_map = {
        "Холбогдсон дугаар": "contact_no",
        "Байгууллагын нэр": "company_name",
        "Хэрэгцээ": "need_type",
        "Явц": "stage",
        "Дүн": "amount",
        "Магадлал": "probability",
        "Магадлалын дүн": "weighted_amount",
        "Санал тавьж эхэлсэн огноо": "proposal_start_date",
        "Санал баталгаажсан огноо": "proposal_confirm_date",
        "Баг": "team",
        "Бие даалт": "ownership_pct",
        "Сүүлд холбогдсон байдал": "last_contact_date",
        "Дараагийн холбоо": "next_contact",
    }
    dfx = dfx.rename(columns=rename_map)

    for c in ["company_name", "need_type", "stage", "team", "next_contact"]:
        if c in dfx.columns:
            dfx[c] = dfx[c].apply(_norm_str)

    for c in ["proposal_start_date", "proposal_confirm_date", "last_contact_date"]:
        if c in dfx.columns:
            dfx[c] = pd.to_datetime(dfx[c], errors="coerce")

    if "amount" in dfx.columns:
        dfx["amount_num"] = dfx["amount"].apply(_parse_money)
    else:
        dfx["amount_num"] = 0.0

    if "weighted_amount" in dfx.columns:
        dfx["weighted_amount_num"] = dfx["weighted_amount"].apply(_parse_money)
    else:
        dfx["weighted_amount_num"] = 0.0

    if "probability" in dfx.columns:
        dfx["probability_num"] = dfx["probability"].apply(_parse_percent)
    else:
        dfx["probability_num"] = 0.0

    return dfx


def _prep_social(df: pd.DataFrame) -> pd.DataFrame:
    dfx = df.copy()

    rename_map = {
        "Эхэлсэн огноо": "start_date",
        "Дууссан огноо": "end_date",
        "Boost-н өдөр": "boost_days",
        "Постын агуулга": "post_content",
        "Пост үзсэн тоо": "post_views",
        "Үзэгчид": "viewers",
        "Чат эхлүүлсэн тоо": "chat_started",
        "Постын төсөв ($ өдөрт)": "daily_budget_usd",
        "Нийт зарцуулсан ($)": "total_spend_usd",
        "Нийт зарцуулсан (₮)": "total_spend_mnt",
        "Хоолой (₮)": "voice_spend_mnt",
        "Adobe (₮)": "adobe_spend_mnt",
        "Hera (₮)": "hera_spend_mnt",
    }
    dfx = dfx.rename(columns=rename_map)

    if "post_content" in dfx.columns:
        dfx["post_content"] = dfx["post_content"].apply(_norm_str)

    for c in ["start_date", "end_date"]:
        if c in dfx.columns:
            dfx[c] = pd.to_datetime(dfx[c], errors="coerce")

    numeric_cols = [
        "boost_days",
        "post_views",
        "viewers",
        "chat_started",
        "daily_budget_usd",
        "total_spend_usd",
        "total_spend_mnt",
        "voice_spend_mnt",
        "adobe_spend_mnt",
        "hera_spend_mnt",
    ]
    for c in numeric_cols:
        if c in dfx.columns:
            dfx[c] = dfx[c].apply(_parse_money)

    if "post_content" in dfx.columns:
        dfx = dfx[dfx["post_content"] != ""].copy()

    return dfx


def _prep_operation(df: pd.DataFrame) -> pd.DataFrame:
    dfx = df.copy()
    rename_map = {
        "Ажлын төрөл": "task_type",
        "Төслийн нэр": "project_name",
        "Эхлэх огноо": "start_date",
        "Дуусах огноо": "end_date",
        "Хугацаа": "duration_days",
        "Хариуцагч": "owner",
        "Дэмжигч": "supporter",
        "Явцын тайлбар": "progress_note",
        "Явц": "status",
    }
    dfx = dfx.rename(columns=rename_map)

    for c in ["task_type", "project_name", "owner", "supporter", "progress_note", "status"]:
        if c in dfx.columns:
            dfx[c] = dfx[c].apply(_norm_str)

    for c in ["start_date", "end_date"]:
        if c in dfx.columns:
            dfx[c] = pd.to_datetime(dfx[c], errors="coerce")

    if "duration_days" in dfx.columns:
        dfx["duration_days_num"] = pd.to_numeric(dfx["duration_days"], errors="coerce").fillna(0)
    else:
        dfx["duration_days_num"] = 0.0

    return dfx

# =========================
# DATA LOAD
# =========================
@st.cache_data(ttl=60)
def load_all_sheets(path: str) -> dict[str, pd.DataFrame]:
    xls = pd.ExcelFile(path)
    required = ["Ticket", "Sales", "Social media", "Operation"]

    data = {}
    for sheet in required:
        if sheet not in xls.sheet_names:
            raise ValueError(f"'{sheet}' sheet олдсонгүй. Байгаа sheet-үүд: {xls.sheet_names}")
        data[sheet] = pd.read_excel(xls, sheet_name=sheet)

    return data


try:
    sheets = load_all_sheets(EXCEL_PATH)
except Exception as e:
    st.error(str(e))
    st.stop()

# =========================
# HEADER
# =========================
h1, h2 = st.columns([1, 3.8], vertical_alignment="center")

with h1:
    if LOGO_PATH:
        st.image(LOGO_PATH, width=150)

with h2:
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-badge">📊 <b>AllCall BI Dashboard</b></div>
            <div class="hero-title">Ticket • Sales • Social Media • Operation</div>
            <div class="hero-sub">
                Нэгдсэн удирдлагын KPI тайлангийн самбар
            </div>
            <div class="hero-sub" style="margin-top:6px;">
                🕒 Сүүлд шинэчлэгдсэн: <b>{datetime.now().strftime("%Y-%m-%d %H:%M")}</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown("## 📂 Dashboard")
    menu = st.selectbox(
        "Module",
        ["Overview", "Ticket", "Sales", "Social media", "Operation"],
        index=0,
    )

    st.markdown("---")
    st.markdown("## 📅 Хугацаа")
    today = date.today()
    dfrom = st.date_input("Эхлэх огноо", value=today - timedelta(days=29))
    dto = st.date_input("Дуусах огноо", value=today)

    st.markdown("---")
    st.markdown(f"<div class='mini-note'>Excel: <b>{EXCEL_PATH}</b></div>", unsafe_allow_html=True)

# =========================
# OVERVIEW
# =========================
if menu == "Overview":
    ticket_df = _prep_ticket(sheets["Ticket"])
    sales_df = _prep_sales(sheets["Sales"])
    social_df = _prep_social(sheets["Social media"])
    operation_df = _prep_operation(sheets["Operation"])

    ticket_cur = _filter_by_date(ticket_df, "date", dfrom, dto)
    sales_cur = _filter_by_date(sales_df, "proposal_start_date", dfrom, dto)
    social_cur = _filter_by_date(social_df, "start_date", dfrom, dto)
    operation_cur = _filter_by_date(operation_df, "start_date", dfrom, dto)

    # Ticket KPIs
    total_tickets = len(ticket_cur)
    resolved_tickets = int((ticket_cur.get("status", pd.Series(dtype=str)) == "Шийдвэрлэсэн").sum()) if "status" in ticket_cur.columns else 0
    top_issue = "—"
    if "issue_type" in ticket_cur.columns:
        vc = ticket_cur["issue_type"].replace("", pd.NA).dropna().value_counts()
        if not vc.empty:
            top_issue = str(vc.index[0])

    # Sales KPIs
    total_sales_records = len(sales_cur)
    total_pipeline = float(sales_cur.get("amount_num", pd.Series(dtype=float)).sum()) if "amount_num" in sales_cur.columns else 0.0
    total_weighted = float(sales_cur.get("weighted_amount_num", pd.Series(dtype=float)).sum()) if "weighted_amount_num" in sales_cur.columns else 0.0
    won_count = int((sales_cur.get("stage", pd.Series(dtype=str)).astype(str).str.lower() == "won").sum()) if "stage" in sales_cur.columns else 0

    # Social KPIs
    total_posts = len(social_cur)
    total_social_views = float(social_cur.get("post_views", pd.Series(dtype=float)).sum()) if "post_views" in social_cur.columns else 0.0
    total_social_viewers = float(social_cur.get("viewers", pd.Series(dtype=float)).sum()) if "viewers" in social_cur.columns else 0.0
    total_social_chats = float(social_cur.get("chat_started", pd.Series(dtype=float)).sum()) if "chat_started" in social_cur.columns else 0.0
    total_social_spend = float(social_cur.get("total_spend_mnt", pd.Series(dtype=float)).sum()) if "total_spend_mnt" in social_cur.columns else 0.0
    social_cost_per_chat = (total_social_spend / total_social_chats) if total_social_chats else 0.0

    social_top_post = "—"
    if "post_content" in social_cur.columns and "post_views" in social_cur.columns:
        top_post_df = social_cur.sort_values("post_views", ascending=False)
        if not top_post_df.empty:
            social_top_post = str(top_post_df.iloc[0]["post_content"])

    # Operation KPIs
    total_tasks = len(operation_cur)
    done_tasks = int((operation_cur.get("status", pd.Series(dtype=str)) == "Хийгдсэн").sum()) if "status" in operation_cur.columns else 0
    contract_tasks = int(operation_cur["task_type"].str.contains("гэрээ", case=False, na=False).sum()) if "task_type" in operation_cur.columns else 0

    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Executive Overview</div>', unsafe_allow_html=True)

    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    with r1c1:
        render_kpi_card("Нийт тикет", f"{total_tickets:,}", f"Шийдвэрлэсэн: {resolved_tickets:,}", "🎫")
    with r1c2:
        render_kpi_card("Sales pipeline", f"₮{total_pipeline:,.0f}", f"Weighted: ₮{total_weighted:,.0f}", "💼")
    with r1c3:
        render_kpi_card("Social spend", f"₮{total_social_spend:,.0f}", f"Chat: {total_social_chats:,.0f}", "📣")
    with r1c4:
        render_kpi_card("Operation tasks", f"{total_tasks:,}", f"Done: {done_tasks:,}", "🛠")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    with r2c1:
        render_kpi_card("Top issue", f"{top_issue}", "Ticket төрөл", "🧩")
    with r2c2:
        render_kpi_card("Won deals", f"{won_count:,}", f"Нийт санал: {total_sales_records:,}", "🏆")
    with r2c3:
        render_kpi_card("Top social post", f"{social_top_post}", f"Views: {total_social_views:,.0f}", "📱")
    with r2c4:
        render_kpi_card("Гэрээтэй холбоотой ажил", f"{contract_tasks:,}", f"1 chat өртөг: ₮{social_cost_per_chat:,.0f}", "📄")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    left, right = st.columns(2)

    with left:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📊 Module summary</div>', unsafe_allow_html=True)

        summary_df = pd.DataFrame({
            "module": ["Ticket", "Sales", "Social media", "Operation"],
            "value": [total_tickets, total_pipeline, total_social_spend, total_tasks]
        })

        chart = alt.Chart(summary_df).mark_bar(
            color=ACCENT,
            cornerRadiusEnd=6
        ).encode(
            y=alt.Y("module:N", sort="-x", title=""),
            x=alt.X("value:Q", title="Value"),
            tooltip=["module:N", "value:Q"]
        ).properties(height=320)
        st.altair_chart(chart, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📌 Overview notes</div>', unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="mini-note" style="line-height:1.8;">
            • Ticket KPI нь гомдол, саналын урсгал болон шийдвэрлэлтийн байдлыг харуулна.<br>
            • Sales KPI нь бүртгэгдсэн санал, pipeline дүн, won боломжуудыг харуулна.<br>
            • Social KPI нь нийт views, chats, spend болон top post-ыг харуулна.<br>
            • Operation KPI нь ажлын явц, гэрээтэй холбоотой ажлуудыг харуулна.<br>
            • Excel source: <b>{EXCEL_PATH}</b>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

elif menu == "Ticket":
    render_ticket_dashboard(sheets["Ticket"], dfrom, dto, ACCENT)

elif menu == "Sales":
    render_sales_dashboard(sheets["Sales"], dfrom, dto, ACCENT)

elif menu == "Social media":
    render_social_dashboard(sheets["Social media"], dfrom, dto, ACCENT)

elif menu == "Operation":
    render_operation_dashboard(sheets["Operation"], dfrom, dto, ACCENT)

st.markdown(
    """
    <div class="footer">
        © AllCall • Incredible service • Incredible business
    </div>
    """,
    unsafe_allow_html=True,
)
