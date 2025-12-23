import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
import re
from datetime import date

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(page_title="Analisi BEL & ALM", layout="wide")
st.title("📊 Analisi BEL e ALM")

# =====================================================
# COSTANTI
# =====================================================
BEL_ROWS = [
    "BEL Undiscounted",
    "BEL Discounted",
    "BEL IR DOWN",
    "Stress Down",
    "BEL IR UP",
    "Stress Up"
]

VAR_ROWS = [
    "Δ BEL Undiscounted",
    "Δ BEL Discounted",
    "Δ BEL IR DOWN",
    "Δ Stress Down",
    "Δ BEL IR UP",
    "Δ Stress Up"
]

file_name = "Summary.xlsx"

MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12
}

# =====================================================
# UTILITY
# =====================================================
def end_of_month_from_period(col):
    """
    Jan '25 vs Dec '24 → 31/01/2025
    """
    match = re.search(r"([A-Za-z]{3})\s*'(\d{2})", str(col))
    if not match:
        return None

    month = MONTH_MAP[match.group(1).lower()]
    year = 2000 + int(match.group(2))
    last_day = calendar.monthrange(year, month)[1]

    return date(year, month, last_day)

# =====================================================
# LOAD DATA
# =====================================================
@st.cache_data
def load_bel_tables():
    df_raw = pd.read_excel(
        file_name,
        sheet_name="Analisi BEL Aggregate",
        usecols="B:N",
        header=None
    )

    def split_tables(df):
        tables, start = [], None
        for i in range(len(df)):
            if not df.iloc[i].isna().all():
                start = i if start is None else start
            elif start is not None:
                tables.append(df.iloc[start:i])
                start = None
        if start is not None:
            tables.append(df.iloc[start:])
        return tables

    def prepare(df):
        df = df.copy().reset_index(drop=True)
        df.columns = df.iloc[1]
        df = df.iloc[2:]
        df = df.set_index(df.columns[0])
        return df.apply(pd.to_numeric, errors="coerce")

    t1, t2, t3 = split_tables(df_raw)
    return prepare(t1), prepare(t2), prepare(t3)

@st.cache_data
def load_alm():
    df = pd.read_excel(file_name, sheet_name="Analisi ALM", usecols="A:E")
    df = df.dropna(how="all")
    df = df.set_index(df.columns[0])
    df.index = pd.to_datetime(df.index, errors="coerce")
    return df.dropna(how="all")

table_1, table_2, table_3 = load_bel_tables()
df_alm = load_alm()

# =====================================================
# PLOT
# =====================================================
def plot_interactive(df, selected, title, x_name):
    df_plot = df.loc[selected].T
    df_plot[x_name] = df_plot.index

    df_long = df_plot.melt(
        id_vars=x_name,
        var_name="Grandezza",
        value_name="Valore"
    )

    fig = px.line(
        df_long,
        x=x_name,
        y="Valore",
        color="Grandezza",
        markers=True,
        title=title
    )

    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# GRAFICO 1 – BEL (CON DATE)
# =====================================================
st.subheader("📌 BEL")

rows = [r for r in BEL_ROWS if r in table_1.index]
selected = st.multiselect("Seleziona le grandezze", rows, default=rows)

date_map = {
    c: end_of_month_from_period(c)
    for c in table_1.columns
    if end_of_month_from_period(c)
}

df_bel = table_1.copy()
df_bel.columns = [date_map[c] for c in df_bel.columns]

dates = list(df_bel.columns)

st.markdown("**Seleziona il periodo di riferimento**")
c1, c2 = st.columns(2)
start = c1.date_input("Data iniziale", min(dates))
end = c2.date_input("Data finale", max(dates))

df_bel_f = df_bel.loc[:, (df_bel.columns >= start) & (df_bel.columns <= end)]

if selected:
    plot_interactive(df_bel_f, selected, "BEL", "Data")

# =====================================================
# GRAFICO 2 – TREND BEL (SENZA PERIODO)
# =====================================================
st.divider()
st.subheader("📌 Trend BEL")

trend_type = st.selectbox(
    "Seleziona il tipo di trend",
    ["Monetary Trend BEL", "% Trend BEL"]
)

df_trend = table_2 if trend_type == "Monetary Trend BEL" else table_3

rows = [r for r in VAR_ROWS if r in df_trend.index]
selected = st.multiselect(
    "Seleziona le grandezze",
    rows,
    default=rows,
    key="trend_rows"
)

if selected:
    plot_interactive(df_trend, selected, trend_type, "Periodo")

# =====================================================
# GRAFICO 3 – ALM (INVARIATO)
# =====================================================
st.divider()
st.subheader("📌 Analisi ALM – Duration Trend")

cols = st.multiselect(
    "Seleziona le grandezze",
    df_alm.columns.tolist(),
    default=df_alm.columns.tolist()
)

dates = df_alm.index.dropna()

st.markdown("**Seleziona il periodo di riferimento**")
c1, c2 = st.columns(2)
start = c1.date_input("Data iniziale", dates.min().date(), key="alm_start")
end = c2.date_input("Data finale", dates.max().date(), key="alm_end")

df_alm_f = df_alm.loc[start:end]

if cols:
    last = df_alm_f.iloc[-1]
    opt = last["Duration Liabilities"] * (1 - last["Surplus Asset %"])

    if st.button("Ottimizzazione Duration Asset"):
        st.info(f"Duration Asset ottimale: **{opt:.2f}**")

    plot_interactive(df_alm_f, cols, "Duration Trend", "Data")
