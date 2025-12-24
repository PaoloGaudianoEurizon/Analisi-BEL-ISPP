## NEWTEST – CODICE COMPLETO CORRETTO

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
# FUNZIONE PLOT
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
# GRAFICO 1 - BEL
# =====================================================
st.subheader("📌 BEL")

rows = [r for r in BEL_ROWS if r in table_1.index]
selected_bel = st.multiselect("Seleziona le grandezze", rows, default=rows)

dates_bel = pd.to_datetime(table_1.columns, errors="coerce").dropna()

if not dates_bel.empty:
    st.markdown("**Seleziona il periodo di riferimento**")
    c1, c2 = st.columns(2)
    start_bel = c1.date_input("Data iniziale", dates_bel.min().date(), key="bel_start")
    end_bel = c2.date_input("Data finale", dates_bel.max().date(), key="bel_end")

    cols_bel = [
        c for c in table_1.columns
        if start_bel <= pd.to_datetime(c, errors="coerce").date() <= end_bel
    ]
else:
    cols_bel = list(table_1.columns)

if len(selected_bel) > 0 and len(cols_bel) > 0:
    plot_interactive(table_1[cols_bel], selected_bel, "BEL", select_rows=True)
else:
    st.warning("Nessun dato BEL disponibile per il periodo selezionato.")

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
selected_trend = st.multiselect("Seleziona le grandezze", rows, default=rows, key="trend_rows")

dates_trend = pd.to_datetime(df_trend.columns, errors="coerce").dropna()

if not dates_trend.empty:
    st.markdown("**Seleziona il periodo di riferimento**")
    c1, c2 = st.columns(2)
    start_trend = c1.date_input("Data iniziale", dates_trend.min().date(), key="trend_start")
    end_trend = c2.date_input("Data finale", dates_trend.max().date(), key="trend_end")

    cols_trend = [
        c for c in df_trend.columns
        if start_trend <= pd.to_datetime(c, errors="coerce").date() <= end_trend
    ]
else:
    cols_trend = list(df_trend.columns)

if len(selected_trend) > 0 and len(cols_trend) > 0:
    plot_interactive(df_trend[cols_trend], selected_trend, trend_type, select_rows=True)

# =====================================================
# GRAFICO 3 - ALM
# =====================================================
st.divider()
st.subheader("📌 Analisi ALM")

selected_alm = st.multiselect(
    "Seleziona le grandezze",
    df_alm.columns.tolist(),
    default=df_alm.columns.tolist()
)

dates_alm = df_alm.index.dropna()

st.markdown("**Seleziona il periodo di riferimento**")
c1, c2 = st.columns(2)
start_alm = c1.date_input("Data iniziale", dates_alm.min().date(), key="alm_start")
end_alm = c2.date_input("Data finale", dates_alm.max().date(), key="alm_end")

df_alm_f = df_alm.loc[start_alm:end_alm]

if len(selected_alm) > 0 and not df_alm_f.empty:
    last = df_alm_f.iloc[-1]

    duration_asset_current = last.get("Duration Assets", float("nan"))
    duration_asset_opt = last["Duration Liabilities"] * (1 - last["Surplus Asset %"])

    if st.button("Ottimizzazione Duration Asset"):
        st.info(
            f"Valore ottimale che annulla il mismatch all'ultimo mese di riferimento: "
            f"**{duration_asset_opt:.2f}** "
            f"(rispetto al dato attuale di **{duration_asset_current:.2f}**)"
        )

    plot_interactive(df_alm_f, selected_alm, "Duration Trend")


