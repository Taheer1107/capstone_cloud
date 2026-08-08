def calculate_adequacy(
    total_bill,
    sum_insured,
    total_covered
):

    coverage_percent = (
        sum_insured / total_bill
    ) * 100


    gap = max(
        0,
        total_bill - sum_insured
    )


    if coverage_percent >= 80:
        status = "Adequate"

    elif coverage_percent >= 40:
        status = "Partially Adequate"

    else:
        status = "Insufficient"


    return {
        "percentage": coverage_percent,
        "gap": gap,
        "status": status,
        "total_covered": total_covered
    }