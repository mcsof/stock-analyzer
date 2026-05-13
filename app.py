import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

# =====================================================
# PAGE
# =====================================================

st.set_page_config(
    page_title="Stock Analytics Dashboard",
    layout="wide"
)


# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.header("Inputs")

stock_input = st.sidebar.text_input(
    "Enter Stock Symbol",
    value="AAPL"
)

period = st.sidebar.text_input(
    "Enter Period",
    value="5d"
)

st.sidebar.caption(
    "Examples: 1d, 2d, 5d, 1mo, 3mo, 1y"
)

interval = st.sidebar.text_input(
    "Enter Interval",
    value="5m"
)

st.sidebar.caption(
    "Examples: 1m, 5m, 10m, 15m, 30m, 60m, 1d"
)

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

# IMPORTANT:
# No run button needed for graph changes

selected_plots = st.sidebar.multiselect(

    "Select Graph Columns",

    plot_columns,

    default=["Close"]
)

# =====================================================
# CACHE DATA
# =====================================================

@st.cache_data
def load_data(
    ticker,
    period,
    interval
):

    df = yf.download(

        ticker,

        period=period,

        interval=interval,

        auto_adjust=True,

        progress=False
    )

    if isinstance(
        df.columns,
        pd.MultiIndex
    ):

        df.columns = (
            df.columns
            .get_level_values(0)
        )

    df.dropna(inplace=True)

    return df

# =====================================================
# LOAD
# =====================================================

# =====================================================
# RUN BUTTON
# =====================================================

run_button = st.sidebar.button("▶ Run Analysis")

# =====================================================
# SESSION STATE
# =====================================================

if "loaded_data" not in st.session_state:
    st.session_state.loaded_data = None

# =====================================================
# LOAD ONLY WHEN BUTTON CLICKED
# =====================================================

if run_button:

    st.session_state.loaded_data = load_data(
        stock_input,
        period,
        interval
    )

# =====================================================
# USE SAVED DATA
# =====================================================

df = st.session_state.loaded_data

# =====================================================
# EMPTY CHECK
# =====================================================

if df is None:

    st.info("Click ▶ Run Analysis")
    st.stop()

# =====================================================
# EMPTY CHECK
# =====================================================

if df.empty:

    st.error("No data found")
    st.stop()

# =====================================================
# DATE
# =====================================================

df["Date"] = (
    df.index.strftime("%d %b")
)

unique_dates = list(
    df["Date"].unique()
)

grouped_dates = [

    unique_dates[i:i + group_days]

    for i in range(
        0,
        len(unique_dates),
        group_days
    )
]

results = []

# =====================================================
# PROCESS
# =====================================================

for group in grouped_dates:

    group_df = df[
        df["Date"].isin(group)
    ].copy()

    if len(group_df) == 0:
        continue

    date_label = " + ".join(group)

    open_price = float(
        group_df["Open"].iloc[0]
    )

    close_price = float(
        group_df["Close"].iloc[-1]
    )

    highest_price = float(
        group_df["High"].max()
    )

    lowest_price = float(
        group_df["Low"].min()
    )

    average_price = float(
        group_df["Close"].mean()
    )

    total_change = (
        close_price - open_price
    )

    percent_change = (
        total_change / open_price
    ) * 100

    highest_idx = (
        group_df["High"].idxmax()
    )

    lowest_idx = (
        group_df["Low"].idxmin()
    )

    highest_time = (
        highest_idx.strftime("%H:%M")
    )

    lowest_time = (
        lowest_idx.strftime("%H:%M")
    )

    # =================================================
    # CROSSINGS
    # =================================================

    crossing_times = []

    for i in range(
        1,
        len(group_df)
    ):

        prev_price = (
            group_df["Close"]
            .iloc[i - 1]
        )

        curr_price = (
            group_df["Close"]
            .iloc[i]
        )

        crossed = (

            (
                prev_price < average_price
                and
                curr_price > average_price
            )

            or

            (
                prev_price > average_price
                and
                curr_price < average_price
            )
        )

        if crossed:

            crossing_times.append(
                group_df.index[i]
            )

    crossing_count = len(
        crossing_times
    )

    # =================================================
    # AVG GAP
    # =================================================

    if len(crossing_times) > 1:

        gaps = []

        for i in range(
            1,
            len(crossing_times)
        ):

            diff = (

                crossing_times[i]

                -

                crossing_times[i - 1]

            ).total_seconds() / 60

            gaps.append(diff)

        avg_cross_gap = round(
            np.mean(gaps),
            2
        )

    else:

        avg_cross_gap = 0

    # =================================================
    # INTERVAL
    # =================================================

    if "m" in interval:

        interval_minutes = int(
            interval.replace("m", "")
        )

    else:

        interval_minutes = 1440

    above_avg = len(

        group_df[
            group_df["Close"]
            > average_price
        ]
    )

    below_avg = len(

        group_df[
            group_df["Close"]
            < average_price
        ]
    )

    time_above_avg = (
        above_avg * interval_minutes
    )

    time_below_avg = (
        below_avg * interval_minutes
    )

    # =================================================
    # SAVE
    # =================================================

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
# DATAFRAME
# =====================================================

result_df = pd.DataFrame(results)

# =====================================================
# TIME NUMERIC
# =====================================================

def time_to_minutes(t):

    h, m = map(
        int,
        t.split(":")
    )

    return h * 60 + m

plot_df = result_df.copy()

plot_df[
    "Highest Time Numeric"
] = plot_df[
    "Highest Time"
].apply(time_to_minutes)

plot_df[
    "Lowest Time Numeric"
] = plot_df[
    "Lowest Time"
].apply(time_to_minutes)

# =====================================================
# LAYOUT
# =====================================================

left, right = st.columns([1.2, 2])

# =====================================================
# TABLE
# =====================================================

with left:

    st.subheader("📋 Analysis Table")

transpose_df = result_df.transpose()

st.dataframe(
    transpose_df,
    use_container_width=True,
    height=700
)

# =====================================================
# BIG GRAPH
# =====================================================

# =====================================================
# BIG GRAPH WITH MULTIPLE Y AXES
# =====================================================

with right:

    st.subheader("📊 Analytics Graph")

    fig, ax1 = plt.subplots(
        figsize=(20, 10)
    )

    axes = [ax1]

    # -------------------------------------------------
    # CREATE EXTRA Y AXES
    # -------------------------------------------------

    for i in range(1, len(selected_plots)):

        ax_new = ax1.twinx()

        ax_new.spines["right"].set_position(
            ("outward", 80 * (i - 1))
        )

        axes.append(ax_new)

    # -------------------------------------------------
    # PLOT
    # -------------------------------------------------

# =====================================================
# BIG GRAPH WITH COLORS
# =====================================================

with right:

    st.subheader("📊 Analytics Graph")

    fig, ax1 = plt.subplots(
        figsize=(20, 10)
    )

    axes = [ax1]

    # -------------------------------------------------
    # COLORS
    # -------------------------------------------------

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

    # -------------------------------------------------
    # MARKERS
    # -------------------------------------------------

    markers = [

        "o",
        "s",
        "^",
        "D",
        "*",
        "X",
        "P",
        "v",
        "<",
        ">"
    ]

    # -------------------------------------------------
    # EXTRA AXES
    # -------------------------------------------------

    for i in range(1, len(selected_plots)):

        ax_new = ax1.twinx()

        ax_new.spines["right"].set_position(
            ("outward", 70 * (i - 1))
        )

        axes.append(ax_new)

    # -------------------------------------------------
    # PLOT
    # -------------------------------------------------

    for i, col in enumerate(selected_plots):

        color = colors[
            i % len(colors)
        ]

        marker = markers[
            i % len(markers)
        ]

        axes[i].plot(

            plot_df["Date Group"],

            plot_df[col],

            color=color,

            marker=marker,

            linewidth=3,

            markersize=9,

            label=col
        )

        axes[i].set_ylabel(
            col,
            fontsize=12,
            color=color
        )

        axes[i].tick_params(
            axis='y',
            colors=color
        )

        axes[i].legend(
            loc='upper left'
        )

    # -------------------------------------------------

    ax1.set_xlabel(
        "Date Groups",
        fontsize=14
    )

    plt.xticks(
        rotation=45,
        fontsize=11
    )

    ax1.set_title(

        f"{stock_input} Multi Analytics Graph",

        fontsize=24,

        fontweight='bold'
    )

    ax1.grid(
        True,
        linestyle='--',
        alpha=0.6
    )

    st.pyplot(
        fig,
        use_container_width=True
    )

# =====================================================
# DOWNLOADS
# =====================================================

st.divider()

csv = result_df.to_csv(
    index=False
).encode("utf-8")

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
