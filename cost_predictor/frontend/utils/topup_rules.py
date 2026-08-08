def get_valid_topups(primary):

    rules = {

        "Private Insurance": [
            "CGHS / State Government Scheme",
            "Military / ECHS"
        ],

        "Government Healthcare": [
            "Private Insurance"
        ],

        "CGHS / State Government Scheme": [
            "Private Insurance"
        ],

        "Military / ECHS": [
            "Private Insurance"
        ],

        "Self Pay": []

    }

    return rules.get(primary, [])