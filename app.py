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

# =====================================================
# UTILITY
# =====================================================
MONTH_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

def parse_month_year(text):
    text = str(text).lower()
    for m, month in MONTH_MAP.items():
        if m in text:
            year = re.findall(r"\d{2,4}", text)
            if year:
                y = int(year[0])
                if y < 100:
                    y += 2000
                last_day = calendar.monthrange(y, month)[1]
                return date(y, month, last_day)
    return None

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
def plot_interactive(df, selected, title, select_rows=False):
    df_plot = df.loc[selected].T if select_rows else df[selected]
    df_plot["Data"] = df_plot.index
    df_long = df_plot.melt(id_vars="Data", var_name="Grandezza", value_name="Valore")

    fig = px.line(
        df_long,
        x="Data",
        y="Valore",
        color="Grandezza",
        markers=True,
        title=title
    )

    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# GRAFICO 1 - BEL (DATE COME ALM)
# =====================================================
st.subheader("📌 BEL")

rows = [r for r in BEL_ROWS if r in table_1.index]
selected = st.multiselect("Seleziona le grandezze", rows, default=rows)

date_map = {c: parse_month_year(c) for c in table_1.columns}
date_map = {k: v for k, v in date_map.items() if v}

st.markdown("**Seleziona il periodo di riferimento**")
c1, c2 = st.columns(2)
start = c1.date_input("Data iniziale", min(date_map.values()), key="bel_start")
end = c2.date_input("Data finale", max(date_map.values()), key="bel_end")

cols = [c for c, d in date_map.items() if start <= d <= end]

if selected:
    plot_interactive(table_1[cols], selected, "BEL", select_rows=True)

# =====================================================
# GRAFICO 2 - TREND BEL (PERIODI VS)
# =====================================================
st.divider()
st.subheader("📌 Trend BEL")

trend_type = st.selectbox(
    "Seleziona il tipo di trend",
    ["Monetary Trend BEL", "% Trend BEL"]
)

df_trend = table_2 if trend_type == "Monetary Trend BEL" else table_3
rows = [r for r in VAR_ROWS if r in df_trend.index]
selected = st.multiselect("Seleziona le grandezze", rows, default=rows, key="trend_rows")

trend_cols = list(df_trend.columns)

st.markdown("**Seleziona il periodo di riferimento**")
c1, c2 = st.columns(2)
p_start = c1.selectbox("Periodo iniziale", trend_cols, index=0)
p_end = c2.selectbox("Periodo finale", trend_cols, index=len(trend_cols) - 1)

start_idx = trend_cols.index(p_start)
end_idx = trend_cols.index(p_end)

if start_idx <= end_idx:
    cols = trend_cols[start_idx:end_idx + 1]
else:
    cols = trend_cols[end_idx:start_idx + 1]

if selected:
    plot_interactive(df_trend[cols], selected, trend_type, select_rows=True)

# =====================================================
# GRAFICO 3 - ALM (INVARIATO)
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

    plot_interactive(df_alm_f, cols, "Duration Trend")
