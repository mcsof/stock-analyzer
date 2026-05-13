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

st.title("📈 Stock Analytics Dashboard")

# =====================================================
# USER INPUTS
# =====================================================

st.sidebar.header("Inputs")

# -----------------------------------------------------

stock_input = st.sidebar.text_input(
    "Enter Stock Symbol",
    value="AAPL"
)

# -----------------------------------------------------

period = st.sidebar.selectbox(
    "Select Period",
    [
        "1d",
        "5d",
        "1mo",
        "3mo",
        "6mo",
        "1y"
    ],
    index=1
)

# -----------------------------------------------------

interval = st.sidebar.selectbox(
    "Select Time Interval",
    [
        "1m",
        "2m",
        "5m",
        "15m",
        "30m",
        "60m",
        "1d"
    ],
    index=2
)

# -----------------------------------------------------

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

    "Which Plot Do You Want?",

    plot_columns,

    default=["Close"]
)

# =====================================================
# RUN BUTTON
# =====================================================

run_button = st.sidebar.button("▶ Run Analysis")

# =====================================================
# ONLY RUN WHEN BUTTON CLICKED
# =====================================================

if run_button:

    # =================================================
    # VALIDATE COMBINATIONS
    # =================================================

    invalid = False

    if interval == "1m" and period not in ["1d", "5d"]:

        invalid = True

    elif interval in [
        "2m",
        "5m",
        "15m",
        "30m"
    ] and period == "1y":

        invalid = True

    if invalid:

        st.error(
            """
            Invalid Yahoo Finance combination.

            Examples:
            • 5d + 5m
            • 1mo + 15m
            • 6mo + 1d
            """
        )

        st.stop()

    # =================================================
    # DOWNLOAD DATA
    # =================================================

    @st.cache_data
    def load_data(
        ticker,
        period,
        interval
    ):

        try:

            df = yf.download(

                ticker,

                period=period,

                interval=interval,

                auto_adjust=True,

                progress=False
            )

            # --------------------------------------------

            if isinstance(
                df.columns,
                pd.MultiIndex
            ):

                df.columns = (
                    df.columns
                    .get_level_values(0)
                )

            # --------------------------------------------

            df.dropna(inplace=True)

            return df

        except Exception as e:

            st.error(
                f"Download Error: {e}"
            )

            return pd.DataFrame()

    # =================================================
    # LOAD
    # =================================================

    df = load_data(
        stock_input,
        period,
        interval
    )

    # =================================================
    # EMPTY CHECK
    # =================================================

    if df.empty:

        st.error(
            """
            No data found.

            Try:
            • AAPL
            • MSFT
            • TSLA

            Best:
            • 5d + 5m
            """
        )

        st.stop()

    # =================================================
    # DATE
    # =================================================

    df["Date"] = (
        df.index.strftime("%d %b")
    )

    unique_dates = list(
        df["Date"].unique()
    )

    # =================================================
    # GROUPS
    # =================================================

    grouped_dates = [

        unique_dates[i:i + group_days]

        for i in range(
            0,
            len(unique_dates),
            group_days
        )
    ]

    results = []

    # =================================================
    # PROCESS
    # =================================================

    for group in grouped_dates:

        group_df = df[
            df["Date"].isin(group)
        ].copy()

        if len(group_df) == 0:

            continue

        # ---------------------------------------------

        date_label = " + ".join(group)

        # =================================================
        # BASIC
        # =================================================

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

        # =================================================
        # CHANGE
        # =================================================

        total_change = (
            close_price - open_price
        )

        percent_change = (
            total_change / open_price
        ) * 100

        # =================================================
        # HIGH / LOW TIME
        # =================================================

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
        # INTERVAL MINUTES
        # =================================================

        if "m" in interval:

            interval_minutes = int(
                interval.replace("m", "")
            )

        else:

            interval_minutes = 1440

        # =================================================
        # ABOVE / BELOW AVG
        # =================================================

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

    # =================================================
    # =====================================================
# DATAFRAME
        # =====================================================
        
        result_df = pd.DataFrame(results)
        
        # =====================================================
        # TRANSPOSE TABLE
        # =====================================================
        
        st.subheader("📋 Analysis Table")
        
        transpose_df = result_df.transpose()
        
        st.dataframe(
            transpose_df,
            use_container_width=True,
            height=700
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
        
            file_name=(
                f"{stock_input}_analysis.csv"
            ),
        
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
        
            file_name=(
                f"{stock_input}_analysis.xlsx"
            ),
        
            mime=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
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
        # PLOT
        # =====================================================
        
        if len(selected_plots) > 0:
        
            st.subheader("📊 Plot")
        
            fig, ax = plt.subplots(
                figsize=(20, 8)
            )
        
            for col in selected_plots:
        
                ax.plot(
        
                    plot_df["Date Group"],
        
                    plot_df[col],
        
                    marker='o',
        
                    linewidth=3,
        
                    markersize=8,
        
                    label=col
                )
        
            # -------------------------------------------------
        
            ax.set_xlabel(
                "Day",
                fontsize=14
            )
        
            ax.set_ylabel(
                "Values",
                fontsize=14
            )
        
            ax.set_title(
                f"{stock_input} Analytics",
                fontsize=20,
                fontweight='bold'
            )
        
            # -------------------------------------------------
        
            plt.xticks(
                rotation=45,
                fontsize=12
            )
        
            plt.yticks(
                fontsize=12
            )
        
            # -------------------------------------------------
        
            ax.grid(
                True,
                linestyle='--',
                alpha=0.7
            )
        
            # -------------------------------------------------
        
            ax.legend(
                fontsize=12
            )
        
            # -------------------------------------------------
        
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