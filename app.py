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
file_name = "summary.xlsx"

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

    table_1 = prepare_table(tables[0])  # BEL
    table_2 = prepare_table(tables[1])  # Monetary Trend BEL
    table_3 = prepare_table(tables[2])  # % Trend BEL

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
# FUNZIONE PLOT PLOTLY
# =====================================================
def plot_interactive(
    df,
    selected,
    title,
    is_index_datetime=True,
    horizontal_line=None,
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

    if horizontal_line is not None:
        fig.add_hline(
            y=horizontal_line,
            line_dash="dash",
            line_color="red",
            annotation_text="Ottimale",
            annotation_position="top left"
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
# SELEZIONE GRAFICO
# =====================================================
grafico = st.selectbox(
    "📌 Seleziona il grafico",
    [
        "BEL",
        "Monetary Trend BEL",
        "% Trend BEL",
        "Duration Trend"
    ]
)

st.divider()

# =====================================================
# GRAFICI STREAMLIT
# =====================================================
if grafico == "BEL":
    rows = [r for r in BEL_ROWS if r in table_1.index]
    selected = st.multiselect("Seleziona le grandezze", rows, default=rows)

    if selected:
        plot_interactive(
            table_1,
            selected,
            "BEL",
            is_index_datetime=False,
            select_rows=True
        )

elif grafico == "Monetary Trend BEL":
    rows = [r for r in VAR_ROWS if r in table_2.index]
    selected = st.multiselect("Seleziona le grandezze", rows, default=rows)

    if selected:
        plot_interactive(
            table_2,
            selected,
            "Monetary Trend BEL",
            is_index_datetime=False,
            select_rows=True
        )

elif grafico == "% Trend BEL":
    rows = [r for r in VAR_ROWS if r in table_3.index]
    selected = st.multiselect("Seleziona le grandezze", rows, default=rows)

    if selected:
        plot_interactive(
            table_3,
            selected,
            "% Trend BEL",
            is_index_datetime=False,
            select_rows=True
        )

elif grafico == "Duration Trend":
    cols = st.multiselect(
        "Seleziona le grandezze",
        df_alm.columns.tolist(),
        default=df_alm.columns.tolist()
    )
    
    if cols:
        last_row = df_alm.iloc[-1]
        duration_liabilities = last_row["Duration Liabilities"]
        surplus_asset_pct = last_row["Surplus Asset %"]
        duration_asset_opt = duration_liabilities * (1 - surplus_asset_pct)

        duration_asset_current = last_row["Duration Asset"]
        if st.button("Ottimizzazione Duration Asset"):
            st.info(
                f"Valore ottimale che annulla il mismatch all'ultimo mese di riferimento: "
                f"**{duration_asset_opt:.2f}** (rispetto al dato attuale di **{duration_asset_current:.2f}**)")

    if cols:
        plot_interactive(
            df_alm,
            cols,
            "Duration Trend"
        )
