from io import BytesIO
from reportlab.platypus import Indenter
from reportlab.lib.styles import ParagraphStyle

from reportlab.lib import colors
from reportlab.lib import styles
from reportlab.lib import styles
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    KeepTogether,
)
def generate_admin_pdf(patient, coverage):
    """
    Creates the Admin Billing PDF.

    Returns:
        BytesIO buffer
    """

    buffer = BytesIO()

    doc = SimpleDocTemplate(
    buffer,
    pagesize=(8.5 * inch, 11 * inch),
    topMargin=0.45 * inch,
    bottomMargin=0.45 * inch,
    leftMargin=0.55 * inch,
    rightMargin=0.55 * inch,
)
    styles = getSampleStyleSheet()
    styles["Title"].fontSize = 20
    styles["Title"].leading = 22

    styles["Heading2"].fontSize = 15
    styles["Heading2"].leading = 18
    styles["Heading2"].leftIndent = 30
    
    story = []

    # =====================================================
    # TITLE
    # =====================================================

    title = Paragraph(
        "<b>Patient Bill</b>",
        styles["Title"]
    )
    scheme_style = ParagraphStyle(
        "SchemeStyle",
        parent=styles["Normal"],          # <-- use Normal instead of Heading3
        fontName="Helvetica-Bold",        # <-- upright bold font
        leftIndent=42,                    # <-- same as Heading2
        spaceBefore=10,
        spaceAfter=8,
        textColor=colors.black,
    )
    story.append(title)
    story.append(Spacer(1, 0.08 * inch))

    # =====================================================
    # PATIENT INFORMATION
    # =====================================================

    story.append(
        Paragraph("<b>Patient Information</b>", styles["Heading2"])
    )

    story.append(Spacer(1, 0.15 * inch))

    patient_table = Table(
        [
            ["Patient ID", patient["hospital_id"]],
            ["Patient Name", patient["name"]],
            ["Age", str(patient["age"])],
            ["Gender", patient["gender"]],
            ["Admission Date", patient["admission_date"]],
            ["Discharge Date", patient["exit_date"]],
        ],
        colWidths=[2.2 * inch, 4.2 * inch],
    )

    patient_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E5E7EB")),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
        ])
    )

    story.append(
    KeepTogether([
        patient_table,
        Spacer(1, 0.30 * inch)
    ])
)
    # =====================================================
    # GROSS BILL BREAKDOWN
    # =====================================================

    story.append(
        Paragraph("<b>Gross Bill Breakdown</b>", styles["Heading2"])
    )

    story.append(Spacer(1, 0.15 * inch))

    gross = coverage["gross_bill"]

    bill_table = Table(
        [
            ["Procedure", f"Rs. {gross['procedure']:,.0f}"],
            ["Diagnostics", f"Rs. {gross['diagnostics']:,.0f}"],
            ["Medicines", f"Rs. {gross['medicines']:,.0f}"],
            ["Consumables", f"Rs. {gross['consumables']:,.0f}"],
            ["Room Charges", f"Rs. {gross['room_charges']:,.0f}"],
            ["Doctor Charges", f"Rs. {gross['doctor_charges']:,.0f}"],
            ["Gross Total", f"Rs. {gross['total']:,.0f}"],
        ],
        colWidths=[4.2 * inch, 2.2 * inch],
    )

    bill_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -2), colors.HexColor("#F3F4F6")),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#DCEAFE")),
            ("FONTNAME", (0, 0), (-1, -2), "Helvetica"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
        ])
    )

    story.append(
    KeepTogether([
        bill_table,
        Spacer(1, 0.30 * inch)
    ])
)
    # =====================================================
    # COVERAGE SUMMARY
    # =====================================================

    story.append(
        Paragraph("<b>Coverage Summary</b>", styles["Heading2"])
    )

    story.append(Spacer(1, 0.15 * inch))

    waterfall = coverage["waterfall"]

    if len(waterfall) == 0:

        no_coverage_style = ParagraphStyle(
            "NoCoverage",
            parent=styles["Normal"],
            leftIndent=30,
            fontSize=12,
        )

        story.append(
            Paragraph(
                "No healthcare coverage has been applied.",
                no_coverage_style
            )
        )

    else:

        for i, item in enumerate(waterfall, start=1):

            coverage_table = Table(
                [
                    ["Eligible Amount", f"Rs. {item['eligible']:,.0f}"],
                    ["Covered Amount", f"Rs. {item['covered']:,.0f}"],
                    ["Remaining Bill", f"Rs. {item['remaining']:,.0f}"],
                ],
                colWidths=[3.5 * inch, 2.5 * inch],
            )

            coverage_table.setStyle(
                TableStyle([
                    ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
                    ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#F3F4F6")),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 8),
                    ("TOPPADDING", (0,0), (-1,-1), 8),
                    ("ALIGN", (1,0), (1,-1), "RIGHT"),
                    ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
                    ("FONTSIZE", (0,0), (-1,-1), 11),
                ])
            )

            story.append(
                KeepTogether([
                    Paragraph(
                        f"<b>{i}. {item['scheme']}</b>",
                        scheme_style
                    ),
                    coverage_table,
                    Spacer(1, 0.20 * inch)
                ])
            )
    # =====================================================
    # FINAL BILL SUMMARY
    # =====================================================

    summary_table = Table(
        [
            ["Gross Hospital Bill", f"Rs. {coverage['gross_bill']['total']:,.0f}"],
            ["Total Covered", f"Rs. {coverage['covered_amount']:,.0f}"],
            ["Patient Pays", f"Rs. {coverage['patient_pays']:,.0f}"],
        ],
        colWidths=[4.2 * inch, 2.2 * inch],
    )

    summary_table.setStyle(
        TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("BACKGROUND", (0,0), (0,-2), colors.HexColor("#F3F4F6")),
            ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#DCEAFE")),
            ("FONTNAME", (0,0), (-1,-2), "Helvetica"),
            ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
            ("ALIGN", (1,0), (1,-1), "RIGHT"),
            ("BOTTOMPADDING", (0,0), (-1,-1), 10),
            ("TOPPADDING", (0,0), (-1,-1), 10),
            ("FONTSIZE", (0,0), (-1,-1), 12),
        ])
    )

    story.append(
        KeepTogether([
            Paragraph(
                "<b>Final Billing Summary</b>",
                styles["Heading2"]
            ),
            Spacer(1, 0.15 * inch),
            summary_table
        ])
    )
    # Build PDF
    doc.build(story)

    buffer.seek(0)

    return buffer
