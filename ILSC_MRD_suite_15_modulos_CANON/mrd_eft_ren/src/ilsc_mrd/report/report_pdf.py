
from typing import Dict, Any, List
import os
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
from reportlab.lib import colors

# robust font (no black/white boxes)
pdfmetrics.registerFont(TTFont("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))

styles = getSampleStyleSheet()
base = ParagraphStyle("Base", parent=styles["Normal"], fontName="DejaVuSans", fontSize=10.5, leading=14.2, spaceAfter=7)
h1 = ParagraphStyle("H1", parent=base, fontSize=16, leading=20, spaceAfter=10)
h2 = ParagraphStyle("H2", parent=base, fontSize=12.5, leading=16, spaceAfter=8, spaceBefore=6)
small = ParagraphStyle("Small", parent=base, fontSize=9.5, leading=12.2, spaceAfter=5)

def P(txt, style=base):
    return Paragraph(txt, style)

def write_pdf(path: str, result: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    doc = SimpleDocTemplate(path, pagesize=LETTER, leftMargin=0.9*inch, rightMargin=0.9*inch,
                            topMargin=0.9*inch, bottomMargin=0.9*inch)
    story = []
    story.append(Paragraph("ILSC MRD-1X (SK) — Run Report (ES/EN)", h1))
    story.append(P(f"<b>Case:</b> {result.get('case_id','')} &nbsp;&nbsp; <b>Verdict:</b> {result.get('verdict','')}"))
    story.append(P(f"<b>Timestamp:</b> {result.get('timestamp','')}"))
    story.append(P(f"<b>Input SHA256:</b> {result.get('input_sha256','')}", small))
    story.append(P(f"<b>Env:</b> {result.get('env',{})}", small))
    story.append(Spacer(1, 8))

    # Locks table
    rows = [["Lock", "PASS?", "Key metric / Métrica clave"]]
    for k, v in result.get("locks", {}).items():
        metric = ""
        if isinstance(v, dict):
            for mk in ["max_violation","min_value","min_eig","max_rel_error","trace_err"]:
                if mk in v:
                    metric = f"{mk}={v[mk]}"
                    break
        rows.append([k, str(bool(v.get("pass", False))) if isinstance(v, dict) else str(v), metric])
    tbl = Table(rows, colWidths=[2.3*inch, 0.7*inch, 3.6*inch])
    tbl.setStyle(TableStyle([
        ("FONT", (0,0), (-1,-1), "DejaVuSans", 9.5),
        ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
        ("GRID", (0,0), (-1,-1), 0.3, colors.grey),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    story.append(Paragraph("Locks / Candados", h2))
    story.append(tbl)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Diagnostics / Diagnóstico", h2))
    story.append(P(result.get("diagnostic","(none)")))

    doc.build(story)
