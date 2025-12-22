import pandas as pd
import matplotlib.pyplot as plt


file_name = "summary.xlsx"
sheet_name = "Analisi BEL Aggregate"
use_cols = "B:N"

bel_rows = [
    "BEL Undiscounted",
    "BEL Discounted",
    "BEL IR DOWN",
    "BEL IR UP"
]

var_rows = [
    "Var. BEL Undiscounted",
    "Var. BEL Discounted",
    "Var. BEL IR DOWN",
    "Var. BEL IR UP"
]


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

tables = split_tables(df_raw)


def prepare_table(df):
    df = df.copy().reset_index(drop=True)


    df.columns = df.iloc[1]
    df = df.iloc[2:]

    df = df.set_index(df.columns[0])

    df = df.apply(pd.to_numeric, errors="coerce")

    return df

table_1 = prepare_table(tables[0])  
table_2 = prepare_table(tables[1])  
table_3 = prepare_table(tables[2])  


def plot_table(df, rows, title):
    plt.figure(figsize=(10, 6))

    for r in rows:
        if r in df.index:
            plt.plot(df.columns, df.loc[r], marker="o", label=r)

    plt.title(title)
    plt.xlabel("Periodo")
    plt.ylabel("Valore")
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

plot_table(
    table_1,
    bel_rows,
    "BEL"
)

plot_table(
    table_2,
    var_rows,
    "Monetary Trend BEL"
)

plot_table(
    table_3,
    var_rows,
    "% Trend BEL"
)


sheet_name = "Analisi ALM"
use_cols = "A:E"


df = pd.read_excel(
    file_name,
    sheet_name=sheet_name,
    usecols=use_cols
)

df = df.dropna(how="all")

date_col = df.columns[0]
df = df.set_index(date_col)

df.index = pd.to_datetime(df.index, errors="coerce")

df = df.apply(pd.to_numeric, errors="coerce")

df = df[df.notna().any(axis=1)]


plt.figure(figsize=(12, 6))

plt.plot(df.index, df["Duration Asset"],
         linestyle=":", marker="o", label="Duration Asset")

plt.plot(df.index, df["Duration Liabilities"],
         linestyle=":", marker="o", label="Duration Liabilities")

plt.plot(df.index, df["Duration Mismatch"],
         linewidth=3, marker="o", label="Duration Mismatch")

plt.plot(df.index, df["Surplus Asset %"],
         linestyle="--", marker="o", label="Surplus Asset %")

plt.title("Duration Trend")
plt.xlabel("Data")
plt.ylabel("Valore")
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


plt.figure(figsize=(12, 5))

plt.plot(df.index, df["Duration Mismatch"],
         linewidth=3, marker="o")

plt.title("Duration Mismatch")
plt.xlabel("Data")
plt.ylabel("Duration")
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
