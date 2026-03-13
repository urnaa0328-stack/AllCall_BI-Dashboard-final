import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime


# =========================
# COLUMN CLEAN
# =========================

def clean_col(col):
    return str(col).replace("\n", " ").replace("\t", " ").strip()


# =========================
# SAFE DATE PARSER
# =========================

def parse_date(x):

    if pd.isna(x):
        return pd.NaT

    if isinstance(x, (pd.Timestamp, datetime)):
        return pd.Timestamp(x)

    # Excel serial date
    if isinstance(x, (int, float)):
        return pd.to_datetime(x, unit="D", origin="1899-12-30", errors="coerce")

    s = str(x).strip()

    # normalize separators
    s = s.replace("/", "-").replace(".", "-")

    # TRY SAFE FORMAT FIRST
    try:
        return pd.to_datetime(s, format="%Y-%m-%d")
    except:
        pass

    try:
        return pd.to_datetime(s, format="%d-%m-%Y")
    except:
        pass

    return pd.to_datetime(s, errors="coerce")


# =========================
# DATA PREP
# =========================

def prepare_social_df(df):

    dfx = df.copy()

    dfx.columns = [clean_col(c) for c in dfx.columns]

    for c in list(dfx.columns):

        if "Эхэлсэн" in c:
            dfx.rename(columns={c: "start_date"}, inplace=True)

        elif "Дууссан" in c:
            dfx.rename(columns={c: "end_date"}, inplace=True)

        elif "Boost" in c:
            dfx.rename(columns={c: "boost_days"}, inplace=True)

        elif "Постын агуулга" in c:
            dfx.rename(columns={c: "post_content"}, inplace=True)

        elif "Пост үзсэн" in c:
            dfx.rename(columns={c: "post_views"}, inplace=True)

        elif "Үзэгчид" in c:
            dfx.rename(columns={c: "viewers"}, inplace=True)

        elif "Чат эхлүүлсэн" in c:
            dfx.rename(columns={c: "chat_started"}, inplace=True)

        elif "Постын төсөв" in c:
            dfx.rename(columns={c: "daily_budget_usd"}, inplace=True)

        elif "Нийт зарцуулсан (₮)" in c:
            dfx.rename(columns={c: "total_spend_mnt"}, inplace=True)

        elif "Хоолой" in c:
            dfx.rename(columns={c: "voice_spend_mnt"}, inplace=True)

        elif "Adobe" in c:
            dfx.rename(columns={c: "adobe_spend_mnt"}, inplace=True)

        elif "Hera" in c:
            dfx.rename(columns={c: "hera_spend_mnt"}, inplace=True)

    dfx = dfx.loc[:, ~dfx.columns.duplicated()]

    if "start_date" in dfx.columns:
        dfx["start_date"] = dfx["start_date"].apply(parse_date)

    if "end_date" in dfx.columns:
        dfx["end_date"] = dfx["end_date"].apply(parse_date)

    numeric_cols = [
        "boost_days",
        "post_views",
        "viewers",
        "chat_started",
        "daily_budget_usd",
        "total_spend_mnt",
        "voice_spend_mnt",
        "adobe_spend_mnt",
        "hera_spend_mnt"
    ]

    for col in numeric_cols:

        if col in dfx.columns:

            dfx[col] = (
                dfx[col]
                .astype(str)
                .str.replace("₮", "", regex=False)
                .str.replace("$", "", regex=False)
                .str.replace(",", "", regex=False)
            )

            dfx[col] = pd.to_numeric(dfx[col], errors="coerce").fillna(0)

    if "post_content" in dfx.columns:
        dfx = dfx[dfx["post_content"].astype(str).str.strip() != ""]

    if "start_date" in dfx.columns:
        dfx = dfx[dfx["start_date"].notna()]

    return dfx.reset_index(drop=True)


# =========================
# FILTER
# =========================

def filter_period(df, dfrom, dto):

    if "start_date" not in df.columns:
        return df

    start = pd.Timestamp(dfrom)
    end = pd.Timestamp(dto)

    mask = (df["start_date"] >= start) & (df["start_date"] <= end)

    return df[mask]


# =========================
# DASHBOARD
# =========================

def render_social_dashboard(df, dfrom, dto, accent):

    st.subheader("📣 Social Media Dashboard")

    dfx = prepare_social_df(df)

    cur = filter_period(dfx, dfrom, dto)

    total_posts = len(cur)

    total_views = cur["post_views"].sum()
    total_viewers = cur["viewers"].sum()
    total_chat = cur["chat_started"].sum()

    total_spend = cur["total_spend_mnt"].sum()

    cost_per_chat = total_spend / total_chat if total_chat else 0

    view_chat_rate = (total_chat / total_viewers * 100) if total_viewers else 0

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Нийт пост", total_posts)
    c2.metric("Нийт үзэлт", f"{total_views:,.0f}")
    c3.metric("Нийт үзэгч", f"{total_viewers:,.0f}")
    c4.metric("Чат эхлүүлсэн", f"{total_chat:,.0f}")

    c5, c6, c7 = st.columns(3)

    c5.metric("Нийт зардал (₮)", f"{total_spend:,.0f}")
    c6.metric("1 чат өртөг", f"{cost_per_chat:,.0f}")
    c7.metric("Viewer → Chat %", f"{view_chat_rate:.2f}%")

    st.divider()

    trend = cur.groupby("start_date", as_index=False)["total_spend_mnt"].sum()

    chart = alt.Chart(trend).mark_line(point=True).encode(
        x="start_date:T",
        y="total_spend_mnt:Q"
    )

    st.altair_chart(chart, use_container_width=True)

    st.divider()

    st.markdown("### 📋 Data")

    st.dataframe(cur, use_container_width=True)

    with st.expander("Debug info"):

        st.write("Prepared row count:", len(dfx))
        st.write("Filtered row count:", len(cur))
        st.write("Dates parsed:")
        st.write(dfx["start_date"])