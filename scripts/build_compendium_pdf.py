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
import re
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
DEFAULT_INSERT_AFTER_PAGE = 82
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


def _find_marker_page(reader: PdfReader, marker: str) -> int | None:
    for idx, page in enumerate(reader.pages, start=1):
        if marker in _extract_text(page):
            return idx
    return None


def _find_insert_after_page(reader: PdfReader) -> int:
    """Find where J4 should be inserted so it remains adjacent to J0..J3."""

    for idx, page in enumerate(reader.pages, start=1):
        text = _extract_text(page).lower()
        if "4. integración con el flujo" in text or "4. integration with the flow" in text:
            return idx

    for idx, page in enumerate(reader.pages, start=1):
        text = _extract_text(page).lower()
        if "3. j3" in text and ("rfs" in text or "recursos finitos" in text):
            return idx

    return DEFAULT_INSERT_AFTER_PAGE


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
            "2) Methodology and lock architecture (J0-J4 integrated in one judge sequence)",
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
            ["Document A", "Methodological constraints and judge/lock contracts J0-J4."],
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
            "2) Metodologia y arquitectura de candados (J0-J4 integrados en una secuencia)",
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
            ["Documento A", "Restricciones metodologicas y contratos de jueces/candados J0-J4."],
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
        story.append(Paragraph("4. J4 — Nuclear Domain Guard (J4 / L4C* / L4E*)", st["h1"]))
        story.append(
            Paragraph(
                "Concept (invariant): a nuclear claim is evaluable only if the nuclear domain "
                "is explicitly declared and observationally anchored with reproducible provenance. "
                "J4 is not an optional add-on; it is the domain continuation of J0-J3.",
                st["body"],
            )
        )
        story.append(Paragraph("4.1 Why J4 is unavoidable", st["h1"]))
        story.append(
            Paragraph(
                "Without domain declarations, nuclear claims become tuneable narratives: "
                "the same statement can be made compatible with mutually incompatible channels "
                "or detector regimes. J4 prevents this by forcing explicit energy windows, "
                "isotopes, reaction channels, detector context, and evidence anchors.",
                st["body"],
            )
        )
        story.append(Paragraph("4.2 Concept-to-equation bridge", st["h1"]))
        story.append(
            Paragraph(
                "Invariant concept: evaluability in Ω_I and no hidden nuclear knob reinjection. "
                "Data-dependent equations: threshold checks, residual checks, and anchor tests.",
                st["body"],
            )
        )
        story.append(Paragraph("Eq. (1): 0 <= E_min < E_max  [MeV]", st["mono"]))
        story.append(Paragraph("Eq. (2): z = |sigma_pred - sigma_obs| / sigma_obs_err", st["mono"]))
        story.append(Paragraph("PASS(E) iff z <= z_max; FAIL(L4E5) iff z > z_max.", st["mono"]))
        story.append(Paragraph("4.3 L4C* locks (consistency/evaluability)", st["h1"]))
        l4c = [
            ("L4C1", "Declare domain.energy_range_mev.{min_mev,max_mev}; missing -> NO-EVAL."),
            ("L4C2", "Declare isotopes[] and reaction_channel; missing -> NO-EVAL."),
            ("L4C3", "Declare detectors[] and operational resolution context."),
            ("L4C4", "Units and thresholds must be explicit and internally consistent."),
            ("L4C5", "Channel and isotope mapping must be non-ambiguous in Ω_I."),
            ("L4C6", "No hidden control knob may carry claim support in Ω_I."),
            ("L4C7", "Finite, reproducible computation path is mandatory for judgment."),
        ]
        for code, text in l4c:
            story.append(Paragraph(f"<b>{code}</b>. {text}", st["body"]))

        story.append(PageBreak())
        story.append(Paragraph("4.4 L4E* locks (evidence/provenance)", st["h1"]))
        l4e = [
            ("L4E1", "Evidence anchor must include dataset_ref."),
            ("L4E2", "Provenance locator is required: source_url or dataset_doi."),
            ("L4E3", "sigma_obs and sigma_obs_err must be declared with units."),
            ("L4E4", "sigma_pred must reference the same observable definition."),
            ("L4E5", "Residual z-test is mandatory; violation -> FAIL(L4E5)."),
            ("L4E6", "Evidence timestamp/version and run trace must be reproducible."),
            ("L4E7", "If anchors are incomplete/untraceable -> NO-EVAL(L4E*)."),
        ]
        for code, text in l4e:
            story.append(Paragraph(f"<b>{code}</b>. {text}", st["body"]))
        story.append(Paragraph("4.5 Integration with J0-J3 flow", st["h1"]))
        story.append(
            Paragraph(
                "Evaluation order remains J0 -> J1 -> J2 -> J3 -> J4. "
                "J4 certifies domain-specific evaluability after projection, "
                "identifiability, and finite-resource stability are already satisfied.",
                st["body"],
            )
        )
        story.append(Paragraph("4.6 Runtime coupling (MRD and predictions)", st["h1"]))
        story.append(
            Paragraph(
                "Runtime assets: occ/judges/nuclear_guard.py, "
                "ILSC_MRD_suite_extensions/mrd_nuclear_guard/, "
                "examples/claim_specs/nuclear_*.yaml, and predictions/registry.yaml (P-0004).",
                st["body"],
            )
        )
        story.append(
            Paragraph(
                "CLI path:<br/>"
                "occ judge examples/claim_specs/nuclear_pass.yaml --profile nuclear<br/>"
                "occ verify --suite extensions --strict --timeout 60",
                st["mono"],
            )
        )
    else:
        story.append(Paragraph("4. J4 — Guardia de Dominio Nuclear (J4 / L4C* / L4E*)", st["h1"]))
        story.append(
            Paragraph(
                "Concepto (invariante): un claim nuclear solo es evaluable si declara "
                "explícitamente su dominio nuclear y lo ancla a evidencia trazable. "
                "J4 no es un extra opcional; es la continuación de J0-J3 en dominio nuclear.",
                st["body"],
            )
        )
        story.append(Paragraph("4.1 Por qué J4 es inevitable", st["h1"]))
        story.append(
            Paragraph(
                "Sin declaraciones de dominio, un mismo claim puede ajustarse "
                "artificialmente a canales o detectores incompatibles. J4 evita esa "
                "maleabilidad exigiendo ventana energética, isotopos, canal de reacción, "
                "contexto instrumental y anclaje observacional reproducible.",
                st["body"],
            )
        )
        story.append(Paragraph("4.2 Puente concepto->ecuacion", st["h1"]))
        story.append(
            Paragraph(
                "Concepto invariante: evaluabilidad en Ω_I sin reinyección de perillas "
                "ocultas. Ecuaciones dependientes de datos: chequeos de umbral, "
                "residuales y trazabilidad de anclajes.",
                st["body"],
            )
        )
        story.append(Paragraph("Ec. (1): 0 <= E_min < E_max  [MeV]", st["mono"]))
        story.append(Paragraph("Ec. (2): z = |sigma_pred - sigma_obs| / sigma_obs_err", st["mono"]))
        story.append(Paragraph("PASS(E) si z <= z_max; FAIL(L4E5) si z > z_max.", st["mono"]))
        story.append(Paragraph("4.3 Familia L4C* (consistencia/evaluabilidad)", st["h1"]))
        l4c = [
            ("L4C1", "Declarar domain.energy_range_mev.{min_mev,max_mev}; ausencia -> NO-EVAL."),
            ("L4C2", "Declarar isotopes[] y reaction_channel; ausencia -> NO-EVAL."),
            ("L4C3", "Declarar detectors[] y contexto de resolución operacional."),
            ("L4C4", "Unidades y umbrales explícitos, coherentes y auditables."),
            ("L4C5", "Mapeo no ambiguo entre canal/isótopos y observables en Ω_I."),
            ("L4C6", "Prohibida perilla oculta que sostenga el claim en Ω_I."),
            ("L4C7", "Ruta computacional finita y reproducible para emitir veredicto."),
        ]
        for code, text in l4c:
            story.append(Paragraph(f"<b>{code}</b>. {text}", st["body"]))

        story.append(PageBreak())
        story.append(Paragraph("4.4 Familia L4E* (evidencia/procedencia)", st["h1"]))
        l4e = [
            ("L4E1", "Anclaje obligatorio con evidence.dataset_ref."),
            ("L4E2", "Localizador de procedencia obligatorio: source_url o dataset_doi."),
            ("L4E3", "sigma_obs y sigma_obs_err declarados con unidades."),
            ("L4E4", "sigma_pred debe referir exactamente el mismo observable."),
            ("L4E5", "Test residual z obligatorio; violación -> FAIL(L4E5)."),
            ("L4E6", "Versionado temporal y traza de corrida reproducibles."),
            ("L4E7", "Anclajes incompletos/no trazables -> NO-EVAL(L4E*)."),
        ]
        for code, text in l4e:
            story.append(Paragraph(f"<b>{code}</b>. {text}", st["body"]))
        story.append(Paragraph("4.5 Integración en el flujo J0-J3", st["h1"]))
        story.append(
            Paragraph(
                "El orden de evaluación se mantiene: J0 -> J1 -> J2 -> J3 -> J4. "
                "J4 certifica evaluabilidad nuclear específica después de cumplir "
                "proyección, identificabilidad y estabilidad con recursos finitos.",
                st["body"],
            )
        )
        story.append(Paragraph("4.6 Acoplamiento con MRD y predicciones", st["h1"]))
        story.append(
            Paragraph(
                "Activos de runtime: occ/judges/nuclear_guard.py, "
                "ILSC_MRD_suite_extensions/mrd_nuclear_guard/, "
                "examples/claim_specs/nuclear_*.yaml y predictions/registry.yaml (P-0004).",
                st["body"],
            )
        )
        story.append(
            Paragraph(
                "Ruta CLI:<br/>"
                "occ judge examples/claim_specs/nuclear_pass.yaml --profile nuclear<br/>"
                "occ verify --suite extensions --strict --timeout 60",
                st["mono"],
            )
        )
    doc.build(story)


def _toc_entries(lang: str) -> List[Tuple[str, int]]:
    prediction_pages = {"section": 331, "p1": 331, "p2": 332, "p3": 333, "p4": 334, "p5": 335}

    if lang == "en":
        return [
            ("Scope", 1),
            ("Start Here", 2),
            ("Roadmap", 3),
            ("Document A+ - Formal Defense (OCC)", 5),
            ("Addendum - Real-Judge Upgrade", 48),
            ("Document A - Methodology (J0-J4 judges and locks)", 53),
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
            ("Predictions", prediction_pages["section"]),
            ("Prediction 1 - aQGC (VBS): positivity (one-operator)", prediction_pages["p1"]),
            ("Prediction 2 - Cosmology: OCC prior + local-cosmo bridge", prediction_pages["p2"]),
            ("Prediction 3 - Baryogenesis: EDM-GW correlation", prediction_pages["p3"]),
            ("Prediction 4 - IR gravity: PPN + gravitational waves", prediction_pages["p4"]),
            (
                "Prediction 5 - Dynamic 4F unification: multi-front consistency",
                prediction_pages["p5"],
            ),
        ]
    return [
        ("Alcance", 1),
        ("Empieza aqui", 2),
        ("Mapa del compendio", 3),
        ("Documento A+ - Defensa formal (OCC)", 5),
        ("Addendum - Real-Judge Upgrade", 48),
        ("Documento A - Metodologia (jueces y candados J0-J4)", 53),
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
        ("Predicciones", prediction_pages["section"]),
        ("Prediccion 1 - aQGC (VBS): positividad (one-operator)", prediction_pages["p1"]),
        ("Prediccion 2 - Cosmologia: prior OCC + puente local-cosmo", prediction_pages["p2"]),
        ("Prediccion 3 - Bariogenesis: correlacion EDM-GW", prediction_pages["p3"]),
        ("Prediccion 4 - Gravedad IR: PPN + ondas gravitacionales", prediction_pages["p4"]),
        (
            "Prediccion 5 - Unificacion dinamica 4F: consistencia multifrente",
            prediction_pages["p5"],
        ),
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
    insert_after_page: int,
) -> Iterable[Tuple[int, object, bool]]:
    for idx, page in enumerate(pages, start=1):
        yield idx, page, False
        if add_inserted and idx == insert_after_page:
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
    insert_after_page: int,
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

    marker_page = _find_marker_page(base_reader, marker)
    already_integrated = marker_page is not None
    inserted_pages = list(section_reader.pages)
    did_insert = False

    for page_no, page, is_inserted in _iter_with_insert(
        base_reader.pages,
        inserted_pages,
        not already_integrated,
        insert_after_page,
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

    normalization = _normalize_prediction_language_pages(out_pdf, lang)
    out_reader = PdfReader(str(out_pdf))
    integrated_page = marker_page or (insert_after_page + 1)
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
        "insert_after_page": insert_after_page,
        "integrated_page": integrated_page,
        "marker": marker,
        "lang": lang,
        "prediction_normalization": normalization,
    }


def _prediction_candidate_pages(reader: PdfReader) -> List[int]:
    pages: List[int] = []
    for idx, page in enumerate(reader.pages, start=1):
        text = _extract_text(page).lower()
        if "predicción #" in text or "prediccion #" in text or _is_english_prediction_page(text):
            pages.append(idx)
    return pages


def _is_english_prediction_page(text: str) -> bool:
    return re.search(r"\benglish\s+context:", text) is not None


def _normalize_prediction_language_pages(out_pdf: Path, lang: str) -> dict[str, int]:
    """Keep only language-matching prediction pages instead of duplicating pairs."""

    reader = PdfReader(str(out_pdf))
    total = len(reader.pages)
    candidates = _prediction_candidate_pages(reader)
    if not candidates:
        return {"removed_pages": 0, "total_before": total, "total_after": total}

    span_start = min(candidates)
    span_end = max(candidates)

    writer = PdfWriter()
    removed_pages = 0
    kept_prediction_pages = 0
    for idx in range(1, total + 1):
        page = reader.pages[idx - 1]
        if span_start <= idx <= span_end:
            text = _extract_text(page).lower()
            if (
                "predicción #" in text
                or "prediccion #" in text
                or _is_english_prediction_page(text)
            ):
                if lang == "en":
                    keep = _is_english_prediction_page(text)
                else:
                    keep = not _is_english_prediction_page(text)
                if not keep:
                    removed_pages += 1
                    continue
                kept_prediction_pages += 1
        writer.add_page(page)

    if reader.metadata:
        writer.add_metadata(dict(reader.metadata))
    with NamedTemporaryFile("wb", delete=False, suffix=".pdf") as tmp:
        writer.write(tmp)
        tmp_path = Path(tmp.name)
    out_pdf.write_bytes(tmp_path.read_bytes())
    tmp_path.unlink(missing_ok=True)

    return {
        "removed_pages": removed_pages,
        "total_before": total,
        "total_after": len(writer.pages),
        "prediction_span_start": span_start,
        "prediction_span_end": span_end,
        "kept_prediction_pages": kept_prediction_pages,
    }


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

    base = _resolve_base(args.base)
    base_reader = PdfReader(str(base))
    insert_after_page = _find_insert_after_page(base_reader)

    build_front_patch(front, args.lang)
    build_integrated_nuclear_section(section, args.lang, marker)
    build_toc_patch(toc, args.lang)
    result = build_compendium(
        base,
        front,
        section,
        toc,
        out,
        marker,
        args.lang,
        insert_after_page,
    )

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
    print(f"  insert_after_page: {result['insert_after_page']}")
    print(f"  integrated_page: {result['integrated_page']}")
    print(f"  section_inserted: {result['section_inserted']}")
    print(f"  already_integrated: {result['already_integrated']}")
    norm = result["prediction_normalization"]
    print(
        "  prediction_normalization: "
        f"removed={norm['removed_pages']} "
        f"before={norm['total_before']} after={norm['total_after']}"
    )

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
