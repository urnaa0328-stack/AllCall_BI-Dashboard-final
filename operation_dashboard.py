import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta, date


def _norm_str(x) -> str:
    return "" if pd.isna(x) else str(x).strip()


def _parse_num(x):
    if pd.isna(x):
        return 0.0
    s = str(x).strip().replace(",", "")
    try:
        return float(s)
    except Exception:
        return 0.0


def _prepare_operation_df(df: pd.DataFrame) -> pd.DataFrame:
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

    for col in ["task_type", "project_name", "owner", "supporter", "progress_note", "status"]:
        if col in dfx.columns:
            dfx[col] = dfx[col].apply(_norm_str)

    for col in ["start_date", "end_date"]:
        if col in dfx.columns:
            dfx[col] = pd.to_datetime(dfx[col], errors="coerce")

    if "duration_days" in dfx.columns:
        dfx["duration_days_num"] = dfx["duration_days"].apply(_parse_num)
    else:
        dfx["duration_days_num"] = 0.0

    return dfx


def _filter_period(df: pd.DataFrame, dfrom: date, dto: date) -> pd.DataFrame:
    if "start_date" not in df.columns:
        return df.copy()
    start_dt = datetime.combine(dfrom, datetime.min.time())
    end_dt = datetime.combine(dto + timedelta(days=1), datetime.min.time())
    return df[(df["start_date"] >= start_dt) & (df["start_date"] < end_dt)].copy()


def render_operation_dashboard(df: pd.DataFrame, dfrom: date, dto: date, accent: str):
    st.subheader("🛠 Operation Dashboard")

    dfx = _prepare_operation_df(df)
    cur = _filter_period(dfx, dfrom, dto)

    total_tasks = len(cur)

    done_count = int((cur["status"] == "Хийгдсэн").sum()) if "status" in cur.columns else 0
    in_progress_count = int((cur["status"] == "Хийгдэж байна").sum()) if "status" in cur.columns else 0
    waiting_count = int((cur["status"] == "Хүлээгдэж байна").sum()) if "status" in cur.columns else 0
    completion_rate = (done_count / total_tasks * 100) if total_tasks else 0.0

    total_contract_tasks = int((cur["task_type"].str.contains("гэрээ", case=False, na=False)).sum()) if "task_type" in cur.columns else 0
    active_contract_tasks = int(
        cur[
            cur["task_type"].str.contains("гэрээ", case=False, na=False) &
            (cur["status"] != "Хийгдсэн")
        ].shape[0]
    ) if {"task_type", "status"}.issubset(cur.columns) else 0

    avg_duration = float(cur["duration_days_num"].mean()) if total_tasks else 0.0

    # Task type distribution
    task_type_df = pd.DataFrame(columns=["task_type", "count"])
    top_task_type = "—"
    top_task_type_count = 0
    if "task_type" in cur.columns:
        vc = cur["task_type"].replace("", pd.NA).dropna().value_counts()
        if not vc.empty:
            top_task_type = str(vc.index[0])
            top_task_type_count = int(vc.iloc[0])
            task_type_df = vc.head(10).reset_index()
            task_type_df.columns = ["task_type", "count"]

    # Owner workload
    owner_df = pd.DataFrame(columns=["owner", "count"])
    top_owner = "—"
    top_owner_count = 0
    if "owner" in cur.columns:
        vc = cur["owner"].replace("", pd.NA).dropna().value_counts()
        if not vc.empty:
            top_owner = str(vc.index[0])
            top_owner_count = int(vc.iloc[0])
            owner_df = vc.head(10).reset_index()
            owner_df.columns = ["owner", "count"]

    # Status distribution
    status_df = pd.DataFrame(columns=["status", "count"])
    if "status" in cur.columns:
        vc = cur["status"].replace("", pd.NA).dropna().value_counts()
        status_df = vc.reset_index()
        status_df.columns = ["status", "count"]

    # Timeline
    timeline_df = pd.DataFrame(columns=["start_date", "count"])
    if "start_date" in cur.columns:
        temp = cur.copy()
        temp["date_only"] = temp["start_date"].dt.date
        timeline_df = temp.groupby("date_only").size().reset_index(name="count")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Нийт ажил", f"{total_tasks:,}")
    c2.metric("Хийгдсэн", f"{done_count:,}")
    c3.metric("Хийгдэж байна", f"{in_progress_count:,}")
    c4.metric("Хүлээгдэж байна", f"{waiting_count:,}")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Гүйцэтгэлийн хувь", f"{completion_rate:.1f}%")
    c6.metric("Нийт гэрээтэй холбоотой ажил", f"{total_contract_tasks:,}")
    c7.metric("Одоо байгуулах ёстой гэрээ", f"{active_contract_tasks:,}")
    c8.metric("Дундаж хугацаа", f"{avg_duration:.1f} хоног")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.markdown("#### 📂 Ажлын төрлийн хуваарилалт")
        if task_type_df.empty:
            st.info("Ажлын төрлийн дата алга.")
        else:
            chart = alt.Chart(task_type_df).mark_bar(
                color=accent, cornerRadiusEnd=6
            ).encode(
                y=alt.Y("task_type:N", sort="-x", title="Ажлын төрөл"),
                x=alt.X("count:Q", title="Тоо"),
                tooltip=["task_type:N", "count:Q"]
            ).properties(height=360)
            st.altair_chart(chart, use_container_width=True)

    with right:
        st.markdown("#### 👤 Хариуцагчийн workload")
        if owner_df.empty:
            st.info("Хариуцагчийн дата алга.")
        else:
            chart = alt.Chart(owner_df).mark_bar(
                color="#56B4FF", cornerRadiusEnd=6
            ).encode(
                y=alt.Y("owner:N", sort="-x", title="Хариуцагч"),
                x=alt.X("count:Q", title="Ажлын тоо"),
                tooltip=["owner:N", "count:Q"]
            ).properties(height=360)
            st.altair_chart(chart, use_container_width=True)

    st.divider()

    left2, right2 = st.columns(2)

    with left2:
        st.markdown("#### 📊 Явцын төлөвийн хуваарилалт")
        if status_df.empty:
            st.info("Явцын дата алга.")
        else:
            chart = alt.Chart(status_df).mark_arc(innerRadius=60).encode(
                theta="count:Q",
                color=alt.Color("status:N", title="Явц"),
                tooltip=["status:N", "count:Q"]
            ).properties(height=320)
            st.altair_chart(chart, use_container_width=True)

    with right2:
        st.markdown("#### 📅 Ажлын эхлэлийн хугацааны тренд")
        if timeline_df.empty:
            st.info("Трендийн дата алга.")
        else:
            chart = alt.Chart(timeline_df).mark_line(
                point=alt.OverlayMarkDef(color=accent, filled=True, size=70),
                color=accent,
                strokeWidth=3
            ).encode(
                x=alt.X("date_only:T", title="Эхлэх огноо"),
                y=alt.Y("count:Q", title="Ажлын тоо"),
                tooltip=["date_only:T", "count:Q"]
            ).properties(height=320)
            st.altair_chart(chart, use_container_width=True)

    st.divider()

    st.markdown("#### 📋 Дэлгэрэнгүй жагсаалт")
    st.dataframe(cur, use_container_width=True, height=360)

    csv = cur.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ CSV татах", csv, file_name="operation_dashboard_filtered.csv", mime="text/csv")