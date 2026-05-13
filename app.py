import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------
st.set_page_config(
    page_title="Stock Analyzer",
    layout="wide"
)

st.title("📈 Stock Analyzer")

# ------------------------------------------------
# USER INPUTS
# ------------------------------------------------
ticker = st.text_input(
    "Enter stock ticker",
    value="AAPL"
).upper()

period = st.selectbox(
    "Select period",
    ["5d", "1mo", "3mo"],
    index=0
)

interval = st.selectbox(
    "Select interval",
    ["1m", "2m", "5m", "15m", "30m", "60m"],
    index=2
)

group_days = st.number_input(
    "Group days",
    min_value=1,
    max_value=10,
    value=1
)

selected_date = st.date_input(
    "Select ending date",
    value=pd.Timestamp.today()
)

# ------------------------------------------------
# CACHE DOWNLOAD
# ------------------------------------------------
@st.cache_data
def load_data(ticker, period, interval):

    data = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False
    )

    return data


# ------------------------------------------------
# RUN ANALYSIS
# ------------------------------------------------
if st.button("Run Analysis"):

    with st.spinner("Downloading stock data..."):

        df = load_data(
            ticker,
            period,
            interval
        )

    # ------------------------------------------------
    # FIX MULTI INDEX
    # ------------------------------------------------
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # ------------------------------------------------
    # REMOVE EMPTY ROWS
    # ------------------------------------------------
    df.dropna(inplace=True)

    # ------------------------------------------------
    # FIX TIMEZONE ISSUE
    # ------------------------------------------------
    df.index = pd.to_datetime(
        df.index
    ).tz_localize(None)

    # ------------------------------------------------
    # FILTER PREVIOUS 5 DAYS
    # ------------------------------------------------
    selected_date = pd.Timestamp(
        selected_date
    )

    start_date = (
        selected_date - pd.Timedelta(days=5)
    )

    df = df[
        (df.index >= start_date)
        &
        (df.index <= selected_date)
    ]

    # ------------------------------------------------
    # CHECK DATA
    # ------------------------------------------------
    if len(df) == 0:

        st.error(
            "No data found for selected dates."
        )

    else:

        results = []

        # ------------------------------------------------
        # DATE COLUMN
        # ------------------------------------------------
        df["Date"] = df.index.strftime(
            "%d %b"
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

        # ------------------------------------------------
        # ANALYSIS LOOP
        # ------------------------------------------------
        for group in grouped_dates:

            group_df = df[
                df["Date"].isin(group)
            ].copy()

            if len(group_df) == 0:
                continue

            date_label = " + ".join(group)

            # ------------------------------------------------
            # PRICE STATS
            # ------------------------------------------------
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

            # ------------------------------------------------
            # CHANGE
            # ------------------------------------------------
            total_change = (
                close_price - open_price
            )

            percent_change = (
                total_change / open_price
            ) * 100

            # ------------------------------------------------
            # HIGH LOW TIMES
            # ------------------------------------------------
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

            # ------------------------------------------------
            # CROSSINGS
            # ------------------------------------------------
            crossing_times = []

            for i in range(
                1,
                len(group_df)
            ):

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

            crossing_count = len(
                crossing_times
            )

            # ------------------------------------------------
            # AVG CROSSING GAP
            # ------------------------------------------------
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

            # ------------------------------------------------
            # TIME ABOVE BELOW AVG
            # ------------------------------------------------
            interval_minutes = int(
                interval.replace("m", "")
            )

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

            # ------------------------------------------------
            # SAVE RESULTS
            # ------------------------------------------------
            results.append({

                "Date Group": date_label,

                "Stock": ticker,

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

                "Avg Crossing Gap (mins)": (
                    avg_cross_gap
                ),

                "Time Above Avg (mins)": (
                    time_above_avg
                ),

                "Time Below Avg (mins)": (
                    time_below_avg
                )
            })

        # ------------------------------------------------
        # RESULT DATAFRAME
        # ------------------------------------------------
        result_df = pd.DataFrame(results)

        # SAVE TO SESSION STATE
        st.session_state["result_df"] = result_df

# ------------------------------------------------
# DISPLAY RESULTS
# ------------------------------------------------
if "result_df" in st.session_state:

    result_df = st.session_state["result_df"]

    # ------------------------------------------------
    # SHOW DATAFRAME
    # ------------------------------------------------
    st.subheader("📊 Analysis Result")

    st.dataframe(
        result_df,
        use_container_width=True
    )

    # ------------------------------------------------
    # NUMERIC COLUMNS
    # ------------------------------------------------
    numeric_columns = result_df.select_dtypes(
        include=["number"]
    ).columns.tolist()

    # ------------------------------------------------
    # SELECT COLUMNS TO PLOT
    # ------------------------------------------------
    selected_columns = st.multiselect(
        "Select columns to plot",
        numeric_columns,
        default=["% Change"]
    )

    # ------------------------------------------------
    # CHART
    # ------------------------------------------------
    if selected_columns:

        st.subheader("📈 Chart")

        st.line_chart(
            data=result_df,
            x="Date Group",
            y=selected_columns
        )

    # ------------------------------------------------
    # DOWNLOAD CSV
    # ------------------------------------------------
    csv = result_df.to_csv(
        index=False
    )

    st.download_button(
        "Download CSV",
        csv,
        "stock_analysis.csv",
        "text/csv"
    )