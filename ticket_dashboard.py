import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta, date


# =========================
# Helpers
# =========================

def _norm_str(x):
    if pd.isna(x):
        return ""
    return str(x).strip()


def prepare_df(df):

    rename_map = {
        "Огноо": "date",
        "Суваг": "channel",
        "Төрөл": "issue_type",
        "Санал, гомдол": "issue_detail",
        "Төлөв": "status",
        "Оператор": "operator",
    }

    df = df.rename(columns=rename_map)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    for col in ["channel", "issue_type", "issue_detail", "status", "operator"]:
        if col in df.columns:
            df[col] = df[col].apply(_norm_str)

    return df


def filter_period(df, dfrom, dto):

    start_dt = datetime.combine(dfrom, datetime.min.time())
    end_dt = datetime.combine(dto + timedelta(days=1), datetime.min.time())

    return df[(df["date"] >= start_dt) & (df["date"] < end_dt)].copy()


def status_count(df, status_name):

    if "status" not in df.columns:
        return 0

    return int((df["status"] == status_name).sum())


def compare_value(current, previous, pct=False):

    diff = current - previous

    if pct:
        sign = "+" if diff > 0 else ""
        return f"{sign}{diff:.1f}%"

    sign = "+" if diff > 0 else ""
    return f"{sign}{diff}"


# =========================
# MAIN
# =========================

def render_ticket_dashboard(df: pd.DataFrame, dfrom: date, dto: date, accent: str):

    st.subheader("🎫 Ticket Dashboard")

    df = prepare_df(df)

    cur = filter_period(df, dfrom, dto)

    days = (dto - dfrom).days + 1

    prev_to = dfrom - timedelta(days=1)
    prev_from = prev_to - timedelta(days=days - 1)

    prev = filter_period(df, prev_from, prev_to)

    total = len(cur)
    prev_total = len(prev)

    resolved = status_count(cur, "Шийдвэрлэсэн")
    accepted = status_count(cur, "Хүлээн авсан")
    checking = status_count(cur, "Шалгаж байгаа")
    transferred = status_count(cur, "Шилжүүлсэн")

    prev_resolved = status_count(prev, "Шийдвэрлэсэн")

    resolution_rate = (resolved / total * 100) if total else 0
    prev_resolution_rate = (prev_resolved / prev_total * 100) if prev_total else 0


    # =========================
    # Top issue
    # =========================

    rep_top10 = pd.DataFrame()

    top_issue = "-"
    top_issue_count = 0

    if "issue_detail" in cur.columns:

        rep = cur["issue_detail"].replace("", pd.NA).dropna()

        vc = rep.value_counts()

        if not vc.empty:

            top_issue = vc.index[0]
            top_issue_count = int(vc.iloc[0])

            rep_top10 = vc.head(10).reset_index()

            rep_top10.columns = ["issue", "count"]


    # =========================
    # Top operator
    # =========================

    op_top10 = pd.DataFrame()

    top_operator = "-"
    top_operator_count = 0

    if {"status", "operator"}.issubset(cur.columns):

        resolved_df = cur[cur["status"] == "Шийдвэрлэсэн"]

        vc = resolved_df["operator"].replace("", pd.NA).dropna().value_counts()

        if not vc.empty:

            top_operator = vc.index[0]
            top_operator_count = int(vc.iloc[0])

            op_top10 = vc.head(10).reset_index()

            op_top10.columns = ["operator", "count"]


    # =========================
    # Channel
    # =========================

    channel_counts = pd.DataFrame()

    if "channel" in cur.columns:

        vc = cur["channel"].replace("", pd.NA).dropna().value_counts()

        if not vc.empty:

            channel_counts = vc.reset_index()

            channel_counts.columns = ["channel", "count"]


    # =========================
    # Daily trend
    # =========================

    trend = pd.DataFrame()

    if "date" in cur.columns:

        temp = cur.copy()

        temp["date_only"] = temp["date"].dt.date

        trend = temp.groupby("date_only").size().reset_index(name="count")


    # =========================
    # KPI
    # =========================

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Нийт тикет", total, compare_value(total, prev_total))
    c2.metric("Шийдвэрлэсэн", resolved)
    c3.metric("Хүлээн авсан", accepted)
    c4.metric("Шалгаж байгаа", checking)

    c5, c6, c7, c8 = st.columns(4)

    c5.metric("Шилжүүлсэн", transferred)
    c6.metric("Resolution rate", f"{resolution_rate:.1f}%")
    c7.metric("Top асуудал", top_issue_count, top_issue)
    c8.metric("Top оператор", top_operator_count, top_operator)

    st.divider()


    # =========================
    # Charts
    # =========================

    left, right = st.columns(2)

    with left:

        st.markdown("### 📡 Суваг")

        if channel_counts.empty:
            st.info("Дата алга")

        else:

            chart = alt.Chart(channel_counts).mark_bar(
                color=accent
            ).encode(
                y=alt.Y("channel:N", sort="-x"),
                x="count:Q",
                tooltip=["channel", "count"]
            )

            st.altair_chart(chart, use_container_width=True)


    with right:

        st.markdown("### 📈 Daily tickets")

        if trend.empty:
            st.info("Дата алга")

        else:

            chart = alt.Chart(trend).mark_line(
                color=accent,
                point=True
            ).encode(
                x="date_only:T",
                y="count:Q",
                tooltip=["date_only", "count"]
            )

            st.altair_chart(chart, use_container_width=True)


    st.divider()


    # =========================
    # Top issue / operator
    # =========================

    left2, right2 = st.columns(2)

    with left2:

        st.markdown("### 🔁 Давтагдсан асуудал")

        if rep_top10.empty:
            st.info("Дата алга")

        else:

            chart = alt.Chart(rep_top10).mark_bar(
                color=accent
            ).encode(
                y=alt.Y("issue:N", sort="-x"),
                x="count:Q",
                tooltip=["issue", "count"]
            )

            st.altair_chart(chart, use_container_width=True)


    with right2:

        st.markdown("### 🏆 Top оператор")

        if op_top10.empty:
            st.info("Дата алга")

        else:

            chart = alt.Chart(op_top10).mark_bar(
                color="#56B4FF"
            ).encode(
                y=alt.Y("operator:N", sort="-x"),
                x="count:Q",
                tooltip=["operator", "count"]
            )

            st.altair_chart(chart, use_container_width=True)


    st.divider()


    # =========================
    # Table
    # =========================

    st.markdown("### 📋 Ticket list")

    st.dataframe(cur, use_container_width=True, height=400)

    csv = cur.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        "⬇️ CSV татах",
        csv,
        file_name="ticket_dashboard.csv",
        mime="text/csv"
    )