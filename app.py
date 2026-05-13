import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Stock Analytics Dashboard",
    layout="wide"
)

# =====================================================
# TITLE
# =====================================================

st.title("📈 Stock Analytics Dashboard")

# =====================================================
# SIDEBAR SETTINGS
# =====================================================

st.sidebar.header("Settings")

stock_input = st.sidebar.text_input(
    "Stock Ticker",
    value="AAPL"
)

period = st.sidebar.selectbox(
    "Period",
    [
        "1d",
        "5d",
        "1mo",
        "3mo",
        "6mo",
        "1y",
        "2y"
    ],
    index=1
)

interval = st.sidebar.selectbox(
    "Interval",
    [
        "1m",
        "2m",
        "5m",
        "15m",
        "30m",
        "60m",
        "90m",
        "1d"
    ],
    index=2
)

group_days = st.sidebar.number_input(
    "Group Days",
    min_value=1,
    max_value=30,
    value=1
)

# =====================================================
# DOWNLOAD DATA
# =====================================================

@st.cache_data
def load_data(ticker, period, interval):

    df = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False
    )

    return df

df = load_data(
    stock_input,
    period,
    interval
)

# =====================================================
# VALIDATION
# =====================================================

if len(df) == 0:

    st.error("No data found.")

    st.stop()

# =====================================================
# FIX MULTI INDEX
# =====================================================

if isinstance(df.columns, pd.MultiIndex):

    df.columns = df.columns.get_level_values(0)

df.dropna(inplace=True)

# =====================================================
# DATE COLUMN
# =====================================================

df["Date"] = df.index.strftime("%d %b")

unique_dates = list(df["Date"].unique())

# =====================================================
# GROUP DAYS
# =====================================================

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
# PROCESS DATA
# =====================================================

for group in grouped_dates:

    group_df = df[
        df["Date"].isin(group)
    ].copy()

    if len(group_df) == 0:

        continue

    # =====================================================
    # LABEL
    # =====================================================

    date_label = " + ".join(group)

    # =====================================================
    # BASIC VALUES
    # =====================================================

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

    # =====================================================
    # CHANGE
    # =====================================================

    total_change = (
        close_price - open_price
    )

    percent_change = (
        total_change / open_price
    ) * 100

    # =====================================================
    # HIGH / LOW TIMES
    # =====================================================

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

    # =====================================================
    # CROSSINGS
    # =====================================================

    crossing_times = []

    for i in range(1, len(group_df)):

        prev_price = (
            group_df["Close"].iloc[i - 1]
        )

        curr_price = (
            group_df["Close"].iloc[i]
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

    crossing_count = len(crossing_times)

    # =====================================================
    # AVG CROSS GAP
    # =====================================================

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

    # =====================================================
    # ABOVE / BELOW AVG
    # =====================================================

    if "m" in interval:

        interval_minutes = int(
            interval.replace("m", "")
        )

    elif "h" in interval:

        interval_minutes = (
            int(
                interval.replace("h", "")
            ) * 60
        )

    else:

        interval_minutes = 1440

    above_avg = len(

        group_df[
            group_df["Close"] > average_price
        ]
    )

    below_avg = len(

        group_df[
            group_df["Close"] < average_price
        ]
    )

    time_above_avg = (
        above_avg * interval_minutes
    )

    time_below_avg = (
        below_avg * interval_minutes
    )

    # =====================================================
    # SAVE RESULTS
    # =====================================================

    results.append({

        "Date Group": date_label,

        "Open": round(
            open_price,
            2
        ),

        "Close": round(
            close_price,
            2
        ),

        "Change": round(
            total_change,
            2
        ),

        "% Change": round(
            percent_change,
            2
        ),

        "Highest": round(
            highest_price,
            2
        ),

        "Highest Time": highest_time,

        "Lowest": round(
            lowest_price,
            2
        ),

        "Lowest Time": lowest_time,

        "Average": round(
            average_price,
            2
        ),

        "Crossings": crossing_count,

        "Avg Crossing Gap (mins)": avg_cross_gap,

        "Time Above Avg (mins)": time_above_avg,

        "Time Below Avg (mins)": time_below_avg
    })

# =====================================================
# RESULT DATAFRAME
# =====================================================

result_df = pd.DataFrame(results)

# =====================================================
# DISPLAY TABLE
# =====================================================

st.subheader("📋 Analysis Table")

st.dataframe(
    result_df,
    use_container_width=True
)

# =====================================================
# CSV DOWNLOAD
# =====================================================

csv = result_df.to_csv(
    index=False
).encode("utf-8")

st.download_button(

    label="⬇ Download CSV",

    data=csv,

    file_name=f"{stock_input}_analysis.csv",

    mime="text/csv"
)

# =====================================================
# EXCEL DOWNLOAD
# =====================================================

excel_buffer = BytesIO()

with pd.ExcelWriter(
    excel_buffer,
    engine="openpyxl"
) as writer:

    result_df.to_excel(
        writer,
        index=False,
        sheet_name="Analysis"
    )

excel_data = excel_buffer.getvalue()

st.download_button(

    label="⬇ Download Excel",

    data=excel_data,

    file_name=f"{stock_input}_analysis.xlsx",

    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =====================================================
# TIME TO NUMERIC
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
].apply(
    time_to_minutes
)

plot_df[
    "Lowest Time Numeric"
] = plot_df[
    "Lowest Time"
].apply(
    time_to_minutes
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

selected_plots = st.multiselect(

    "📊 Select Metrics To Plot",

    plot_columns,

    default=["Close"]
)

# =====================================================
# PLOT
# =====================================================

if len(selected_plots) > 0:

    fig, ax = plt.subplots(
        figsize=(16, 7)
    )

    for col in selected_plots:

        ax.plot(

            plot_df["Date Group"],

            plot_df[col],

            marker='o',

            label=col
        )

    ax.set_xlabel("Day")

    ax.set_ylabel("Values")

    ax.set_title(
        f"{stock_input} Analytics"
    )

    plt.xticks(rotation=45)

    ax.grid(True)

    ax.legend()

    st.pyplot(fig)

# =====================================================
# RAW DATA
# =====================================================

with st.expander(
    "📄 Show Raw Downloaded Data"
):

    st.dataframe(
        df,
        use_container_width=True
    )