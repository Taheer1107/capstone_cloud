import pandas as pd
from pathlib import Path

# ----------------------------------
# LOAD CONSUMABLE CATALOG
# ----------------------------------

DATA_PATH = (
    Path(__file__)
    .resolve()
    .parents[2]
    / "datasets"
    / "consumable_catalog.csv"
)

df = pd.read_csv(DATA_PATH)

# ----------------------------------
# SEARCH
# ----------------------------------

def search_consumables(search_text=""):

    if search_text == "":

        return (
            df[
                [
                    "consumable_id",
                    "item_name",
                    "unit_price"
                ]
            ]
            .head(30)
            .to_dict("records")
        )

    result = df[
        df["item_name"].str.contains(
            search_text,
            case=False,
            na=False
        )
    ]

    return (
        result[
            [
                "consumable_id",
                "item_name",
                "unit_price"
            ]
        ]
        .head(30)
        .to_dict("records")
    )


# ----------------------------------
# LOOKUP USING ID
# ----------------------------------

def get_consumable(consumable_id):

    row = df[
        df["consumable_id"] == consumable_id
    ]

    if len(row) == 0:
        return None

    row = row.iloc[0]

    return {

        "consumable_id": row["consumable_id"],

        "item_name": row["item_name"],

        "unit_price": float(row["unit_price"])

    }


# ----------------------------------
# CALCULATE TOTAL
# ----------------------------------

def calculate_total(items):

    """
    items =

    [
        {
            "consumable_id":"CON00015",
            "quantity":5
        }
    ]
    """

    detailed = []

    total = 0

    for item in items:

        consumable = get_consumable(
            item["consumable_id"]
        )

        if consumable is None:
            continue

        subtotal = (
            consumable["unit_price"]
            * item["quantity"]
        )

        detailed.append({

            "consumable_id": consumable["consumable_id"],

            "item_name": consumable["item_name"],

            "quantity": item["quantity"],

            "unit_price": consumable["unit_price"],

            "subtotal": subtotal

        })

        total += subtotal

    return {

        "items": detailed,

        "total": total

    }