#!/usr/bin/env python3
"""Build and integrate the OCC v1.4.0 nuclear addendum PDF.

This script creates a canonical addendum page set and appends/replaces it in
the principal compendium PDF.
"""

from __future__ import annotations

import logging
from pathlib import Path
from tempfile import NamedTemporaryFile

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]
MAIN_PDF = ROOT / "docs" / "OCC_Compendio_Canonico_Completo.pdf"
ADDENDUM_PDF = ROOT / "docs" / "canonical" / "OCC_Addendum_Nuclear_v1.4.0.pdf"
MARKER = "NUCLEAR-LOCK-PACKAGE-V1.4.0"
LEGACY_MARKERS = [
    "NUCLEAR-LOCK-PACKAGE-V1.2.0",
]

# Existing canonical PDF can contain legacy metadata entries that trigger
# non-fatal parser warnings in pypdf; keep script output clean.
logging.getLogger("pypdf").setLevel(logging.ERROR)


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleNuclear",
            parent=base["Title"],
            fontSize=16,
            leading=20,
            spaceAfter=10,
        ),
        "h1": ParagraphStyle(
            "H1Nuclear",
            parent=base["Heading1"],
            fontSize=12,
            leading=15,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "BodyNuclear",
            parent=base["BodyText"],
            fontSize=10,
            leading=14,
            spaceAfter=6,
        ),
        "mono": ParagraphStyle(
            "MonoNuclear",
            parent=base["Code"],
            fontSize=9,
            leading=12,
            spaceAfter=5,
        ),
    }


def build_addendum_pdf(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        topMargin=2.2 * cm,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        bottomMargin=2.0 * cm,
    )
    st = _styles()
    story = []

    story.append(
        Paragraph(
            "OCC Canonical Addendum — Nuclear Domain Expansion (v1.4.0)",
            st["title"],
        )
    )
    story.append(
        Paragraph(
            f"Marker: <b>{MARKER}</b><br/>Date: 2026-02-16<br/>"
            "Scope: Formal integration of the numbered nuclear judge/locks (J4, L4C/L4E), "
            "MRD module, prediction anchor, and batch Experiment Lab alignment.",
            st["body"],
        )
    )

    story.append(Paragraph("1. Canonical alignment and numbering", st["h1"]))
    story.append(
        Paragraph(
            "Foundational judges remain J0–J3 (ISAAC/PA/IO/RFS), as defined in Documento A+. "
            "This addendum introduces the operational nuclear frontend judge <b>J4</b>, with "
            "numbered lock families <b>L4C*</b> (consistency/evaluability) and <b>L4E*</b> "
            "(evidence anchor/provenance).",
            st["body"],
        )
    )

    story.append(Paragraph("2. Lock classes and equations", st["h1"]))
    story.append(
        Paragraph(
            "<b>Class C (consistency / evaluability in Ω_I):</b> "
            "declare energy window, isotope set, reaction channel, and detector set. "
            "Missing declarations imply NO-EVAL(L4C*). "
            "Malformed numerical declarations imply FAIL(L4C*).",
            st["body"],
        )
    )
    story.append(Paragraph("Eq. (1): 0 <= E_min < E_max   (MeV)", st["mono"]))
    story.append(
        Paragraph(
            "<b>Class E (evidence anchor):</b> compare model prediction "
            "against declared observable anchor with uncertainty and source provenance "
            "(dataset reference + URL/DOI locator). Missing anchors imply NO-EVAL(L4E*).",
            st["body"],
        )
    )
    story.append(Paragraph("Eq. (2): z = |sigma_pred - sigma_obs| / sigma_obs_err", st["mono"]))
    story.append(Paragraph("PASS(E) iff z <= z_max; FAIL(L4E5) iff z > z_max.", st["mono"]))
    story.append(
        Paragraph(
            "Lock map: L4C1..L4C7 (domain declarations) and L4E1..L4E7 "
            "(evidence/provenance anchor).",
            st["body"],
        )
    )

    story.append(Paragraph("3. Operational semantics of violations", st["h1"]))
    story.append(
        Paragraph(
            "- NO-EVAL: claim is not operationally compilable "
            "(missing domain/evidence declarations).<br/>"
            "- FAIL: claim is compilable but inconsistent with declared "
            "consistency/evidence locks.<br/>"
            "- PASS: claim satisfies J4 lock set inside Ω_I, with explicit witness values.",
            st["body"],
        )
    )

    story.append(Paragraph("4. MRD implementation and reproducibility", st["h1"]))
    story.append(
        Paragraph(
            "Extension module: <b>ILSC_MRD_suite_extensions/mrd_nuclear_guard</b><br/>"
            "Cases: PASS(J4), NO-EVAL(L4C6), FAIL(L4E5)<br/>"
            "Prediction anchor extension: registry entry P-0004.<br/>"
            "Batch matrix workflow: `occ lab run --claims-dir ... --profiles core nuclear`.",
            st["body"],
        )
    )
    story.append(
        Paragraph(
            "CLI judge profile:<br/>"
            "occ judge examples/claim_specs/nuclear_pass.yaml --profile nuclear",
            st["mono"],
        )
    )
    story.append(
        Paragraph(
            "MRD execution:<br/>"
            "occ verify --suite extensions --strict --timeout 60",
            st["mono"],
        )
    )

    story.append(PageBreak())
    story.append(Paragraph("Anexo ES — Integración nuclear formal (v1.4.0)", st["h1"]))
    story.append(
        Paragraph(
            "Este anexo integra el juez nuclear numerado J4 y su paquete de candados "
            "L4C*/L4E* compatible con la arquitectura OCC. "
            "La jerarquía canónica se conserva: J0-J3 siguen como jueces fundacionales.",
            st["body"],
        )
    )
    story.append(
        Paragraph(
            "Clase C (consistencia): energía, isótopos, canal de reacción, detectores.<br/>"
            "Clase E (evidencia): anclaje observable con incertidumbre, contraste z-score y "
            "metadatos de procedencia (referencia + URL/DOI).",
            st["body"],
        )
    )
    story.append(Paragraph("z = |sigma_pred - sigma_obs| / sigma_obs_err <= z_max", st["mono"]))
    story.append(
        Paragraph(
            "Si faltan anclajes: NO-EVAL(L4E*). "
            "Si hay contradicción cuantitativa: FAIL(L4E5).",
            st["body"],
        )
    )

    story.append(Spacer(1, 12))
    story.append(
        Paragraph(
            "Files covered: occ/judges/nuclear_guard.py, "
            "ILSC_MRD_suite_extensions/mrd_nuclear_guard/, "
            "examples/claim_specs/nuclear_*.yaml, predictions/registry.yaml (P-0004).",
            st["body"],
        )
    )
    doc.build(story)


def _find_marker_page(pdf_path: Path, marker: str) -> int | None:
    reader_main = PdfReader(str(pdf_path))
    for idx, page in enumerate(reader_main.pages):
        text = page.extract_text() or ""
        if marker in text:
            return idx
    return None


def integrate_addendum_to_main(main_pdf: Path, addendum_pdf: Path, marker: str) -> str:
    marker_page = _find_marker_page(main_pdf, marker)
    if marker_page is None:
        for legacy in LEGACY_MARKERS:
            marker_page = _find_marker_page(main_pdf, legacy)
            if marker_page is not None:
                break

    reader_main = PdfReader(str(main_pdf))
    reader_add = PdfReader(str(addendum_pdf))
    writer = PdfWriter()

    if marker_page is None:
        base_pages = reader_main.pages
        action = "appended"
    else:
        # Replace any prior addendum segment starting at the marker page.
        base_pages = reader_main.pages[:marker_page]
        action = "replaced"

    for page in base_pages:
        writer.add_page(page)
    for page in reader_add.pages:
        writer.add_page(page)

    if reader_main.metadata:
        writer.add_metadata(dict(reader_main.metadata))

    with NamedTemporaryFile("wb", delete=False, suffix=".pdf") as tmp:
        writer.write(tmp)
        tmp_path = Path(tmp.name)

    main_pdf.write_bytes(tmp_path.read_bytes())
    tmp_path.unlink(missing_ok=True)
    return action


def main() -> int:
    if not MAIN_PDF.is_file():
        raise SystemExit(f"Main PDF not found: {MAIN_PDF}")

    build_addendum_pdf(ADDENDUM_PDF)
    action = integrate_addendum_to_main(MAIN_PDF, ADDENDUM_PDF, MARKER)
    print(f"{action.title()} nuclear addendum v1.4.0 in main compendium: {MAIN_PDF}")
    print(f"Addendum PDF: {ADDENDUM_PDF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
