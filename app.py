import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt

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

# =====================================================
# FILE
# =====================================================
file_name = "Summary.xlsx"

# =====================================================
# FUNZIONI DI CARICAMENTO
# =====================================================
@st.cache_data
def load_bel_tables():
    sheet_name = "Analisi BEL Aggregate"
    use_cols = "B:N"

    df_raw = pd.read_excel(
        file_name,
        sheet_name=sheet_name,
        usecols=use_cols,
        header=None
    )

    def split_tables(df):
        tables = []
        start = None
        for i in range(len(df)):
            if not df.iloc[i].isna().all():
                if start is None:
                    start = i
            else:
                if start is not None:
                    tables.append(df.iloc[start:i])
                    start = None
        if start is not None:
            tables.append(df.iloc[start:])
        return tables

    def prepare_table(df):
        df = df.copy().reset_index(drop=True)
        df.columns = df.iloc[1]
        df = df.iloc[2:]
        df = df.set_index(df.columns[0])
        df = df.apply(pd.to_numeric, errors="coerce")
        return df

    tables = split_tables(df_raw)

    table_1 = prepare_table(tables[0])
    table_2 = prepare_table(tables[1])
    table_3 = prepare_table(tables[2])

    return table_1, table_2, table_3


@st.cache_data
def load_alm():
    sheet_name = "Analisi ALM"
    use_cols = "A:E"

    df = pd.read_excel(
        file_name,
        sheet_name=sheet_name,
        usecols=use_cols
    )

    df = df.dropna(how="all")
    df = df.set_index(df.columns[0])
    df.index = pd.to_datetime(df.index, errors="coerce")
    df = df.apply(pd.to_numeric, errors="coerce")
    df = df[df.notna().any(axis=1)]

    return df

# =====================================================
# FUNZIONE PLOT
# =====================================================
def plot_interactive(
    df,
    selected,
    title,
    is_index_datetime=True,
    select_rows=False
):
    if select_rows:
        df_plot = df.loc[selected].T.copy()
    else:
        df_plot = df[selected].copy()

    if is_index_datetime:
        df_plot["Data"] = df_plot.index.strftime('%d %B %Y')
    else:
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

    fig.update_layout(
        xaxis_title="Data",
        yaxis_title="Valore",
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# LOAD DATA
# =====================================================
table_1, table_2, table_3 = load_bel_tables()
df_alm = load_alm()

# =====================================================
# SEZIONE 1 - ANALISI BEL
# =====================================================
st.subheader("📌 Analisi BEL")

grafico_bel = st.selectbox(
    "Seleziona il grafico BEL",
    ["BEL", "Monetary Trend BEL", "% Trend BEL"]
)

st.divider()

if grafico_bel == "BEL":
    df_ref = table_1
    rows = [r for r in BEL_ROWS if r in df_ref.index]

elif grafico_bel == "Monetary Trend BEL":
    df_ref = table_2
    rows = [r for r in VAR_ROWS if r in df_ref.index]

else:
    df_ref = table_3
    rows = [r for r in VAR_ROWS if r in df_ref.index]

selected = st.multiselect("Seleziona le grandezze", rows, default=rows)

# ---- FILTRO PERIODO (asse X)
date_index = pd.to_datetime(df_ref.columns, errors="coerce")
date_index = date_index.dropna()

min_date, max_date = date_index.min(), date_index.max()

st.markdown("**Seleziona il periodo di riferimento**")
col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input("Data iniziale", min_date)

with col2:
    end_date = st.date_input("Data finale", max_date)

if selected:
    cols_filtered = [
        c for c in df_ref.columns
        if pd.to_datetime(c, errors="coerce") >= pd.to_datetime(start_date)
        and pd.to_datetime(c, errors="coerce") <= pd.to_datetime(end_date)
    ]

    plot_interactive(
        df_ref[cols_filtered],
        selected,
        grafico_bel,
        is_index_datetime=False,
        select_rows=True
    )

# =====================================================
# SEZIONE 2 - ANALISI ALM
# =====================================================
st.divider()
st.subheader("📌 Analisi ALM – Duration Trend")

cols = st.multiselect(
    "Seleziona le grandezze",
    df_alm.columns.tolist(),
    default=df_alm.columns.tolist()
)

# ---- FILTRO PERIODO (asse X)
min_date_alm, max_date_alm = df_alm.index.min(), df_alm.index.max()

st.markdown("**Seleziona il periodo di riferimento**")
col1, col2 = st.columns(2)

with col1:
    start_date_alm = st.date_input("Data iniziale", min_date_alm, key="alm_start")

with col2:
    end_date_alm = st.date_input("Data finale", max_date_alm, key="alm_end")

df_alm_filtered = df_alm.loc[start_date_alm:end_date_alm]

if cols:
    last_row = df_alm_filtered.iloc[-1]
    duration_liabilities = last_row["Duration Liabilities"]
    surplus_asset_pct = last_row["Surplus Asset %"]
    duration_asset_opt = duration_liabilities * (1 - surplus_asset_pct)
    duration_asset_current = last_row["Duration Asset"]

    if st.button("Ottimizzazione Duration Asset"):
        st.info(
            f"Valore ottimale che annulla il mismatch all'ultimo mese di riferimento: "
            f"**{duration_asset_opt:.2f}** "
            f"(rispetto al dato attuale di **{duration_asset_current:.2f}**)"
        )

    plot_interactive(
        df_alm_filtered,
        cols,
        "Duration Trend"
    )
