#!/usr/bin/env python3
"""Build OCC compendium PDFs with language-separated integration blocks.

Editorial goals:
- No bilingual pages in newly generated integration blocks.
- Keep nuclear integration inside the canonical flow (not detached at the end).
- Keep English as default release-facing output.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable, List, Tuple

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = ROOT / "docs" / "OCC_Compendio_Canonico_Completo_FINAL_INTRO (1).pdf"
DEFAULT_BASE_FALLBACK = ROOT / "docs" / "OCC_Compendio_Canonico_Completo.pdf"
DEFAULT_OUT_EN = ROOT / "docs" / "OCC_Canonical_Compendium_EN_v1.5.0.pdf"
DEFAULT_OUT_ES = ROOT / "docs" / "OCC_Compendio_Canonico_ES_v1.5.0.pdf"
DEFAULT_MAIN = ROOT / "docs" / "OCC_Compendio_Canonico_Completo.pdf"
SECTION_EN = ROOT / "docs" / "canonical" / "OCC_Integrated_Nuclear_Section_EN_v1.5.0.pdf"
SECTION_ES = ROOT / "docs" / "canonical" / "OCC_Seccion_Integrada_Nuclear_ES_v1.5.0.pdf"
TOC_EN = ROOT / "docs" / "canonical" / "OCC_TOC_EN_v1.5.0.pdf"
TOC_ES = ROOT / "docs" / "canonical" / "OCC_TOC_ES_v1.5.0.pdf"
FRONT_EN = ROOT / "docs" / "canonical" / "OCC_FRONT_EN_v1.5.0.pdf"
FRONT_ES = ROOT / "docs" / "canonical" / "OCC_FRONT_ES_v1.5.0.pdf"
MARKER_EN = "NUCLEAR-INTEGRATED-SECTION-EN-V1.5.0"
MARKER_ES = "NUCLEAR-INTEGRATED-SECTION-ES-V1.5.0"
INSERT_AFTER_PAGE = 82  # after Documento A - Metodologia
TOC_REPLACE_PAGE = 4

logging.getLogger("pypdf").setLevel(logging.ERROR)


def _extract_text(page: object) -> str:
    try:
        return str(getattr(page, "extract_text")() or "")
    except Exception:
        return ""


def _contains_marker(reader: PdfReader, marker: str) -> bool:
    for page in reader.pages:
        if marker in _extract_text(page):
            return True
    return False


def _resolve_base(path: Path) -> Path:
    if path.is_file():
        return path
    if path == DEFAULT_BASE and DEFAULT_BASE_FALLBACK.is_file():
        return DEFAULT_BASE_FALLBACK
    raise FileNotFoundError(f"Base compendium not found: {path}")


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleIntegrated",
            parent=base["Title"],
            fontSize=16,
            leading=20,
            spaceAfter=10,
        ),
        "h1": ParagraphStyle(
            "H1Integrated",
            parent=base["Heading1"],
            fontSize=12,
            leading=15,
            spaceBefore=6,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "BodyIntegrated",
            parent=base["BodyText"],
            fontSize=10,
            leading=13,
            spaceAfter=6,
        ),
        "mono": ParagraphStyle(
            "MonoIntegrated",
            parent=base["Code"],
            fontSize=9,
            leading=11,
            spaceAfter=5,
        ),
        "toc_title": ParagraphStyle(
            "TocTitleIntegrated",
            parent=base["Heading1"],
            fontSize=11,
            leading=13,
            spaceAfter=6,
        ),
        "toc_label": ParagraphStyle(
            "TocLabelIntegrated",
            parent=base["BodyText"],
            fontSize=9,
            leading=11,
        ),
        "front_title": ParagraphStyle(
            "FrontTitleIntegrated",
            parent=base["Title"],
            fontSize=22,
            leading=26,
            spaceAfter=10,
        ),
        "front_h2": ParagraphStyle(
            "FrontH2Integrated",
            parent=base["Heading2"],
            fontSize=13,
            leading=16,
            spaceBefore=6,
            spaceAfter=4,
        ),
        "front_body": ParagraphStyle(
            "FrontBodyIntegrated",
            parent=base["BodyText"],
            fontSize=10.5,
            leading=14,
            spaceAfter=8,
        ),
    }


def build_front_patch(path: Path, lang: str) -> None:
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

    if lang == "en":
        story.append(Paragraph("Operational Consistency Compiler (OCC)", st["front_title"]))
        story.append(
            Paragraph(
                "Canonical Compendium (English Edition) - v1.5.0",
                st["front_h2"],
            )
        )
        story.append(
            Paragraph(
                "Date: 2026-02-17<br/>Repository: github.com/MarcoAIsaac/OCC",
                st["front_body"],
            )
        )
        story.append(
            Paragraph(
                "Scope: canonical theory framework, operational methodology, closed MRD modules, "
                "and prediction catalog with reproducible traces.",
                st["front_body"],
            )
        )
        story.append(
            Paragraph(
                "Editorial note: this English document is generated from the current canonical "
                "source set and includes the integrated nuclear section J4/L4C*/L4E*.",
                st["front_body"],
            )
        )

        story.append(PageBreak())
        story.append(Paragraph("Start Here", st["front_h2"]))
        story.append(
            Paragraph(
                "Read the compendium in this order for fastest onboarding:",
                st["front_body"],
            )
        )
        onboarding = [
            "1) Formal foundations (Document A+)",
            "2) Methodology and lock architecture (J0-J3 + integrated J4 domain package)",
            "3) MRD modules and reproducible PASS/FAIL/NO-EVAL workflows",
            "4) Prediction set and experimental-facing witness logic",
        ]
        for line in onboarding:
            story.append(Paragraph(line, st["front_body"]))

        story.append(PageBreak())
        story.append(Paragraph("Roadmap", st["front_h2"]))
        data = [
            ["Section", "Purpose"],
            ["Document A+", "Formal operational semantics and judge structure."],
            ["Document A", "Methodological constraints and lock contracts."],
            ["Integrated nuclear section", "J4/L4C*/L4E* domain package in-line."],
            ["MRD modules", "Executable reproducibility and verdict artifacts."],
            ["Predictions", "Operationally falsifiable outputs and witness mapping."],
        ]
    else:
        story.append(Paragraph("Operational Consistency Compiler (OCC)", st["front_title"]))
        story.append(
            Paragraph(
                "Compendio Canonico (Edicion en Espanol) - v1.5.0",
                st["front_h2"],
            )
        )
        story.append(
            Paragraph(
                "Fecha: 2026-02-17<br/>Repositorio: github.com/MarcoAIsaac/OCC",
                st["front_body"],
            )
        )
        story.append(
            Paragraph(
                "Alcance: marco teorico canonico, metodologia operacional, modulos MRD cerrados "
                "y catalogo de predicciones con trazabilidad reproducible.",
                st["front_body"],
            )
        )
        story.append(
            Paragraph(
                "Nota editorial: este documento en espanol se genera desde el conjunto canonico "
                "actual e integra la seccion nuclear J4/L4C*/L4E* en el flujo principal.",
                st["front_body"],
            )
        )

        story.append(PageBreak())
        story.append(Paragraph("Empieza Aqui", st["front_h2"]))
        story.append(
            Paragraph(
                "Lee el compendio en este orden para acelerar el onboarding:",
                st["front_body"],
            )
        )
        onboarding = [
            "1) Fundamentos formales (Documento A+)",
            "2) Metodologia y arquitectura de candados (J0-J3 + paquete J4 integrado)",
            "3) Modulos MRD y flujos reproducibles PASS/FAIL/NO-EVAL",
            "4) Set de predicciones y logica de testigos para contrastacion experimental",
        ]
        for line in onboarding:
            story.append(Paragraph(line, st["front_body"]))

        story.append(PageBreak())
        story.append(Paragraph("Mapa del Compendio", st["front_h2"]))
        data = [
            ["Seccion", "Proposito"],
            ["Documento A+", "Semantica operacional formal y estructura de jueces."],
            ["Documento A", "Restricciones metodologicas y contratos de candados."],
            ["Seccion nuclear integrada", "Paquete de dominio J4/L4C*/L4E* en linea."],
            ["Modulos MRD", "Reproducibilidad ejecutable y artefactos de veredicto."],
            ["Predicciones", "Salidas falsables operacionalmente y mapeo de testigos."],
        ]

    table = Table(data, colWidths=[5.2 * cm, 10.0 * cm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5eef9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)
    doc.build(story)


def build_integrated_nuclear_section(path: Path, lang: str, marker: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        topMargin=2.0 * cm,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
    )
    st = _styles()
    story = []

    if lang == "en":
        story.append(
            Paragraph(
                "OCC Integrated Section - Nuclear Domain (J4 / L4C* / L4E*) v1.5.0",
                st["title"],
            )
        )
        story.append(
            Paragraph(
                f"Marker: <b>{marker}</b><br/>Date: 2026-02-17<br/>"
                "Editorial status: integrated canonical section (not detached addendum).",
                st["body"],
            )
        )
        story.append(Paragraph("1. Canonical placement and numbering", st["h1"]))
        story.append(
            Paragraph(
                "Foundational judges remain J0-J3 (ISAAC/PA/IO/RFS). "
                "Nuclear-domain constraints are integrated as J4 with lock families "
                "L4C* (consistency/evaluability) and L4E* (evidence/provenance).",
                st["body"],
            )
        )
        story.append(Paragraph("2. Operational lock semantics", st["h1"]))
        story.append(
            Paragraph(
                "Class C requires explicit domain declarations (energy range, isotopes, "
                "reaction channel, detectors). Missing declarations -> NO-EVAL(L4C*). "
                "Malformed domain constraints -> FAIL(L4C*).",
                st["body"],
            )
        )
        story.append(Paragraph("Eq. (1): 0 <= E_min < E_max  [MeV]", st["mono"]))
        story.append(
            Paragraph(
                "Class E requires an evidence anchor and provenance reference.",
                st["body"],
            )
        )
        story.append(Paragraph("Eq. (2): z = |sigma_pred - sigma_obs| / sigma_obs_err", st["mono"]))
        story.append(Paragraph("PASS(E) iff z <= z_max; FAIL(L4E5) iff z > z_max.", st["mono"]))
        story.append(Paragraph("3. MRD and prediction coupling", st["h1"]))
        story.append(
            Paragraph(
                "Integrated assets in OCC runtime: "
                "occ/judges/nuclear_guard.py, "
                "ILSC_MRD_suite_extensions/mrd_nuclear_guard/, "
                "examples/claim_specs/nuclear_*.yaml, "
                "predictions/registry.yaml (P-0004).",
                st["body"],
            )
        )
        story.append(
            Paragraph(
                "CLI path:<br/>"
                "occ judge examples/claim_specs/nuclear_pass.yaml --profile auto<br/>"
                "occ verify --suite extensions --strict --timeout 60",
                st["mono"],
            )
        )
    else:
        story.append(
            Paragraph(
                "OCC Seccion Integrada - Dominio Nuclear (J4 / L4C* / L4E*) v1.5.0",
                st["title"],
            )
        )
        story.append(
            Paragraph(
                f"Marca: <b>{marker}</b><br/>Fecha: 2026-02-17<br/>"
                "Estado editorial: seccion canonica integrada (no addendum externo).",
                st["body"],
            )
        )
        story.append(Paragraph("1. Ubicacion canonica y numeracion", st["h1"]))
        story.append(
            Paragraph(
                "Los jueces fundacionales siguen siendo J0-J3 (ISAAC/PA/IO/RFS). "
                "Las restricciones del dominio nuclear se integran como J4 con familias "
                "de candados L4C* (consistencia/evaluabilidad) y "
                "L4E* (evidencia/procedencia).",
                st["body"],
            )
        )
        story.append(Paragraph("2. Semantica operacional de candados", st["h1"]))
        story.append(
            Paragraph(
                "La Clase C exige declaraciones explicitas de dominio (energia, isotopos, "
                "canal de reaccion, detectores). Ausencias -> NO-EVAL(L4C*). "
                "Inconsistencias de dominio -> FAIL(L4C*).",
                st["body"],
            )
        )
        story.append(Paragraph("Ec. (1): 0 <= E_min < E_max  [MeV]", st["mono"]))
        story.append(
            Paragraph(
                "La Clase E exige anclaje observacional y referencia de procedencia.",
                st["body"],
            )
        )
        story.append(Paragraph("Ec. (2): z = |sigma_pred - sigma_obs| / sigma_obs_err", st["mono"]))
        story.append(Paragraph("PASS(E) si z <= z_max; FAIL(L4E5) si z > z_max.", st["mono"]))
        story.append(Paragraph("3. Acoplamiento MRD y predicciones", st["h1"]))
        story.append(
            Paragraph(
                "Activos integrados en OCC runtime: "
                "occ/judges/nuclear_guard.py, "
                "ILSC_MRD_suite_extensions/mrd_nuclear_guard/, "
                "examples/claim_specs/nuclear_*.yaml, "
                "predictions/registry.yaml (P-0004).",
                st["body"],
            )
        )
        story.append(
            Paragraph(
                "Ruta CLI:<br/>"
                "occ judge examples/claim_specs/nuclear_pass.yaml --profile auto<br/>"
                "occ verify --suite extensions --strict --timeout 60",
                st["mono"],
            )
        )

    story.append(PageBreak())
    if lang == "en":
        story.append(Paragraph("Nuclear integration checklist (J4/L4) - operational", st["h1"]))
        story.append(
            Paragraph(
                "Required claim declarations: domain.energy_range_mev, domain.isotopes, "
                "domain.reaction_channel, domain.detectors, evidence anchor, "
                "dataset reference and URL/DOI locator.",
                st["body"],
            )
        )
        story.append(
            Paragraph(
                "Editorial policy: all future judge/lock/module/prediction updates must be "
                "integrated in-line in the compendium flow with numbering continuity.",
                st["body"],
            )
        )
    else:
        story.append(Paragraph("Checklist de integracion nuclear (J4/L4) - operacional", st["h1"]))
        story.append(
            Paragraph(
                "Declaraciones obligatorias del claim: domain.energy_range_mev, "
                "domain.isotopes, domain.reaction_channel, domain.detectors, "
                "anclaje de evidencia, referencia de dataset y localizador URL/DOI.",
                st["body"],
            )
        )
        story.append(
            Paragraph(
                "Politica editorial: toda actualizacion futura de jueces/candados/modulos/"
                "predicciones debe integrarse en linea en el flujo del compendio, "
                "respetando continuidad de numeracion.",
                st["body"],
            )
        )
    doc.build(story)


def _toc_entries(lang: str) -> List[Tuple[str, int]]:
    if lang == "en":
        return [
            ("Scope", 1),
            ("Start Here", 2),
            ("Roadmap", 3),
            ("Document A+ - Formal Defense (OCC)", 5),
            ("Addendum - Real-Judge Upgrade", 48),
            ("Document A - Methodology (J0-J3 judges and locks)", 53),
            ("Integrated section - Nuclear domain (J4/L4C*/L4E*)", 83),
            ("Closed modules (MRD)", 85),
            ("Module - Observability and instrumentation (ISAAC)", 85),
            ("Module - UV projection -> Omega_I (auditable)", 101),
            ("Module 4F - Operational dictionary (CUI/HUI)", 119),
            ("Module - Schwinger-Keldysh (open systems)", 137),
            ("Module - Effective branch, decoherence, objectivity", 152),
            ("Module - Symmetries, anomalies, topology (operational)", 169),
            ("Module - EFT: operational renormalization", 187),
            ("Module G0 - Effective dark matter", 204),
            ("Module - Vacuum and effective dark energy", 219),
            ("Module - IR gravity: PPN and gravitational waves", 234),
            ("Module - Operational cosmology: local-cosmo bridge", 249),
            ("Module 4F - Operational unification (gating)", 268),
            ("Module 4F - Dynamic unification (multi-front consistency)", 283),
            ("Module - Amplitudes: analyticity, unitarity, positivity", 299),
            ("Module - Baryogenesis: EDM-GW correlation", 316),
            ("Predictions", 331),
            ("Prediction 1 - aQGC (VBS): positivity (one-operator)", 331),
            ("Prediction 2 - Cosmology: OCC prior + local-cosmo bridge", 333),
            ("Prediction 3 - Baryogenesis: EDM-GW correlation", 335),
            ("Prediction 4 - IR gravity: PPN + gravitational waves", 337),
            ("Prediction 5 - Dynamic 4F unification: multi-front consistency", 339),
        ]
    return [
        ("Alcance", 1),
        ("Empieza aqui", 2),
        ("Mapa del compendio", 3),
        ("Documento A+ - Defensa formal (OCC)", 5),
        ("Addendum - Real-Judge Upgrade", 48),
        ("Documento A - Metodologia (jueces y candados J0-J3)", 53),
        ("Seccion integrada - Dominio nuclear (J4/L4C*/L4E*)", 83),
        ("Modulos cerrados (MRD)", 85),
        ("Modulo - Observabilidad e instrumentacion (ISAAC)", 85),
        ("Modulo - Proyeccion UV -> Omega_I (auditable)", 101),
        ("Modulo 4F - Diccionario operacional (CUI/HUI)", 119),
        ("Modulo - Schwinger-Keldysh (sistemas abiertos)", 137),
        ("Modulo - Rama efectiva, decoherencia, objetividad", 152),
        ("Modulo - Simetrias, anomalias, topologia (operacional)", 169),
        ("Modulo - EFT: renormalizacion operacional", 187),
        ("Modulo G0 - Materia oscura efectiva", 204),
        ("Modulo - Vacio y energia oscura efectiva", 219),
        ("Modulo - Gravedad IR: PPN y ondas gravitacionales", 234),
        ("Modulo - Cosmologia operacional: puente local-cosmo", 249),
        ("Modulo 4F - Unificacion operacional (gating)", 268),
        ("Modulo 4F - Unificacion dinamica (consistencia multifrente)", 283),
        ("Modulo - Amplitudes: analiticidad, unitariedad, positividad", 299),
        ("Modulo - Bariogenesis: correlacion EDM-GW", 316),
        ("Predicciones", 331),
        ("Prediccion 1 - aQGC (VBS): positividad (one-operator)", 331),
        ("Prediccion 2 - Cosmologia: prior OCC + puente local-cosmo", 333),
        ("Prediccion 3 - Bariogenesis: correlacion EDM-GW", 335),
        ("Prediccion 4 - Gravedad IR: PPN + ondas gravitacionales", 337),
        ("Prediccion 5 - Unificacion dinamica 4F: consistencia multifrente", 339),
    ]


def build_toc_patch(path: Path, lang: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        topMargin=1.8 * cm,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        bottomMargin=1.8 * cm,
    )
    st = _styles()
    story = []
    if lang == "en":
        story.append(Paragraph("OCC Canonical Compendium - TOC", st["toc_title"]))
        story.append(Paragraph("3  Table of Contents", st["toc_label"]))
    else:
        story.append(Paragraph("Compendio Canonico OCC - Indice", st["toc_title"]))
        story.append(Paragraph("3  Indice", st["toc_label"]))
    story.append(Spacer(1, 0.2 * cm))

    data: List[List[object]] = []
    for label, page in _toc_entries(lang):
        data.append([Paragraph(label, st["toc_label"]), Paragraph(str(page), st["toc_label"])])

    table = Table(data, colWidths=[14.8 * cm, 1.5 * cm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.2 * cm))
    if lang == "en":
        story.append(Paragraph("OCC Canonical Compendium - TOC", st["toc_label"]))
    else:
        story.append(Paragraph("Compendio Canonico OCC - Indice", st["toc_label"]))
    doc.build(story)


def _iter_with_insert(
    pages: Iterable[object],
    inserted_pages: List[object],
    add_inserted: bool,
) -> Iterable[Tuple[int, object, bool]]:
    for idx, page in enumerate(pages, start=1):
        yield idx, page, False
        if add_inserted and idx == INSERT_AFTER_PAGE:
            for inserted in inserted_pages:
                yield idx, inserted, True


def build_compendium(
    base_pdf: Path,
    front_pdf: Path,
    section_pdf: Path,
    toc_pdf: Path,
    out_pdf: Path,
    marker: str,
    lang: str,
) -> dict[str, object]:
    base_pdf = _resolve_base(base_pdf)
    if not front_pdf.is_file():
        raise FileNotFoundError(f"Front patch PDF not found: {front_pdf}")
    if not section_pdf.is_file():
        raise FileNotFoundError(f"Integrated section PDF not found: {section_pdf}")
    if not toc_pdf.is_file():
        raise FileNotFoundError(f"TOC patch PDF not found: {toc_pdf}")

    base_reader = PdfReader(str(base_pdf))
    front_reader = PdfReader(str(front_pdf))
    section_reader = PdfReader(str(section_pdf))
    toc_reader = PdfReader(str(toc_pdf))
    writer = PdfWriter()

    already_integrated = _contains_marker(base_reader, marker)
    inserted_pages = list(section_reader.pages)
    did_insert = False

    for page_no, page, is_inserted in _iter_with_insert(
        base_reader.pages,
        inserted_pages,
        not already_integrated,
    ):
        if is_inserted:
            writer.add_page(page)
            did_insert = True
            continue

        if page_no in (1, 2, 3):
            writer.add_page(front_reader.pages[page_no - 1])
        elif page_no == TOC_REPLACE_PAGE:
            writer.add_page(toc_reader.pages[0])
        else:
            writer.add_page(page)

    if base_reader.metadata:
        metadata = dict(base_reader.metadata)
    else:
        metadata = {}

    if lang == "en":
        metadata["/Title"] = "OCC Canonical Compendium EN v1.5.0"
    else:
        metadata["/Title"] = "OCC Compendio Canonico ES v1.5.0"
    metadata["/Subject"] = "Integrated canonical compendium with J4/L4 nuclear section"
    metadata["/Creator"] = "OCC compendium builder (pypdf + reportlab)"
    writer.add_metadata(metadata)

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("wb", delete=False, suffix=".pdf") as tmp:
        writer.write(tmp)
        tmp_path = Path(tmp.name)
    out_pdf.write_bytes(tmp_path.read_bytes())
    tmp_path.unlink(missing_ok=True)

    _normalize_prediction_language_pages(out_pdf, lang)
    out_reader = PdfReader(str(out_pdf))
    return {
        "base": str(base_pdf),
        "front_patch": str(front_pdf),
        "section": str(section_pdf),
        "toc_patch": str(toc_pdf),
        "output": str(out_pdf),
        "base_pages": len(base_reader.pages),
        "section_pages": len(section_reader.pages),
        "output_pages": len(out_reader.pages),
        "already_integrated": already_integrated,
        "section_inserted": did_insert,
        "marker": marker,
        "lang": lang,
    }


def _normalize_prediction_language_pages(out_pdf: Path, lang: str) -> None:
    """Normalize prediction pair pages to reduce visible ES/EN mixing.

    Base pattern in current compendium tail is paired pages:
    - odd: ES prediction page
    - even: EN context page
    """

    reader = PdfReader(str(out_pdf))
    writer = PdfWriter()
    total = len(reader.pages)

    if lang == "es":
        replacement_map = {332: 331, 334: 333, 336: 335, 338: 337, 340: 339}
    else:
        replacement_map = {331: 332, 333: 334, 335: 336, 337: 338, 339: 340}

    for idx in range(1, total + 1):
        source = replacement_map.get(idx, idx)
        if source < 1 or source > total:
            source = idx
        writer.add_page(reader.pages[source - 1])

    if reader.metadata:
        writer.add_metadata(dict(reader.metadata))
    with NamedTemporaryFile("wb", delete=False, suffix=".pdf") as tmp:
        writer.write(tmp)
        tmp_path = Path(tmp.name)
    out_pdf.write_bytes(tmp_path.read_bytes())
    tmp_path.unlink(missing_ok=True)


def audit_language_traces(pdf_path: Path, lang: str) -> dict[str, object]:
    """Heuristic audit for opposite-language traces in a PDF."""

    reader = PdfReader(str(pdf_path))
    if lang == "en":
        needles = [" español", " predicción", "jueces", "candados", "metodología"]
    else:
        needles = [" english ", "table of contents", "start here", "prediction", "judges", "locks"]

    pages = []
    for idx, page in enumerate(reader.pages, start=1):
        text = f" {_extract_text(page).lower()} "
        if any(n in text for n in needles):
            pages.append(idx)
    return {
        "pdf": str(pdf_path),
        "lang": lang,
        "total_pages": len(reader.pages),
        "opposite_trace_pages": pages,
        "count": len(pages),
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build integrated OCC compendium PDF with inline nuclear section."
    )
    p.add_argument("--base", type=Path, default=DEFAULT_BASE)
    p.add_argument("--lang", choices=["en", "es"], default="en")
    p.add_argument("--out", type=Path, help="Output PDF path")
    p.add_argument(
        "--replace-main",
        action="store_true",
        help="Overwrite docs/OCC_Compendio_Canonico_Completo.pdf with built output.",
    )
    p.add_argument(
        "--audit-lang",
        action="store_true",
        help="Print basic opposite-language trace metrics after building.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.lang == "en":
        front = FRONT_EN
        section = SECTION_EN
        toc = TOC_EN
        marker = MARKER_EN
        out = args.out or DEFAULT_OUT_EN
    else:
        front = FRONT_ES
        section = SECTION_ES
        toc = TOC_ES
        marker = MARKER_ES
        out = args.out or DEFAULT_OUT_ES

    build_front_patch(front, args.lang)
    build_integrated_nuclear_section(section, args.lang, marker)
    build_toc_patch(toc, args.lang)
    result = build_compendium(args.base, front, section, toc, out, marker, args.lang)

    print("Built integrated compendium:")
    print(f"  lang: {result['lang']}")
    print(f"  base: {result['base']}")
    print(f"  front_patch: {result['front_patch']}")
    print(f"  section: {result['section']}")
    print(f"  toc_patch: {result['toc_patch']}")
    print(f"  output: {result['output']}")
    print(f"  base_pages: {result['base_pages']}")
    print(f"  section_pages: {result['section_pages']}")
    print(f"  output_pages: {result['output_pages']}")
    print(f"  section_inserted: {result['section_inserted']}")
    print(f"  already_integrated: {result['already_integrated']}")

    if args.replace_main:
        main_pdf = DEFAULT_MAIN
        main_pdf.write_bytes(Path(str(result["output"])).read_bytes())
        print(f"  replaced_main: {main_pdf}")

    if args.audit_lang:
        audit = audit_language_traces(Path(str(result["output"])), args.lang)
        print("Language trace audit:")
        print(f"  opposite_trace_count: {audit['count']}")
        sample = list(audit["opposite_trace_pages"])[:20]
        print(f"  opposite_trace_pages_sample: {sample}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
