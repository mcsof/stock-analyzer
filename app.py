import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO


# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Stock Analytics Dashboard",
    layout="wide"
)

st.title("📈 Stock Analytics Dashboard")


# =====================================================
# SIDEBAR INPUTS
# =====================================================

st.sidebar.header("Inputs")

stock_input = st.sidebar.text_input(
    "Enter Stock Symbol",
    value="AAPL"
).upper().strip()

period = st.sidebar.text_input(
    "Enter Period",
    value="5d"
).lower().strip()

st.sidebar.caption("Examples: 1d, 2d, 5d, 1mo, 3mo, 1y")

interval = st.sidebar.text_input(
    "Enter Interval",
    value="5m"
).lower().strip()

st.sidebar.caption("Examples: 1m, 2m, 5m, 15m, 30m, 60m, 1h, 1d")

group_days = st.sidebar.number_input(
    "How Many Days Per Group?",
    min_value=1,
    max_value=30,
    value=1
)


# =====================================================
# PLOT OPTIONS
# =====================================================

plot_columns = [
    "Open",
    "Close",
    "Change",
    "% Change",
    "Highest",
    "Lowest",
    "Average",
    "Crossings",
    "Avg Crossing Gap (mins)",
    "Time Above Avg (mins)",
    "Time Below Avg (mins)",
    "Highest Time Numeric",
    "Lowest Time Numeric"
]

selected_plots = st.sidebar.multiselect(
    "Select Graph Columns",
    plot_columns,
    default=["Close"]
)


# =====================================================
# RUN BUTTON
# =====================================================

run_button = st.sidebar.button("▶ Run Analysis")


# =====================================================
# SCREEN BUTTONS
# =====================================================

st.sidebar.divider()
st.sidebar.subheader("View")

if "page" not in st.session_state:
    st.session_state.page = "table"

if st.sidebar.button("📋 Show Table"):
    st.session_state.page = "table"

if st.sidebar.button("📊 Show Full Screen Plot"):
    st.session_state.page = "plot"

if st.sidebar.button("⬇ Show Downloads"):
    st.session_state.page = "downloads"


# =====================================================
# CACHE DATA
# =====================================================

@st.cache_data
def load_data(ticker, selected_period, selected_interval):
    df = yf.download(
        ticker,
        period=selected_period,
        interval=selected_interval,
        auto_adjust=True,
        progress=False
    )

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.dropna(inplace=True)

    return df


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def interval_to_minutes(interval_value):
    interval_value = interval_value.lower().strip()

    try:
        if interval_value.endswith("m"):
            return int(interval_value.replace("m", ""))

        if interval_value.endswith("h"):
            return int(interval_value.replace("h", "")) * 60

        if interval_value.endswith("d"):
            return int(interval_value.replace("d", "")) * 1440

        return 1440

    except Exception:
        return 1440


def time_to_minutes(time_value):
    h, m = map(int, time_value.split(":"))
    return h * 60 + m


# =====================================================
# SESSION STATE
# =====================================================

if "loaded_data" not in st.session_state:
    st.session_state.loaded_data = None


# =====================================================
# LOAD DATA
# =====================================================

if run_button:
    try:
        st.session_state.loaded_data = load_data(
            stock_input,
            period,
            interval
        )

    except Exception as e:
        st.error(f"Download Error: {e}")
        st.stop()


# =====================================================
# CHECK DATA
# =====================================================

df = st.session_state.loaded_data

if df is None:
    st.info("Enter inputs, then click ▶ Run Analysis")
    st.stop()

if df.empty:
    st.error("No data found. Please check stock symbol, period, or interval.")
    st.stop()


# =====================================================
# PREPARE DATA
# =====================================================

df = df.copy()

df["OnlyDate"] = pd.to_datetime(df.index).date

unique_dates = sorted(df["OnlyDate"].unique())

grouped_dates = [
    unique_dates[i:i + group_days]
    for i in range(0, len(unique_dates), group_days)
]

results = []

interval_minutes = interval_to_minutes(interval)


# =====================================================
# PROCESS GROUPS
# =====================================================

for group in grouped_dates:
    group_df = df[df["OnlyDate"].isin(group)].copy()

    if len(group_df) == 0:
        continue

    date_label = " + ".join([str(d) for d in group])

    open_price = float(group_df["Open"].iloc[0])
    close_price = float(group_df["Close"].iloc[-1])
    highest_price = float(group_df["High"].max())
    lowest_price = float(group_df["Low"].min())
    average_price = float(group_df["Close"].mean())

    total_change = close_price - open_price

    if open_price != 0:
        percent_change = (total_change / open_price) * 100
    else:
        percent_change = 0

    highest_idx = group_df["High"].idxmax()
    lowest_idx = group_df["Low"].idxmin()

    highest_time = highest_idx.strftime("%H:%M")
    lowest_time = lowest_idx.strftime("%H:%M")

    crossing_times = []

    for i in range(1, len(group_df)):
        prev_price = group_df["Close"].iloc[i - 1]
        curr_price = group_df["Close"].iloc[i]

        crossed = (
            (
                prev_price < average_price
                and curr_price > average_price
            )
            or
            (
                prev_price > average_price
                and curr_price < average_price
            )
        )

        if crossed:
            crossing_times.append(group_df.index[i])

    crossing_count = len(crossing_times)

    if len(crossing_times) > 1:
        gaps = []

        for i in range(1, len(crossing_times)):
            diff = (
                crossing_times[i] - crossing_times[i - 1]
            ).total_seconds() / 60

            gaps.append(diff)

        avg_cross_gap = round(np.mean(gaps), 2)

    else:
        avg_cross_gap = 0

    above_avg = len(group_df[group_df["Close"] > average_price])
    below_avg = len(group_df[group_df["Close"] < average_price])

    time_above_avg = above_avg * interval_minutes
    time_below_avg = below_avg * interval_minutes

    results.append({
        "Date Group": date_label,
        "Open": round(open_price, 2),
        "Close": round(close_price, 2),
        "Change": round(total_change, 2),
        "% Change": round(percent_change, 2),
        "Highest": round(highest_price, 2),
        "Lowest": round(lowest_price, 2),
        "Average": round(average_price, 2),
        "Crossings": crossing_count,
        "Avg Crossing Gap (mins)": avg_cross_gap,
        "Time Above Avg (mins)": time_above_avg,
        "Time Below Avg (mins)": time_below_avg,
        "Highest Time": highest_time,
        "Lowest Time": lowest_time
    })


# =====================================================
# RESULT DATAFRAME
# =====================================================

result_df = pd.DataFrame(results)

if result_df.empty:
    st.error("No analysis results created.")
    st.stop()

plot_df = result_df.copy()

plot_df["Highest Time Numeric"] = plot_df["Highest Time"].apply(time_to_minutes)
plot_df["Lowest Time Numeric"] = plot_df["Lowest Time"].apply(time_to_minutes)


# =====================================================
# TABLE SCREEN
# =====================================================

if st.session_state.page == "table":
    st.subheader("📋 Analysis Table")

    transpose_df = result_df.transpose()

    st.dataframe(
        transpose_df,
        use_container_width=True,
        height=900
    )


# =====================================================
# PLOT SCREEN
# =====================================================

elif st.session_state.page == "plot":
    st.subheader("📊 Full Screen Interactive Analytics Graph")

    if len(selected_plots) == 0:
        st.warning("Please select at least one graph column from the sidebar.")
        st.stop()

    fig = go.Figure()

    colors = [
        "blue",
        "red",
        "green",
        "orange",
        "purple",
        "brown",
        "pink",
        "black",
        "cyan",
        "magenta"
    ]

    markers = [
        "circle",
        "square",
        "diamond",
        "cross",
        "x",
        "triangle-up",
        "star"
    ]

    for i, col in enumerate(selected_plots):
        if col not in plot_df.columns:
            st.error(f"Column not found: {col}")
            continue

        fig.add_trace(
            go.Scatter(
                x=plot_df["Date Group"],
                y=plot_df[col],
                mode="lines+markers",
                name=col,
                line=dict(
                    color=colors[i % len(colors)],
                    width=4
                ),
                marker=dict(
                    symbol=markers[i % len(markers)],
                    size=12
                )
            )
        )

    fig.update_layout(
        height=900,
        title=f"{stock_input} Analytics Dashboard",
        title_font_size=28,
        hovermode="x unified",
        template="plotly_dark",
        xaxis=dict(
            title="Date Groups",
            tickangle=-45,
            rangeslider=dict(visible=True)
        ),
        yaxis=dict(
            title="Values"
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =====================================================
# DOWNLOAD SCREEN
# =====================================================

elif st.session_state.page == "downloads":
    st.subheader("⬇ Download Results")

    csv = result_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇ Download CSV",
        csv,
        file_name=f"{stock_input}_analysis.csv",
        mime="text/csv"
    )

    excel_buffer = BytesIO()

    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl"
    ) as writer:
        result_df.to_excel(
            writer,
            index=False
        )

    st.download_button(
        "⬇ Download Excel",
        excel_buffer.getvalue(),
        file_name=f"{stock_input}_analysis.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
