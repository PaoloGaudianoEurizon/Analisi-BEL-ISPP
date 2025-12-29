import streamlit as st
import pandas as pd
import plotly.express as px

# =====================================================
# CONFIG STREAMLIT
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

    bel_dates = pd.to_datetime(df_raw.iloc[2], errors="coerce")

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

    def prepare(df, dates):
        df = df.copy().reset_index(drop=True)
        df.columns = dates
        df = df.iloc[3:]
        df = df.set_index(df.columns[0])
        return df.apply(pd.to_numeric, errors="coerce")

    t1, t2, t3 = split_tables(df_raw)

    return (
        prepare(t1, bel_dates),
        prepare(t2, bel_dates),
        prepare(t3, bel_dates)
    )

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
# FUNZIONE PLOT
# =====================================================
def plot_interactive(df, selected, title, select_rows=False):
    df_plot = df.loc[selected].T if select_rows else df[selected]
    df_plot["Data"] = df_plot.index

    df_long = df_plot.melt(
        id_vars="Data",
        var_name="Grandezza",
        value_name="Valore"
    )

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
# GRAFICO 1 - BEL
# =====================================================
st.subheader("📌 BEL")

rows = [r for r in BEL_ROWS if r in table_1.index]
selected = st.multiselect(
    "Seleziona le grandezze",
    rows,
    default=rows
)

dates = table_1.columns.dropna()
date_options = sorted(dates)

st.markdown("**Seleziona il periodo di riferimento**")
c1, c2 = st.columns(2)

start = c1.selectbox(
    "Data iniziale",
    date_options,
    index=0,
    )

end = c2.selectbox(
    "Data finale",
    date_options,
    index=len(date_options) - 1,
    )

cols = [c for c in date_options if start <= c <= end]

if selected and cols:
    plot_interactive(table_1[cols], selected, "BEL", select_rows=True)

# =====================================================
# GRAFICO 2 - VARIAZIONE BEL
# =====================================================
st.divider()
st.subheader("📌 Variazione BEL")

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

dates = df_trend.columns.dropna()
date_options = sorted(dates)

st.markdown("**Seleziona il periodo di riferimento**")
c1, c2 = st.columns(2)

start = c1.selectbox(
    "Data iniziale",
    date_options,
    index=0,
    key="trend_start"
)

end = c2.selectbox(
    "Data finale",
    date_options,
    index=len(date_options) - 1,
    key="trend_end"
)

cols = [c for c in date_options if start <= c <= end]

if selected and cols:
    plot_interactive(df_trend[cols], selected, trend_type, select_rows=True)

# =====================================================
# GRAFICO 3 - ALM
# =====================================================
st.divider()
st.subheader("📌 Analisi ALM")

cols_selected = st.multiselect(
    "Seleziona le grandezze",
    df_alm.columns.tolist(),
    default=df_alm.columns.tolist()
)

dates = df_alm.index.dropna()
date_options = sorted(dates)

st.markdown("**Seleziona il periodo di riferimento**")
c1, c2 = st.columns(2)

start = c1.selectbox(
    "Data iniziale",
    date_options,
    index=0,
    key="alm_start"
)

end = c2.selectbox(
    "Data finale",
    date_options,
    index=len(date_options) - 1,
    key="alm_end"
)

df_alm_f = df_alm.loc[start:end]

if cols_selected and not df_alm_f.empty:
    plot_interactive(df_alm_f, cols_selected, "Duration Trend")

