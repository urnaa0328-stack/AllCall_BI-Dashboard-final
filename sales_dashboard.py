import re
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta, date


def _norm_str(x):
    return "" if pd.isna(x) else str(x).strip()


def _norm_colname(x):
    s = "" if pd.isna(x) else str(x)
    s = s.replace("\n", " ").replace("\xa0", " ").strip()
    s = re.sub(r"\s+", " ", s)
    return s.lower()


def _parse_percent_value(x):
    if pd.isna(x):
        return 0.0
    s = str(x).replace("%", "").replace(",", "").strip()
    try:
        return float(s)
    except:
        return 0.0


def _parse_money(x):
    if pd.isna(x):
        return 0.0

    s = str(x)
    s = s.replace("₮", "")
    s = s.replace(",", "")
    s = s.replace(" ", "")

    s = re.sub(r"[^\d.\-]", "", s)

    try:
        return float(s) if s else 0.0
    except:
        return 0.0


def _find_matching_column(columns, aliases):

    normalized = {_norm_colname(c): c for c in columns}

    for alias in aliases:
        a = _norm_colname(alias)

        for norm_col, original in normalized.items():
            if a in norm_col:
                return original

    return None


def _prepare_sales_df(df):

    dfx = df.copy()

    aliases = {

        "stage": ["явц", "төлөв", "статус"],

        "amount": [
            "дүн",
            "саналын дүн",
            "үнийн дүн",
            "бүртгэсэн дүн",
            "бүртгэгдсэн дүн",
        ],

        "probability": [
            "магадлал",
            "магадлал %",
        ],

        "team": ["баг"],

        "need_type": ["хэрэгцээ"],

        "proposal_start_date": [
            "эхэлсэн огноо",
            "бүртгэсэн огноо",
            "огноо",
        ],
    }

    rename_map = {}

    for key, alias_list in aliases.items():
        col = _find_matching_column(dfx.columns, alias_list)
        if col:
            rename_map[col] = key

    dfx = dfx.rename(columns=rename_map)

    if "stage" in dfx.columns:
        dfx["stage_norm"] = dfx["stage"].astype(str).str.lower().str.strip()
    else:
        dfx["stage_norm"] = ""

    if "team" not in dfx.columns:
        dfx["team"] = "Unknown"

    if "amount" in dfx.columns:
        dfx["amount_num"] = dfx["amount"].apply(_parse_money)
    else:
        dfx["amount_num"] = 0.0

    if "probability" in dfx.columns:
        dfx["probability_num"] = dfx["probability"].apply(_parse_percent_value)
    else:
        dfx["probability_num"] = 0.0

    if "proposal_start_date" in dfx.columns:
        dfx["proposal_start_date"] = pd.to_datetime(
            dfx["proposal_start_date"], errors="coerce"
        )

    return dfx


def _filter_period(df, dfrom, dto):

    if "proposal_start_date" not in df.columns:
        return df

    start_dt = pd.Timestamp(datetime.combine(dfrom, datetime.min.time()))
    end_dt = pd.Timestamp(datetime.combine(dto + timedelta(days=1), datetime.min.time()))

    return df[
        (df["proposal_start_date"] >= start_dt)
        & (df["proposal_start_date"] < end_dt)
    ]


def render_sales_dashboard(df, dfrom, dto, accent):

    st.subheader("💼 Sales Dashboard")

    dfx = _prepare_sales_df(df)

    cur = _filter_period(dfx, dfrom, dto)

    total_deals = len(cur)

    total_amount = cur["amount_num"].sum()

    won_df = cur[cur["stage_norm"].str.contains("won", na=False)]

    won_count = len(won_df)

    won_amount = won_df["amount_num"].sum()

    conversion_rate = (won_count / total_deals * 100) if total_deals else 0

    avg_probability = cur["probability_num"].mean() if total_deals else 0

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Бүртгэгдсэн санал", f"{total_deals:,}")
    c2.metric("Нийт мөнгөн дүн", f"₮{total_amount:,.0f}")
    c3.metric("Won мөнгөн дүн", f"₮{won_amount:,.0f}")
    c4.metric("Won conversion", f"{conversion_rate:.1f}%")

    st.divider()

    team_amount_df = (
        cur.groupby("team", as_index=False)["amount_num"]
        .sum()
        .rename(columns={"amount_num": "amount"})
        .sort_values("amount", ascending=False)
    )

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("#### 💰 Бүртгэгдсэн саналын мөнгөн дүн (Багаар)")

        if team_amount_df.empty:
            st.info("Багийн дата алга.")
        else:

            chart = alt.Chart(team_amount_df).mark_bar(
                color=accent
            ).encode(
                y=alt.Y("team:N", sort="-x", title="Баг"),
                x=alt.X("amount:Q", title="Мөнгөн дүн"),
                tooltip=["team", "amount"]
            )

            st.altair_chart(chart, use_container_width=True)

    with col2:

        st.markdown("#### 📊 Явцын хуваарилалт")

        stage_df = (
            cur["stage"]
            .replace("", pd.NA)
            .dropna()
            .value_counts()
            .rename_axis("stage")
            .reset_index(name="count")
        )

        if stage_df.empty:
            st.info("Явцын дата алга.")
        else:

            chart = alt.Chart(stage_df).mark_arc(innerRadius=60).encode(
                theta="count",
                color="stage",
                tooltip=["stage", "count"]
            )

            st.altair_chart(chart, use_container_width=True)

    st.divider()

    st.markdown("#### 📋 Дэлгэрэнгүй жагсаалт")

    st.dataframe(cur, use_container_width=True)
