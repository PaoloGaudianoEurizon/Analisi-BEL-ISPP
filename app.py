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

    # MANTIENE LE COLONNE ESATTAMENTE COME NELL'EXCEL
    bel_cols = df_raw.iloc[2]

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

    def prepare(df, cols):
        df = df.copy().reset_index(drop=True)
        df.columns = cols
        df = df.iloc[3:]
        df = df.set_index(df.columns[0])
        return df.apply(pd.to_numeric, errors="coerce")

    t1, t2, t3 = split_tables(df_raw)

    return (
        prepare(t1, bel_cols),
        prepare(t2, bel_cols),
        prepare(t3, bel_cols)
    )

@st.cache_data
def load_alm():
    df = pd.read_excel(
        file_name,
        sheet_name="Analisi ALM",
        usecols="A:E"
    )
    df = df.dropna(how="all")
    df = df.set_index(df.columns[0])  # INDICE COME DA EXCEL
    return df.dropna(how="all")

table_1, table_2, table_3 = load_bel_tables()
df_alm = load_alm()

# =====================================================
# FUNZIONE PLOT
# =====================================================
def plot_interactive(df, selected, title, select_rows=False):
    df_plot = df.loc[selected].T if select_rows else df[selected]
    df_plot["Asse"] = df_plot.index

    df_long = df_plot.melt(
        id_vars="Asse",
        var_name="Grandezza",
        value_name="Valore"
    )

    fig = px.line(
        df_long,
        x="Asse",
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

date_options = list(table_1.columns)

st.markdown("**Seleziona il periodo di riferimento**")
c1, c2 = st.columns(2)

start = c1.selectbox(
    "Data iniziale",
    date_options,
    index=0
)

end = c2.selectbox(
    "Data finale",
    date_options,
    index=len(date_options) - 1
)

cols = [
    c for c in date_options
    if date_options.index(start) <= date_options.index(c) <= date_options.index(end)
]

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

date_options = list(df_trend.columns)

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

cols = [
    c for c in date_options
    if date_options.index(start) <= date_options.index(c) <= date_options.index(end)
]

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

index_options = list(df_alm.index)

st.markdown("**Seleziona il periodo di riferimento**")
c1, c2 = st.columns(2)

start = c1.selectbox(
    "Data iniziale",
    index_options,
    index=0,
    key="alm_start"
)

end = c2.selectbox(
    "Data finale",
    index_options,
    index=len(index_options) - 1,
    key="alm_end"
)

df_alm_f = df_alm.loc[
    index_options[index_options.index(start): index_options.index(end) + 1]
]

if cols_selected and not df_alm_f.empty:
    plot_interactive(df_alm_f, cols_selected, "Duration Trend")
