from pathlib import Path
import pandas as pd

DATA_PATH = (
    Path(__file__)
    .resolve()
    .parents[2]
    / "datasets"
    / "medicine_generic_catalog.csv"
)

df = pd.read_csv(DATA_PATH)

# ----------------------------------
# SEARCH
# ----------------------------------

def search_medicines(search_text=""):

    if search_text == "":

        return (
            df[
                [
                    "medicine_id",
                    "generic_name",
                    "average_price"
                ]
            ]
            .head(30)
            .to_dict("records")
        )

    result = df[
        df["generic_name"].str.contains(
            search_text,
            case=False,
            na=False
        )
    ]

    return (
        result[
            [
                "medicine_id",
                "generic_name",
                "average_price"
            ]
        ]
        .head(30)
        .to_dict("records")
    )


# ----------------------------------
# LOOKUP USING ID
# ----------------------------------

def get_medicine(medicine_id):

    row = df[
        df["medicine_id"] == medicine_id
    ]

    if len(row) == 0:
        return None

    row = row.iloc[0]

    return {

        "medicine_id": row["medicine_id"],

        "generic_name": row["generic_name"],

        "unit_price": float(row["average_price"])

    }


# ----------------------------------
# CALCULATE TOTAL
# ----------------------------------

def calculate_total(items):

    """
    items =

    [
        {
            "medicine_id":"MED00025",
            "quantity":5
        }
    ]
    """

    detailed = []

    total = 0

    for item in items:

        med = get_medicine(
            item["medicine_id"]
        )

        if med is None:
            continue

        subtotal = (
            med["unit_price"]
            * item["quantity"]
        )

        detailed.append({

            "medicine_id": med["medicine_id"],

            "generic_name": med["generic_name"],

            "quantity": item["quantity"],

            "unit_price": med["unit_price"],

            "subtotal": subtotal

        })

        total += subtotal

    return {

        "items": detailed,

        "total": total

    }