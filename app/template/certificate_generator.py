
from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

APP_DIR = Path(__file__).resolve().parent.parent
FONT_DIR = APP_DIR / "assets" / "fonts"
pdfmetrics.registerFont(
    TTFont("CertificateTitle", str(FONT_DIR / "Cinzel-VariableFont_wght.ttf"))
)

pdfmetrics.registerFont(
    TTFont("RecipientScript", str(FONT_DIR / "Allura-Regular.ttf"))
)

pdfmetrics.registerFont(
    TTFont("CertificateBody", str(FONT_DIR / "Montserrat-VariableFont_wght.ttf"))
)

pdfmetrics.registerFont(
    TTFont("CertificateBodyItalic", str(FONT_DIR / "Montserrat-Italic-VariableFont_wght.ttf"))
)

# A4 landscape: 842 x 595 points approximately
PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)

BLACK = HexColor("#242424")
DARK_BLACK = HexColor("#171717")
GOLD = HexColor("#D9A62E")
LIGHT_GOLD = HexColor("#F4D47A")
PALE_GOLD = HexColor("#FFF1C7")
CREAM = HexColor("#F8F5EF")
WHITE = HexColor("#FFFFFF")
GRAY = HexColor("#454545")


def polygon(pdf, points, fill, stroke=None, line_width=1):
    path = pdf.beginPath()
    path.moveTo(*points[0])

    for point in points[1:]:
        path.lineTo(*point)

    path.close()
    pdf.setFillColor(fill)

    if stroke:
        pdf.setStrokeColor(stroke)
        pdf.setLineWidth(line_width)
        pdf.drawPath(path, fill=1, stroke=1)
    else:
        pdf.drawPath(path, fill=1, stroke=0)


def bezier_shape(pdf, start, curves, fill, stroke=None, line_width=1):
    """Draw a closed shape using cubic Bezier curves."""
    path = pdf.beginPath()
    path.moveTo(*start)

    for control1, control2, end in curves:
        path.curveTo(
            control1[0], control1[1],
            control2[0], control2[1],
            end[0], end[1],
        )

    path.close()
    pdf.setFillColor(fill)

    if stroke:
        pdf.setStrokeColor(stroke)
        pdf.setLineWidth(line_width)
        pdf.drawPath(path, fill=1, stroke=1)
    else:
        pdf.drawPath(path, fill=1, stroke=0)


def draw_corner_design(pdf, width, height):
    """Draw black-and-gold geometric corner decorations."""

    # Top-left layered corner ribbons
    polygon(pdf, [
        (0, height), (190, height), (130, height - 62),
        (60, height - 132), (0, height - 190)
    ], BLACK)

    polygon(pdf, [
        (0, height - 18), (162, height - 18),
        (105, height - 75), (52, height - 128),
        (0, height - 180)
    ], GOLD)

    polygon(pdf, [
        (0, height - 30), (145, height - 30),
        (92, height - 83), (46, height - 129),
        (0, height - 175)
    ], DARK_BLACK)

    # Fine gold diagonal line
    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(1.5)
    pdf.line(25, height - 5, 145, height - 125)

    # Top-left nested diamond
    polygon(pdf, [
        (22, height), (190, height),
        (104, height - 88)
    ], DARK_BLACK, GOLD, 1)

    polygon(pdf, [
        (49, height - 2), (164, height - 2),
        (105, height - 61)
    ], BLACK, GOLD, 1)

    # Bottom-right layered corner ribbons
    polygon(pdf, [
        (width, 0), (width - 190, 0),
        (width - 130, 62), (width - 60, 132),
        (width, 190)
    ], BLACK)

    polygon(pdf, [
        (width, 18), (width - 162, 18),
        (width - 105, 75), (width - 52, 128),
        (width, 180)
    ], GOLD)

    polygon(pdf, [
        (width, 30), (width - 145, 30),
        (width - 92, 83), (width - 46, 129),
        (width, 175)
    ], DARK_BLACK)

    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(1.5)
    pdf.line(width - 25, 5, width - 145, 125)

    # Decorative gold ribbons at top-right
    bezier_shape(
        pdf,
        (width * 0.66, height),
        [
            ((width * 0.77, height - 25),
             (width * 0.84, height - 8),
             (width, height - 75)),
            ((width, height - 45),
             (width * 0.85, height + 2),
             (width * 0.66, height)),
        ],
        GOLD,
    )

    bezier_shape(
        pdf,
        (width * 0.72, height),
        [
            ((width * 0.84, height - 35),
             (width * 0.92, height - 15),
             (width, height - 55)),
            ((width, height - 35),
             (width * 0.86, height + 5),
             (width * 0.72, height)),
        ],
        DARK_BLACK,
    )

    # Decorative ribbon along bottom-left
    bezier_shape(
        pdf,
        (0, 58),
        [
            ((50, 15), (100, -5), (150, 8)),
            ((205, 17), (230, 0), (285, 0)),
            ((220, 28), (160, 35), (105, 26)),
            ((55, 20), (30, 40), (0, 40)),
        ],
        GOLD,
    )

    bezier_shape(
        pdf,
        (0, 28),
        [
            ((55, -2), (100, 2), (150, 0)),
            ((200, 2), (245, 0), (285, 0)),
            ((225, 15), (170, 20), (110, 15)),
            ((55, 8), (30, 22), (0, 15)),
        ],
        DARK_BLACK,
    )


def draw_medal(pdf, x, y):
    """Draw a gold medal using circles, rays, and ribbon polygons."""

    # Ribbon tails
    polygon(pdf, [
        (x - 20, y - 17), (x - 10, y - 48),
        (x, y - 35), (x + 8, y - 51),
        (x + 20, y - 17)
    ], GOLD)

    polygon(pdf, [
        (x - 13, y - 19), (x - 9, y - 38),
        (x, y - 29), (x + 10, y - 40),
        (x + 14, y - 19)
    ], LIGHT_GOLD)

    # Medal rays
    import math

    pdf.setFillColor(GOLD)

    for i in range(24):
        angle = math.radians(i * 15)
        inner = 20
        outer = 27

        p1 = (
            x + inner * math.cos(angle - 0.08),
            y + inner * math.sin(angle - 0.08),
        )
        p2 = (
            x + outer * math.cos(angle),
            y + outer * math.sin(angle),
        )
        p3 = (
            x + inner * math.cos(angle + 0.08),
            y + inner * math.sin(angle + 0.08),
        )
        polygon(pdf, [p1, p2, p3], GOLD)

    # Medal rings
    pdf.setFillColor(GOLD)
    pdf.circle(x, y, 21, fill=1, stroke=0)

    pdf.setFillColor(LIGHT_GOLD)
    pdf.circle(x, y, 16, fill=1, stroke=0)

    pdf.setStrokeColor(HexColor("#B9891B"))
    pdf.setLineWidth(1)
    pdf.circle(x, y, 12, fill=0, stroke=1)

    pdf.setFillColor(HexColor("#C79724"))
    pdf.circle(x, y, 5, fill=1, stroke=0)


def draw_centered_text(
    pdf, text, x, y, font, font_size, color,
    max_width=None, min_size=9
):
    """Draw centered text and reduce font size when needed."""
    text = str(text)
    size = font_size

    if max_width:
        while (
            stringWidth(text, font, size) > max_width
            and size > min_size
        ):
            size -= 1

    pdf.setFillColor(color)
    pdf.setFont(font, size)
    pdf.drawCentredString(x, y, text)


def draw_certificate_template(pdf, job, certificate):
    """Draw the complete certificate using vector shapes and text."""

    width, height = PAGE_WIDTH, PAGE_HEIGHT
    center = width / 2
    recipient_name = str(certificate.recipient_name)
    event_name = str(job.event_name)
    issuer_name = str(getattr(job, "issuer", "Larana Company"))
    organizer_name = str(getattr(job, "organizer_name", issuer_name))
    signatory_name = str(getattr(job, "signatory_name", "ROSA MARIA AGUADO"))
    signatory_role = str(getattr(job, "signatory_role", "CEO"))
    issue_date = job.event_date.strftime("%d %B %Y")

    pdf.setFillColor(CREAM)
    pdf.rect(0, 0, width, height, fill=1, stroke=0)

    bezier_shape(
        pdf,
        (0, 72),
        [
            ((160, 15), (260, 40), (420, 24)),
            ((560, 14), (700, 92), (width, 150)),
            ((width, 90), (width, 40), (width, 0)),
            ((560, 0), (250, 0), (0, 0)),
        ],
        HexColor("#EEEAE5"),
    )

    draw_corner_design(pdf, width, height)

    pdf.setStrokeColor(HexColor("#C7C0B7"))
    pdf.setLineWidth(0.8)
    pdf.rect(7, 7, width - 14, height - 14, fill=0, stroke=1)

    draw_medal(pdf, width - 110, height - 110)

    draw_centered_text(
        pdf,
        "CERTIFICATE",
        center,
        height - 112,
        "CertificateTitle",
        30,
        DARK_BLACK,
        max_width=width * 0.55,
        min_size=18,
    )

    draw_centered_text(
        pdf,
        f"OF {str(job.certificate_title).upper()}",
        center,
        height - 146,
        "Helvetica-Bold",
        15,
        DARK_BLACK,
        max_width=width * 0.4,
    )

    draw_centered_text(
        pdf,
        "This certificate is proudly presented to",
        center,
        height - 186,
        "Helvetica-Bold",
        12,
        DARK_BLACK,
    )

    draw_centered_text(
        pdf,
        recipient_name,
        center,
        height - 235,
        "RecipientScript",
        32,
        HexColor("#C59728"),
        max_width=width * 0.62,
        min_size=18,
    )

    description_top = height - 283
    description_text = (
        f"For participating in the {event_name} "
        f"held by {organizer_name} on {issue_date}"
    )
    draw_centered_text(
        pdf,
        description_text,
        center,
        description_top,
        "Helvetica-Bold",
        10.5,
        DARK_BLACK,
        max_width=width * 0.66,
        min_size=8,
    )

    signature_y = 135
    signature_x = center

    pdf.setStrokeColor(HexColor("#6F6F6F"))
    pdf.setLineWidth(0.8)
    pdf.line(center - 105, signature_y, center + 105, signature_y)

    draw_centered_text(
        pdf,
        signatory_name,
        signature_x,
        signature_y - 22,
        "RecipientScript",
        24,
        DARK_BLACK,
        max_width=220,
        min_size=14,
    )

    draw_centered_text(
        pdf,
        signatory_name.upper(),
        center,
        signature_y - 48,
        "CertificateBody",
        11,
        DARK_BLACK,
        max_width=240,
    )

    draw_centered_text(
        pdf,
        f"{signatory_role} of {organizer_name}",
        center,
        signature_y - 62,
        "CertificateBody",
        9,
        GRAY,
        max_width=240,
    )

    pdf.showPage()
