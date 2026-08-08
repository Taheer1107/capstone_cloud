import pandas as pd
from pathlib import Path

# ----------------------------------
# LOAD DATASET
# ----------------------------------

DATA_PATH = (
    Path(__file__)
    .resolve()
    .parents[2]
    / "datasets"
    / "diagnostics_clean_final.csv"
)

df = pd.read_csv(DATA_PATH)
df["procedure_name"] = df["procedure_name"].fillna("").astype(str)

# ----------------------------------
# SEARCH
# ----------------------------------

def search_diagnostics(search_text=""):

    if search_text == "":
        return (
            df[["procedure_name", "rate"]]
            .head(30)
            .to_dict("records")
        )

    result = df[
        df["procedure_name"]
        .str.contains(
            search_text,
            case=False,
            na=False
        )
    ]

    return (
        result[
            ["procedure_name", "rate"]
        ]
        .head(30)
        .to_dict("records")
    )

# ----------------------------------
# PRICE LOOKUP
# ----------------------------------

def get_price(procedure_name):

    row = df[
        df["procedure_name"] == procedure_name
    ]

    if len(row) == 0:
        return None

    return float(row.iloc[0]["rate"])

# ----------------------------------
# TOTAL
# ----------------------------------

def calculate_total(items):

    """
    items =

    [
        {
            "procedure_name":"MRI Brain",
            "quantity":2
        },

        {
            "procedure_name":"CBC",
            "quantity":1
        }
    ]
    """

    total = 0

    detailed = []

    for item in items:

        price = get_price(
            item["procedure_name"]
        )

        if price is None:
            continue

        qty = item["quantity"]

        subtotal = price * qty

        detailed.append({

            "procedure_name": item["procedure_name"],

            "quantity": qty,

            "unit_price": price,

            "subtotal": subtotal

        })

        total += subtotal

    return {

        "items": detailed,

        "total": total

    }