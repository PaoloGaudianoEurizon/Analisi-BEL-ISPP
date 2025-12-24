# =====================================================
# GRAFICO 1 - BEL
# =====================================================
st.subheader("📌 BEL")

rows = [r for r in BEL_ROWS if r in table_1.index]
selected = st.multiselect("Seleziona le grandezze", rows, default=rows)

dates = pd.to_datetime(table_1.columns, errors="coerce").dropna()

if not dates.empty:
    st.markdown("**Seleziona il periodo di riferimento**")

    start, end = st.date_input(
        "Intervallo date",
        value=(dates.min().date(), dates.max().date()),
        min_value=dates.min().date(),
        max_value=dates.max().date(),
        key="bel_date_range"
    )

    cols = [
        c for c in table_1.columns
        if start <= pd.to_datetime(c, errors="coerce").date() <= end
    ]
else:
    cols = list(table_1.columns)  # ← FIX REALE

if selected and cols:
    plot_interactive(table_1[cols], selected, "BEL", select_rows=True)
