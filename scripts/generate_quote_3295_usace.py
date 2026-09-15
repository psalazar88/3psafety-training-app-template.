#!/usr/bin/env python3
"""Generate 3P Safety Training quote #3295.

Annual inspection of a Liebherr 1300 330-ton mobile crane for the
U.S. Army Corps of Engineers, performed on site at Winfield Lock and Dam.
"""

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT = "quotes/3P_Safety_Quote_3295.pdf"

NAVY = colors.HexColor("#0B2340")
ORANGE = colors.HexColor("#E07A1F")
SLATE = colors.HexColor("#5B646F")
DARK = colors.HexColor("#222222")
BODY = colors.HexColor("#111111")
RULE = colors.HexColor("#D8DDE3")
BAND = colors.HexColor("#F2F4F6")
TAGLINE = colors.HexColor("#C9D4E0")

MARGIN = 0.75 * inch
CONTENT_W = letter[0] - (2 * MARGIN)
BAND_PAD = 18
BAND_W = CONTENT_W - (2 * BAND_PAD)
FOOTER_RULE_Y = 40          # from page bottom
# Frame adds 6pt of internal padding on top of the margin, so the usable
# bottom sits at BOTTOM_MARGIN + 6 -- keep it clear of the footer rule.
BOTTOM_MARGIN = 46

QUOTE_NO = "3295"
QUOTE_DATE = "September 15, 2026"
TOTAL = "$3,295.00"


def style(name, **kw):
    kw.setdefault("fontName", "Helvetica")
    kw.setdefault("fontSize", 9)
    kw.setdefault("leading", 11.8)
    kw.setdefault("textColor", DARK)
    return ParagraphStyle(name, **kw)


S = {
    "brand": style("brand", fontName="Helvetica-Bold", fontSize=18, leading=22,
                   textColor=colors.white),
    "quote_word": style("quote_word", fontName="Helvetica-Bold", fontSize=18,
                        leading=22, textColor=colors.white, alignment=TA_RIGHT),
    "quote_meta": style("quote_meta", fontName="Helvetica-Bold", fontSize=9,
                        leading=12, textColor=colors.white, alignment=TA_RIGHT),
    "tagline": style("tagline", textColor=TAGLINE),
    "section": style("section", fontName="Helvetica-Bold", fontSize=11,
                     leading=13, textColor=NAVY),
    "label": style("label", fontName="Helvetica-Bold", fontSize=9, leading=12,
                   textColor=SLATE),
    "party": style("party", fontSize=10.5, leading=14, textColor=BODY),
    "body": style("body"),
    "small": style("small", fontSize=8, leading=11, textColor=SLATE),
    "note": style("note", fontName="Helvetica-Oblique", fontSize=8.5,
                  leading=12, textColor=SLATE),
    "th": style("th", fontName="Helvetica-Bold", fontSize=8.5, leading=12,
                textColor=SLATE),
    "th_r": style("th_r", fontName="Helvetica-Bold", fontSize=8.5, leading=12,
                  textColor=SLATE, alignment=TA_RIGHT),
    "amount": style("amount", fontSize=9, leading=11.8, alignment=TA_RIGHT),
    "total_label": style("total_label", fontName="Helvetica-Bold", fontSize=11,
                         leading=13, textColor=NAVY, alignment=TA_RIGHT),
    "total_amt": style("total_amt", fontName="Helvetica-Bold", fontSize=11,
                       leading=13, textColor=ORANGE, alignment=TA_RIGHT),
    "sig": style("sig", fontSize=8.5, leading=12, textColor=SLATE),
    "tick": style("tick", fontSize=9, leading=11.8, textColor=NAVY),
    "footer": style("footer", fontName="Helvetica-Oblique", fontSize=8.5,
                    leading=12, textColor=SLATE),
}

FLUSH = [
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ("TOPPADDING", (0, 0), (-1, -1), 0),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
]


def header():
    """Navy masthead: brand on the left, quote metadata on the right."""
    meta = [
        Paragraph("QUOTE", S["quote_word"]),
        Spacer(1, 4),
        Paragraph(f"No. {QUOTE_NO}", S["quote_meta"]),
        Paragraph(f"Date: {QUOTE_DATE}", S["quote_meta"]),
        Paragraph("Valid for 30 days", S["quote_meta"]),
    ]
    top = Table(
        [[Paragraph("3P SAFETY TRAINING", S["brand"]), meta]],
        colWidths=[BAND_W * 0.55, BAND_W * 0.45],
    )
    top.setStyle(TableStyle(FLUSH + [("VALIGN", (0, 0), (0, 0), "MIDDLE")]))

    tag = Paragraph(
        "Workplace Safety Training, Crane Inspection &amp; OSHA Certification",
        S["tagline"],
    )
    band = Table([[top], [tag]], colWidths=[CONTENT_W])
    band.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), BAND_PAD),
        ("RIGHTPADDING", (0, 0), (-1, -1), BAND_PAD),
        ("TOPPADDING", (0, 0), (0, 0), 12),
        ("BOTTOMPADDING", (0, 0), (0, 0), 6),
        ("TOPPADDING", (0, 1), (0, 1), 0),
        ("BOTTOMPADDING", (0, 1), (0, 1), 8),
    ]))
    return band


def parties():
    frm = [
        Paragraph("FROM", S["label"]),
        Spacer(1, 6),
        Paragraph("3P Safety Training", S["party"]),
        Paragraph("Patrick Salazar, Owner", S["party"]),
        Paragraph("(252) 229-5238", S["party"]),
        Paragraph("patrick.salazar@3psafety.net", S["party"]),
    ]
    to = [
        Paragraph("PREPARED FOR", S["label"]),
        Spacer(1, 6),
        Paragraph("U.S. Army Corps of Engineers", S["party"]),
        Paragraph("Light Capacity Fleet", S["party"]),
        Paragraph("Attn: Travis Hill", S["party"]),
        Paragraph("1180 Cinder Rd", S["party"]),
        Paragraph("Old Hickory, TN 37138", S["party"]),
    ]
    t = Table([[frm, to]], colWidths=[CONTENT_W * 0.45, CONTENT_W * 0.55])
    t.setStyle(TableStyle(FLUSH))
    return t


def equipment():
    eq = [
        Paragraph("EQUIPMENT", S["label"]),
        Spacer(1, 6),
        Paragraph("Liebherr 1300 &#8212; 330-ton mobile crane", S["party"]),
    ]
    site = [
        Paragraph("INSPECTION SITE", S["label"]),
        Spacer(1, 6),
        Paragraph("Winfield Lock and Dam", S["party"]),
        Paragraph("170 Lock Rd", S["party"]),
        Paragraph("Red House, WV", S["party"]),
    ]
    t = Table([[eq, site]], colWidths=[CONTENT_W * 0.45, CONTENT_W * 0.55])
    t.setStyle(TableStyle(FLUSH))
    return t


def line_items():
    desc = [
        Paragraph(
            "<b>Annual (comprehensive) crane inspection</b> &#8212; Liebherr 1300, "
            "330-ton mobile crane",
            S["body"],
        ),
        Spacer(1, 3),
        Paragraph(
            "Performed on site at Winfield Lock and Dam, Red House, WV by an "
            "NCCCO-Certified Crane Inspector to OSHA 29 CFR 1926.1412(f) / "
            "1910.180(d) and ASME B30.5. <b>Annual inspection only &#8212; does "
            "not include a load test.</b>",
            S["small"],
        ),
    ]
    rows = [
        [Paragraph("DESCRIPTION", S["th"]), Paragraph("QTY", S["th_r"]),
         Paragraph("AMOUNT", S["th_r"])],
        [desc, Paragraph("1 crane", S["amount"]), Paragraph(TOTAL, S["amount"])],
    ]
    t = Table(rows, colWidths=[CONTENT_W - 150, 60, 90])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BAND),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, -1), 0.75, RULE),
    ]))
    return t


def total_row():
    t = Table(
        [[Paragraph("TOTAL (all travel included)", S["total_label"]),
          Paragraph(TOTAL, S["total_amt"])]],
        colWidths=[CONTENT_W - 90, 90],
    )
    t.setStyle(TableStyle(FLUSH + [
        ("RIGHTPADDING", (1, 0), (1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


INCLUDED = [
    "Annual/comprehensive inspection by an NCCCO-Certified Crane Inspector",
    "Structural, mechanical, hydraulic, and electrical systems; boom and outriggers",
    "Wire rope, hooks, sheaves, rigging hardware, limit and safety devices, load chart",
    "Written inspection report and dated inspection decal on completion",
    "All inspector travel, lodging, and per diem &#8212; no additional travel charges",
]

TERMS = [
    ("Scheduling:", "Inspection date to be confirmed upon acceptance of this quote, "
                    "subject to inspector availability."),
    ("Site requirements:", "The crane must be available with a qualified operator "
                           "on site for function checks."),
    ("Payment:", "Net 30 from submission of the inspection report. Government "
                 "purchase card or purchase order accepted."),
]


def bullets():
    rows = [[Paragraph("\u2022", S["tick"]), Paragraph(item, S["body"])]
            for item in INCLUDED]
    t = Table(rows, colWidths=[14, CONTENT_W - 14])
    t.setStyle(TableStyle(FLUSH + [("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


def terms():
    rows = [[Paragraph(f"<b>{k}</b> {v}", S["body"])] for k, v in TERMS]
    t = Table(rows, colWidths=[CONTENT_W])
    t.setStyle(TableStyle(FLUSH + [("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return t


def exclusions():
    """Called out on its own band so the scope limit cannot be missed."""
    t = Table([[Paragraph(
        "<b>NOT INCLUDED:</b> Annual (periodic) inspection only. A <b>load test is "
        "not included</b>, nor is NDT or repair of any deficiencies found "
        "&#8212; these can be quoted separately on request.",
        S["body"])]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BAND),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBEFORE", (0, 0), (0, -1), 2, ORANGE),
    ]))
    return t


def signature_block():
    line = "_______________________________"
    t = Table(
        [[Paragraph(line, S["body"]), "", Paragraph(line, S["body"])],
         [Paragraph("Authorized Signature &#8212; U.S. Army Corps of Engineers",
                    S["sig"]), "", Paragraph("Date", S["sig"])]],
        colWidths=[CONTENT_W * 0.5, CONTENT_W * 0.06, CONTENT_W * 0.44],
    )
    t.setStyle(TableStyle(FLUSH + [("TOPPADDING", (0, 1), (-1, 1), 4)]))
    return t


def footer(canvas, doc):
    """Drawn in the bottom margin, clear of the text frame."""
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.75)
    canvas.line(MARGIN, FOOTER_RULE_Y, MARGIN + CONTENT_W * 0.8, FOOTER_RULE_Y)
    canvas.setFont("Helvetica-Oblique", 8.5)
    canvas.setFillColor(SLATE)
    canvas.drawString(
        MARGIN, FOOTER_RULE_Y - 12,
        f"3P Safety Training  |  Quote #{QUOTE_NO}  |  Prepared by Patrick Salazar"
        "  |  patrick.salazar@3psafety.net",
    )
    canvas.restoreState()


def build():
    doc = SimpleDocTemplate(
        OUT, pagesize=letter,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=0.45 * inch, bottomMargin=BOTTOM_MARGIN,
        title=f"3P Safety Training Quote #{QUOTE_NO}",
        author="Patrick Salazar, 3P Safety Training",
        subject="Annual crane inspection - Liebherr 1300, 330-ton mobile crane",
    )

    story = [
        header(),
        Spacer(1, 12),
        parties(),
        Spacer(1, 10),
        equipment(),
        Spacer(1, 12),
        Paragraph("SCOPE OF WORK", S["section"]),
        Spacer(1, 5),
        line_items(),
        total_row(),
        Spacer(1, 12),
        KeepTogether([
            Paragraph("WHAT'S INCLUDED", S["section"]),
            Spacer(1, 5),
            bullets(),
            Spacer(1, 8),
            exclusions(),
        ]),
        Spacer(1, 8),
        KeepTogether([
            Paragraph("SCHEDULING &amp; TERMS", S["section"]),
            Spacer(1, 5),
            terms(),
        ]),
        Spacer(1, 4),
        KeepTogether([
            Paragraph("ACCEPTANCE", S["section"]),
            Spacer(1, 5),
            Paragraph(
                "To accept, sign below or reply to confirm and we will contact you "
                "to schedule the inspection date.",
                S["body"],
            ),
            Spacer(1, 8),
            signature_block(),
        ]),
    ]

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
