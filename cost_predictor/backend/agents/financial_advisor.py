class FinancialAdvisorAgent:
    def calculate_financial_risk(
        self,
        patient_pay,
        total_bill
    ):

        if total_bill <= 0:

            return {
                "risk_level": "Unknown",
                "liability_percentage": 0,
                "absolute_risk": "Unknown"
            }


        liability_percentage = (
            patient_pay / total_bill
        ) * 100


        # -----------------------------
        # Percentage based assessment
        # -----------------------------

        if liability_percentage <= 20:

            percentage_risk = "Low"

        elif liability_percentage <= 50:

            percentage_risk = "Medium"

        else:

            percentage_risk = "High"


        # -----------------------------
        # Absolute financial burden
        # -----------------------------

        if patient_pay <= 25000:

            absolute_risk = "Low"

        elif patient_pay <= 200000:

            absolute_risk = "Medium"

        else:

            absolute_risk = "High"



        # -----------------------------
        # Combined decision
        # -----------------------------
        


        # percentage gets higher importance
        # absolute amount only increases risk
        # when the amount is genuinely large

        if percentage_risk == "High":

            final_risk = "High"


        elif percentage_risk == "Medium":

            if absolute_risk == "High":
                final_risk = "High"
            else:
                final_risk = "Medium"


        else:

            if patient_pay >= 500000:
                final_risk = "Medium"
            else:
                final_risk = "Low"



        return {

        "risk_level": final_risk,

        "liability_percentage":
            round(liability_percentage,2),

        "coverage_percentage":
            round(100 - liability_percentage,2),

        "absolute_risk":
            absolute_risk,

        "percentage_risk":
            percentage_risk,

        "patient_pay":
            patient_pay

}
    def calculate_catastrophic_risk(
        self,
        patient_pay,
        city_tier
    ):

        income_reference = {

            "Tier-1": 600000,

            "Tier-2": 300000,

            "Tier-3": 180000

        }


        estimated_income = income_reference.get(
            city_tier,
            300000
        )


        threshold = estimated_income * 0.10


        # Ignore only very small payments
        # Avoid false alarms for small bills

        if patient_pay < 10000:

            return {

                "is_catastrophic": False,

                "reference_income": estimated_income,

                "income_impact_percentage": 0

            }


        impact_percentage = (
            patient_pay / estimated_income
        ) * 100



        return {

            "is_catastrophic":
                patient_pay > threshold,


            "reference_income":
                estimated_income,


            "income_impact_percentage":
                round(
                    impact_percentage,
                    2
                )

        }
    def get_scheme_action(
        self,
        scheme,
        risk_level
    ):

        scheme_actions = {


            ("Private Insurance", "High"):

            (
                "Your insurance coverage may not be sufficient "
                "for this treatment cost. Consider increasing "
                "your sum insured or adding a super top-up plan."
            ),


            ("Private Insurance", "Medium"):

            (
                "Your insurance reduced the financial burden. "
                "A super top-up plan may provide additional "
                "protection for future high-cost treatments."
            ),


            ("CGHS / State Government Scheme", "High"):

            (
                "Your government healthcare coverage may not "
                "fully cover this treatment cost. Review "
                "eligible hospitals, scheme limits and "
                "available benefits."
            ),


            ("CGHS / State Government Scheme", "Medium"):

            (
                "Your government scheme provides support, "
                "but some expenses may remain due to limits "
                "or exclusions."
            ),


            ("Military / ECHS", "High"):

            (
                "Your coverage gap may be due to package limits "
                "or hospital eligibility. Prefer ECHS approved "
                "facilities whenever possible."
            ),


            ("Self Pay", "High"):

            (
                "You are paying a significant amount without "
                "active coverage. Explore government healthcare "
                "schemes or financial assistance options."
            )

        }


        return scheme_actions.get(
            (scheme, risk_level),
            "Continue maintaining adequate healthcare coverage."
        )

    def generate_advice(
        self,
        predicted_cost,
        explanation,
        coverage,
        insurance_info,
        scheme=None
):


        advice = []


        patient_pay = coverage.get(
            "patient_pays",
            0
        )


        total_bill = predicted_cost


        risk = self.calculate_financial_risk(
            patient_pay,
            total_bill
        )

        city_tier = insurance_info.get(
            "city_tier",
            "Tier-2"
        )


        catastrophic = self.calculate_catastrophic_risk(
            patient_pay,
            city_tier
        )

        # =====================================
        # 1. Financial Risk Analysis
        # =====================================

        if total_bill > 0:

            coverage_percentage = (
                (total_bill - patient_pay)
                /
                total_bill
            ) * 100


            if risk["risk_level"] == "Low":

                advice.append({

                    "title":
                    "Strong Financial Protection",

                    "reason":
                    (
                        f"Your coverage handled most of the treatment cost. "
                        f"You only need to pay ₹{patient_pay:,.0f} "
                        f"({risk['liability_percentage']}%) of the total bill."
                    ),

                    "action":
                    "Continue maintaining adequate healthcare coverage.",

                    "priority":
                    "Low"

                })


            elif risk["risk_level"] == "High":

                advice.append({

                    "title":
                    "High Financial Risk",

                    "reason":
                    f"Approximately ₹{patient_pay:,.0f} remains payable after coverage.",

                    "action":
                    self.get_scheme_action(
                        scheme,
                        "High"
                    ),

                    "priority":
                    "High"

                })


            elif risk["risk_level"] == "Medium":

                advice.append({

                    "title":
                    "Moderate Financial Risk",

                    "reason":
                    "Your current coverage reduces the financial burden, but additional protection may be useful for future high-cost treatments.",

                    "action":
                    self.get_scheme_action(
                        scheme,
                        "Medium"
                    ),

                    "priority":
                    "Medium"

                })
        # =====================================
        # Catastrophic Expense Analysis
        # =====================================

        if catastrophic["is_catastrophic"]:

            advice.append({

                "title":
                "High Financial Burden Compared To Estimated Income",

                "reason":
                (
                    f"Based on your selected {city_tier} category, "
                    f"we assumed an annual household income of "
                    f"₹{catastrophic['reference_income']:,.0f}. "
                    f"Your expected payment of ₹{patient_pay:,.0f} "
                    f"represents a significant financial burden "
                    f"under this assumption."
                ),

                "action":
                (
                    "Consider additional financial protection "
                    "such as higher coverage limits or government schemes."
                ),

                "priority":
                "High"

            })

        # =====================================
        # 2. XAI Cost Analysis
        # =====================================


        if explanation:


            hospital = explanation.get(
                "Hospital Type",
                0
            )


            if hospital > 0 and risk["risk_level"] != "Low":


                advice.append({

                    "title":
                    "Hospital Cost Optimization",

                    "reason":
                    "The selected hospital category contributed to increased predicted treatment cost.",

                    "action":
                    "Compare hospitals with similar facilities and treatment quality.",

                    "priority":
                    "Medium"

                })



            city = explanation.get(
                "City Tier",
                0
            )


            if city > 0:


                advice.append({

                    "title":
                    "Location Cost Optimization",

                    "reason":
                    "Healthcare costs are influenced by the selected city tier.",

                    "action":
                    "If possible, compare treatment costs across nearby locations.",

                    "priority":
                    "Low"

                })



        # =====================================
        # 3. Insurance Review
        # =====================================


        provider = ""


        if insurance_info:

            provider = insurance_info.get(
                "provider",
                ""
            )


        if provider and risk["risk_level"] != "Low":

            if provider in ["SBI", "HDFC", "ICICI"]:

                action = (
                    f"Review your {provider} policy sum insured "
                    "and consider a super top-up for future high-cost treatments."
                )

            else:

                action = (
                    "Review your policy limits and available coverage options."
                )


            advice.append({

                "title":
                "Insurance Policy Review",

                "reason":
                f"Your {provider} policy was considered while calculating coverage.",

                "action":
                action,

                "priority":
                "Low"

            })



        # =====================================
        # Default
        # =====================================

        if not advice:


            advice.append({

                "title":
                "Financial Plan Looks Stable",

                "reason":
                "Your current coverage provides adequate protection for this treatment estimate.",

                "action":
                "Continue monitoring your insurance protection.",

                "priority":
                "Low"

            })


        return {

    "risk": risk,

    "catastrophic": catastrophic,

    "recommendations": advice

}