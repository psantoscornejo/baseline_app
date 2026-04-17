"""
BASELINE SOLUTIONS — Guía interactiva del estado del arte en cierre de minas
==============================================================================
Aplicación Streamlit que consolida:
  - Marco regulatorio SERNAGEOMIN (Ley 20.551, DS 41/2012, guías metodológicas)
  - ICMM Integrated Mine Closure Good Practice Guide (2019) — 17 elementos
  - GISTM Global Industry Standard on Tailings Management (2020) — 15 principios
  - Matriz de correlación para incorporación en Planes de Cierre
  - Roadmap de cumplimiento y checklist auto-evaluable

Autor: Baseline Solutions — consultoría especializada en cierre de minas y gestión de pasivos ambientales.
Uso:
    pip install streamlit pandas
    streamlit run app.py
"""

import base64
import io
import os
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

# =============================================================================
# CONFIGURACIÓN DE PÁGINA
# =============================================================================
st.set_page_config(
    page_title="Guía Cierre de Minas — Chile",
    page_icon="⛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Paleta de marca (tomada del logo)
BRAND_DARK = "#1F2E3D"
BRAND_ORANGE = "#C14A1F"
BRAND_SLATE = "#4A5A6A"
BRAND_LIGHT = "#F4F6F8"

CUSTOM_CSS = f"""
<style>
    .main > div {{ padding-top: 1rem; }}
    h1, h2, h3 {{ color: {BRAND_DARK}; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 4px; }}
    .stTabs [data-baseweb="tab"] {{
        background-color: {BRAND_SLATE};
        border-radius: 6px 6px 0 0;
        padding: 8px 16px;
        font-weight: 600;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {BRAND_DARK};
        color: {BRAND_SLATE};
    }}
    div[data-testid="stMetricValue"] {{ color: {BRAND_ORANGE}; }}
    .hero-box {{
        background: linear-gradient(135deg, {BRAND_DARK} 0%, {BRAND_SLATE} 100%);
        padding: 28px 32px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }}
    .hero-box h1 {{ color: {BRAND_SLATE}; margin: 0; font-size: 1.9rem; }}
    .hero-box p {{ color: #D8DEE4; margin: 6px 0 0 0; font-size: 1rem; }}
    .callout {{
        border-left: 4px solid {BRAND_ORANGE};
        background: {BRAND_DARK};
        padding: 12px 16px;
        border-radius: 4px;
        margin: 10px 0;
    }}
    .principle-card {{
        background: {BRAND_SLATE};
        border: 1px solid #E1E5EB;
        border-left: 4px solid {BRAND_ORANGE};
        padding: 14px 18px;
        border-radius: 6px;
        margin-bottom: 10px;
    }}
    /* Espaciado entre opciones del radio en el sidebar */
    section[data-testid="stSidebar"] div[role="radiogroup"] label {{
        padding-top: 8px;
        padding-bottom: 8px;
        line-height: 1.5;
    }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =============================================================================
# HELPERS
# =============================================================================
def get_logo_base64():
    """Carga el logo local si existe y lo devuelve como base64."""
    logo_path = Path(__file__).parent / "logo.jpeg"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


def render_header(subtitle: str):
    """Header con título por página."""
    st.markdown(
        f'<div class="hero-box" style="position:relative;">'
        f'<h1>{subtitle}</h1>'
        f'<p>Guía interactiva del estado del arte — Cierre de minas en Chile</p>'
        f'<span style="position:absolute;bottom:8px;right:14px;'
        f'font-size:0.72rem;color:#aab0bb;letter-spacing:0.5px;">'
        f'Patricio Santos</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


# =============================================================================
# HELPER — GENERADOR PDF GAP ASSESSMENT
# =============================================================================
def generate_gap_pdf(empresa: str, responsable: str, checklist_items: dict, scores: dict) -> bytes:
    """Genera un informe PDF de gap assessment."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.platypus import (
            HRFlowable, Image, Paragraph, SimpleDocTemplate,
            Spacer, Table, TableStyle,
        )
    except ImportError:
        return b""

    C_DARK   = colors.HexColor("#1F2E3D")
    C_ORANGE = colors.HexColor("#C14A1F")
    C_SLATE  = colors.HexColor("#4A5A6A")
    C_LIGHT  = colors.HexColor("#F4F6F8")
    C_WHITE  = colors.white

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    s_title   = ParagraphStyle("Title",   parent=styles["Normal"], fontSize=22, textColor=C_WHITE,   leading=28, alignment=TA_CENTER, fontName="Helvetica-Bold")
    s_sub     = ParagraphStyle("Sub",     parent=styles["Normal"], fontSize=11, textColor=C_LIGHT,   leading=15, alignment=TA_CENTER)
    s_h2      = ParagraphStyle("H2",      parent=styles["Normal"], fontSize=13, textColor=C_DARK,    leading=18, spaceBefore=12, fontName="Helvetica-Bold")
    s_h3      = ParagraphStyle("H3",      parent=styles["Normal"], fontSize=11, textColor=C_ORANGE,  leading=15, spaceBefore=8,  fontName="Helvetica-Bold")
    s_body    = ParagraphStyle("Body",    parent=styles["Normal"], fontSize=9,  textColor=C_SLATE,   leading=13)
    s_gap     = ParagraphStyle("Gap",     parent=styles["Normal"], fontSize=9,  textColor=colors.HexColor("#8B1A00"), leading=13)
    s_ok      = ParagraphStyle("OK",      parent=styles["Normal"], fontSize=9,  textColor=colors.HexColor("#1A5C2A"), leading=13)
    s_caption = ParagraphStyle("Caption", parent=styles["Normal"], fontSize=8,  textColor=C_SLATE,   leading=11, alignment=TA_CENTER)

    story = []

    # ── Portada ─────────────────────────────────────────────────────────────
    cover_data = [[Paragraph(
        f'<font color="white"><b>REFERENCE EXAMPLE</b></font><br/>'
        f'<font color="#C14A1F" size="14"><b>Gap Assessment — Cierre de Minas</b></font>',
        ParagraphStyle("cov", fontSize=20, leading=30, alignment=TA_CENTER, fontName="Helvetica-Bold")
    )]]
    cover_tbl = Table(cover_data, colWidths=[17*cm])
    cover_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), C_DARK),
        ("TOPPADDING",    (0,0), (-1,-1), 28),
        ("BOTTOMPADDING", (0,0), (-1,-1), 28),
        ("LEFTPADDING",   (0,0), (-1,-1), 20),
        ("RIGHTPADDING",  (0,0), (-1,-1), 20),
        ("ROUNDEDCORNERS", [8]),
    ]))
    story.append(cover_tbl)
    story.append(Spacer(1, 0.6*cm))

    # Logo (if available)
    logo_path = Path(__file__).parent / "logo.jpeg"
    if logo_path.exists():
        img = Image(str(logo_path), width=5*cm, height=2.2*cm, kind="proportional")
        img.hAlign = "CENTER"
        story.append(img)
        story.append(Spacer(1, 0.3*cm))

    meta_data = [
        ["Empresa / Faena:", empresa or "—"],
        ["Responsable:",      responsable or "—"],
        ["Fecha de emisión:", date.today().strftime("%d/%m/%Y")],
        ["Herramienta:",      "Patricio Santos — Guía Cierre de Minas v1.0"],
    ]
    meta_tbl = Table(meta_data, colWidths=[5*cm, 12*cm])
    meta_tbl.setStyle(TableStyle([
        ("FONTNAME",    (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("TEXTCOLOR",   (0,0), (0,-1), C_DARK),
        ("TEXTCOLOR",   (1,0), (1,-1), C_SLATE),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [C_LIGHT, C_WHITE]),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 0.4*cm))
    story.append(HRFlowable(width="100%", thickness=2, color=C_ORANGE))
    story.append(Spacer(1, 0.4*cm))

    # ── Resumen ejecutivo ────────────────────────────────────────────────────
    story.append(Paragraph("1. Resumen ejecutivo", s_h2))

    total_cump  = sum(s[0] for s in scores.values())
    total_items = sum(s[1] for s in scores.values())
    pct_global  = (total_cump / total_items * 100) if total_items > 0 else 0

    if pct_global < 40:
        nivel = "CRÍTICO"; nivel_color = "#C14A1F"
        recomendacion = "Iniciar gap assessment estructurado y plan de cierre de brechas con carácter urgente."
    elif pct_global < 70:
        nivel = "INTERMEDIO"; nivel_color = "#8B6914"
        recomendacion = "Plan en curso con brechas significativas en ICMM/GISTM. Priorizar elementos faltantes."
    elif pct_global < 90:
        nivel = "AVANZADO"; nivel_color = "#1A5C2A"
        recomendacion = "Plan alineado. Afinar elementos pendientes y documentar buenas prácticas."
    else:
        nivel = "EXCELENCIA"; nivel_color = "#0A3D1A"
        recomendacion = "Plan dual-compliant. Mantener ciclo de mejora continua y auditorías periódicas."

    summary_data = [
        [Paragraph("<b>Indicador</b>", s_body), Paragraph("<b>Valor</b>", s_body)],
        ["Ítems cumplidos / Total",  f"{total_cump} / {total_items}"],
        ["Cumplimiento global",      f"{pct_global:.1f} %"],
        ["Nivel de madurez",         Paragraph(f'<font color="{nivel_color}"><b>{nivel}</b></font>', s_body)],
    ]
    for marco, (cump, total) in scores.items():
        pct = (cump / total * 100) if total > 0 else 0
        name = marco.split(" (")[0]
        summary_data.append([name, f"{cump}/{total}  ({pct:.0f} %)"])

    sum_tbl = Table(summary_data, colWidths=[10*cm, 7*cm])
    sum_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  C_DARK),
        ("TEXTCOLOR",     (0,0), (-1,0),  C_WHITE),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [C_LIGHT, C_WHITE]),
        ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#CCCCCC")),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
    ]))
    story.append(sum_tbl)
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"<b>Recomendación principal:</b> {recomendacion}", s_body))
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=C_ORANGE))

    # ── Detalle por marco ────────────────────────────────────────────────────
    story.append(Paragraph("2. Detalle de brechas por marco normativo", s_h2))

    checkbox_keys = {
        marco: {item: st.session_state.get(f"{marco}_{item}", False) for item in items}
        for marco, items in checklist_items.items()
    }

    for idx, (marco, items) in enumerate(checklist_items.items(), start=1):
        cump, total = scores[marco]
        pct = (cump / total * 100) if total > 0 else 0
        story.append(Paragraph(f"2.{idx}  {marco}  —  {cump}/{total} ({pct:.0f} %)", s_h3))

        rows = [[
            Paragraph("<b>#</b>", s_body),
            Paragraph("<b>Requisito</b>", s_body),
            Paragraph("<b>Estado</b>", s_body),
        ]]
        for i, item in enumerate(items, start=1):
            checked = checkbox_keys[marco].get(item, False)
            estado = Paragraph('<font color="#1A5C2A">✔ Cumplido</font>', s_body) if checked \
                     else Paragraph('<font color="#C14A1F">✘ Brecha</font>', s_body)
            rows.append([str(i), Paragraph(item, s_body), estado])

        detail_tbl = Table(rows, colWidths=[0.8*cm, 13.2*cm, 3*cm])
        detail_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),  C_SLATE),
            ("TEXTCOLOR",     (0,0), (-1,0),  C_WHITE),
            ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,-1), 8),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [C_LIGHT, C_WHITE]),
            ("GRID",          (0,0), (-1,-1), 0.3, colors.HexColor("#DDDDDD")),
            ("TOPPADDING",    (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("LEFTPADDING",   (0,0), (-1,-1), 6),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(detail_tbl)
        story.append(Spacer(1, 0.4*cm))

    story.append(HRFlowable(width="100%", thickness=1, color=C_ORANGE))

    # ── Brechas prioritarias ─────────────────────────────────────────────────
    story.append(Paragraph("3. Brechas prioritarias a cerrar", s_h2))
    gaps_found = False
    for marco, items in checklist_items.items():
        gaps = [item for item in items if not checkbox_keys[marco].get(item, False)]
        if gaps:
            gaps_found = True
            story.append(Paragraph(marco.split(" (")[0], s_h3))
            for g in gaps:
                story.append(Paragraph(f"• {g}", s_gap))
    if not gaps_found:
        story.append(Paragraph("Sin brechas detectadas. Nivel de excelencia alcanzado.", s_ok))

    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=C_ORANGE))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Este informe fue generado automáticamente por la herramienta interactiva en desarrollo. "
        "Los contenidos son de referencia general y no reemplazan la asesoría especializada.",
        s_caption,
    ))

    doc.build(story)
    return buffer.getvalue()


# =============================================================================
# DATOS — SERNAGEOMIN / Ley 20.551
# =============================================================================
CLASIFICACION_PLANES = [
    {
        "Categoría": "Exploraciones y prospecciones",
        "Capacidad (tpm)": "N/A (ingresan SEIA)",
        "Procedimiento": "Simplificado",
        "Nivel ingeniería": "Conceptual",
        "Auditoría externa": "No",
        "Guía SERNAGEOMIN": "Guía Planes de Cierre de Exploraciones y Prospecciones (2013)",
    },
    {
        "Categoría": "Declaración",
        "Capacidad (tpm)": "≤ 5.000",
        "Procedimiento": "Simplificado (formulario)",
        "Nivel ingeniería": "Básico",
        "Auditoría externa": "No",
        "Guía SERNAGEOMIN": "Guía Metodológica Declaración ≤ 5.000 tpm (2020)",
    },
    {
        "Categoría": "Plan simplificado",
        "Capacidad (tpm)": "> 5.000 y ≤ 10.000",
        "Procedimiento": "Simplificado — examen admisibilidad + fondo",
        "Nivel ingeniería": "Intermedio",
        "Auditoría externa": "No (salvo extraordinaria)",
        "Guía SERNAGEOMIN": "Guía Planes de Cierre 5.000–10.000 tpm (2014)",
    },
    {
        "Categoría": "Plan de aplicación general",
        "Capacidad (tpm)": "> 10.000",
        "Procedimiento": "Aplicación general",
        "Nivel ingeniería": "Detallada (informe vida útil Ley 20.235)",
        "Auditoría externa": "Sí — periódica cada 5 años + final + extraordinaria",
        "Guía SERNAGEOMIN": "Guía Presentación y Actualización Planes de Cierre Procedimiento General (2025)",
    },
]

CONTENIDOS_PLAN_GENERAL = [
    "1. Resumen Ejecutivo",
    "2. Índice",
    "3. Tipo de Plan de Cierre y sus modificaciones",
    "4. Descripción de la faena minera (identificación, ubicación, entorno, operación)",
    "5. Resumen de Resoluciones de Calificación Ambiental (RCAs)",
    "6. Informe de Vida Útil certificado por Persona Competente Ley 20.235",
    "7. Metodología de Evaluación de Riesgos (base ISO 31000)",
    "8. Descripción de las instalaciones a cerrar",
    "9. Evaluación de Riesgos por instalación",
    "10. Medidas y actividades de cierre propuestas (físicas, químicas, biológicas)",
    "11. Programación de ejecución del cierre",
    "12. Monitoreo y actividades de post-cierre",
    "13. Estabilidad física de instalaciones remanentes",
    "14. Estabilidad química y manejo de drenajes",
    "15. Garantías financieras (tasa BCU, VPT, cronograma de constitución)",
    "16. Información estratégica (patrimonio, monumentos, sitios de valor)",
    "17. Programa de difusión y participación",
    "18. Anexos técnicos (planos, modelos, cálculos)",
]

GUIAS_SERNAGEOMIN = [
    ("Guía Planes de Cierre Exploraciones y Prospecciones", 2013, "Simplificado"),
    ("Guía Planes de Cierre 5.000–10.000 tpm", 2014, "Simplificado"),
    ("Guía Evaluación de Riesgos para Cierre de Faenas (base ISO 31000)", 2014, "Ambos"),
    ("Guía Constitución y Disposición de Garantía Financiera", 2014, "Ambos"),
    ("Guía Metodológica Estabilidad Química", 2015, "Ambos"),
    ("Guía Metodológica Estabilidad Física (PUCV)", 2017, "Ambos"),
    ("Guía Metodológica Declaración Plan de Cierre ≤ 5.000 tpm", 2020, "Simplificado"),
    ("Guía Presentación Planes de Cierre Parcial", 2021, "General"),
    ("Guía Informe Vida Útil certificado por Persona Competente", 2023, "General"),
    ("Guía Presentación y Actualización Planes de Cierre Procedimiento General", 2025, "General"),
    ("Guía Presentación Programas e Informes de Auditorías (Aux. RPAE)", 2025, "General"),
    ("Guía SEA — Trámite PAS art. 137 Reglamento SEIA", 2020, "Ambos"),
]


# =============================================================================
# DATOS — ICMM Integrated Mine Closure Good Practice Guide (2019)
# =============================================================================
ICMM_ELEMENTOS = [
    {
        "N°": 1,
        "Elemento": "Integration into Life of Mine Planning",
        "Traducción": "Integración en la planificación del ciclo de vida",
        "Descripción": "El cierre debe integrarse en la planificación de corto, mediano y largo plazo de la mina desde las fases tempranas de exploración y desarrollo.",
        "Entregable típico": "Life-of-Mine (LoM) plan con capítulo de cierre integrado; closure planning milestones en el schedule maestro.",
        "Fase LoA": "Diseño y permisos → Operación",
    },
    {
        "N°": 2,
        "Elemento": "Knowledge Base",
        "Traducción": "Base de conocimiento",
        "Descripción": "Repositorio iterativo de información ambiental, social, geoquímica, operacional y regulatoria que alimenta todas las decisiones de cierre.",
        "Entregable típico": "Base de datos geoespacial, línea base ambiental, caracterización geoquímica, modelo conceptual del sitio.",
        "Fase LoA": "Todo el ciclo de vida",
    },
    {
        "N°": 3,
        "Elemento": "Closure Vision, Principles and Objectives",
        "Traducción": "Visión, principios y objetivos de cierre",
        "Descripción": "Definición temprana de la visión aspiracional del cierre, principios rectores (estabilidad física/química, cumplimiento, transición social) y objetivos medibles.",
        "Entregable típico": "Closure Vision Statement con objetivos SMART por dominio.",
        "Fase LoA": "Diseño y permisos",
    },
    {
        "N°": 4,
        "Elemento": "Post-closure Land Use",
        "Traducción": "Uso del suelo post-cierre",
        "Descripción": "Definición del uso futuro del terreno (agricultura, forestal, conservación, industrial, repurposing, recreación).",
        "Entregable típico": "Land use plan consensuado con stakeholders; criterios de capacidad de la tierra.",
        "Fase LoA": "Diseño → Operación",
    },
    {
        "N°": 5,
        "Elemento": "Engagement for Closure Plan Development",
        "Traducción": "Participación para el desarrollo del plan",
        "Descripción": "Proceso continuo de engagement con stakeholders internos y externos (comunidad, regulador, trabajadores, sociedad civil) para co-construir el plan.",
        "Entregable típico": "Stakeholder map, plan de engagement, registro de consultas y compromisos.",
        "Fase LoA": "Todo el ciclo de vida",
    },
    {
        "N°": 6,
        "Elemento": "Identifying and Assessing Risks and Opportunities",
        "Traducción": "Identificación y evaluación de riesgos y oportunidades",
        "Descripción": "Proceso formal de evaluación de riesgos físicos, sociales, económicos y ecológicos, más identificación proactiva de oportunidades de valor.",
        "Entregable típico": "Risk register, risk/opportunity matrix, análisis cuantitativo por dominio.",
        "Fase LoA": "Todo el ciclo de vida",
    },
    {
        "N°": 7,
        "Elemento": "Closure Activities",
        "Traducción": "Actividades de cierre",
        "Descripción": "Acciones concretas ejecutables: reperfilamiento, coberturas, tratamiento de aguas, revegetación, desmantelamiento, remediación.",
        "Entregable típico": "Diseños de ingeniería (conceptual → detallado); especificaciones técnicas por instalación.",
        "Fase LoA": "Operación → Cierre",
    },
    {
        "N°": 8,
        "Elemento": "Success Criteria",
        "Traducción": "Criterios de éxito",
        "Descripción": "Indicadores cuantitativos y cualitativos que definen cuándo el cierre se considera exitoso y permite el relinquishment.",
        "Entregable típico": "Tabla de criterios de éxito por dominio, con umbrales y métodos de medición.",
        "Fase LoA": "Diseño → Post-cierre",
    },
    {
        "N°": 9,
        "Elemento": "Progressive Closure",
        "Traducción": "Cierre progresivo",
        "Descripción": "Ejecución de actividades de cierre durante la operación para reducir pasivos, validar técnicas y generar aprendizajes.",
        "Entregable típico": "Programa de cierre progresivo integrado al plan minero anual.",
        "Fase LoA": "Operación",
    },
    {
        "N°": 10,
        "Elemento": "Social Transition",
        "Traducción": "Transición social",
        "Descripción": "Planificación de la transición económica y social de trabajadores y comunidades afectadas por el cese de operaciones.",
        "Entregable típico": "Plan de transición social, inversión social de legado, planes de reconversión laboral.",
        "Fase LoA": "Operación → Post-cierre",
    },
    {
        "N°": 11,
        "Elemento": "Closure Costs",
        "Traducción": "Costos de cierre",
        "Descripción": "Estimación iterativa de costos de cierre con clases AACE (de 5 a 1) actualizada periódicamente, base de las garantías financieras.",
        "Entregable típico": "Closure cost estimate class 5→1; input directo al cálculo de garantía financiera.",
        "Fase LoA": "Todo el ciclo de vida",
    },
    {
        "N°": 12,
        "Elemento": "Closure Execution Plan",
        "Traducción": "Plan de ejecución del cierre",
        "Descripción": "Documento operativo que detalla cronograma, recursos, responsabilidades y secuencia de implementación del cierre.",
        "Entregable típico": "Execution plan con WBS, Gantt, asignación de recursos y contingencias.",
        "Fase LoA": "Operación → Cierre",
    },
    {
        "N°": 13,
        "Elemento": "Monitoring, Maintenance and Management",
        "Traducción": "Monitoreo, mantenimiento y gestión",
        "Descripción": "Programa de monitoreo durante y después del cierre para verificar cumplimiento de criterios de éxito.",
        "Entregable típico": "Plan de monitoreo con parámetros, frecuencia, triggers y protocolos de acción correctiva.",
        "Fase LoA": "Cierre → Post-cierre",
    },
    {
        "N°": 14,
        "Elemento": "Relinquishment",
        "Traducción": "Relinquishment (entrega final)",
        "Descripción": "Transferencia formal del sitio a un tercero (Estado, comunidad, privado) una vez cumplidos los criterios de éxito.",
        "Entregable típico": "Documentación de cumplimiento de success criteria, transferencia legal, liberación de garantías.",
        "Fase LoA": "Post-cierre",
    },
    {
        "N°": 15,
        "Elemento": "Temporary or Sudden Closure",
        "Traducción": "Cierre temporal o repentino",
        "Descripción": "Planificación de escenarios de cierre no planificado (cese operaciones, quiebra, fuerza mayor) con medidas de contingencia.",
        "Entregable típico": "Sudden closure plan; análisis what-if escenarios.",
        "Fase LoA": "Todo el ciclo de vida",
    },
    {
        "N°": 16,
        "Elemento": "Closure Governance",
        "Traducción": "Gobernanza del cierre",
        "Descripción": "Estructura organizacional (comité de cierre, estándares corporativos, roles y responsabilidades) que asegura integración del cierre en la toma de decisiones.",
        "Entregable típico": "Closure governance charter, closure committee terms of reference.",
        "Fase LoA": "Todo el ciclo de vida",
    },
    {
        "N°": 17,
        "Elemento": "Stakeholder Engagement (cross-cutting)",
        "Traducción": "Engagement con stakeholders (transversal)",
        "Descripción": "Proceso transversal continuo con todos los grupos de interés, presente en todas las fases del ciclo de vida.",
        "Entregable típico": "Engagement strategy, registro de compromisos, grievance mechanism.",
        "Fase LoA": "Todo el ciclo de vida",
    },
]


# =============================================================================
# DATOS — GISTM 15 Principios (2020) agrupados en 6 Topics
# =============================================================================
GISTM_TOPICS = {
    "I. Affected Communities": [1],
    "II. Integrated Knowledge Base": [2, 3],
    "III. Design, Construction, Operation & Monitoring": [4, 5, 6, 7],
    "IV. Management and Governance": [8, 9, 10, 11, 12],
    "V. Emergency Response and Long-Term Recovery": [13, 14],
    "VI. Public Disclosure and Access to Information": [15],
}

GISTM_PRINCIPIOS = {
    1: {
        "title": "Respect the rights of project-affected people",
        "title_es": "Respetar los derechos de las personas afectadas por el proyecto",
        "summary": "Respetar derechos de las personas afectadas y engagement significativo en todas las fases del ciclo de vida de la instalación, incluyendo el cierre. Incluye derechos humanos, FPIC de pueblos indígenas, mecanismos de grievance operacionales.",
        "requirements_count": 4,
        "skills": "Socio-económico / comunidades",
        "ley_chile": "Consulta indígena Convenio 169 OIT; Ley 19.300 (participación ciudadana); PAC del SEIA.",
    },
    2: {
        "title": "Develop and maintain an interdisciplinary knowledge base",
        "title_es": "Desarrollar y mantener una base de conocimiento interdisciplinaria",
        "summary": "Base de conocimiento social, ambiental, económico y técnico del sitio. Actualización mínima cada 5 años o ante cambios materiales. Debe capturar incertidumbres climáticas.",
        "requirements_count": 5,
        "skills": "Ambiental + socio-económico + agua + geotécnico",
        "ley_chile": "Línea base del EIA/DIA; caracterización geoquímica y geotécnica en plan de cierre.",
    },
    3: {
        "title": "Use all elements of the knowledge base to inform decisions",
        "title_es": "Usar todos los elementos de la base de conocimiento en las decisiones",
        "summary": "Usar la base de conocimiento para informar todas las decisiones del ciclo de vida, incluyendo cierre. Incorporar cambio climático en evaluación de riesgos.",
        "requirements_count": 2,
        "skills": "Ambiental + agua + geotécnico + socio-económico",
        "ley_chile": "Actualización quinquenal del plan de cierre; informe de auditoría periódica.",
    },
    4: {
        "title": "Develop plans and design criteria to minimise risk",
        "title_es": "Desarrollar planes y criterios de diseño para minimizar riesgo",
        "summary": "Desarrollar criterios de diseño del depósito considerando clasificación de consecuencias (Low, Significant, High, Very High, Extreme). Revisión DSR cada 5 años. Aplicar criterios Extreme o mantener factibilidad de upgrade.",
        "requirements_count": 9,
        "skills": "Ingeniería geotécnica/civil",
        "ley_chile": "DS 248 Reglamento Depósitos de Relaves; Guía Estabilidad Física SERNAGEOMIN.",
    },
    5: {
        "title": "Develop a robust design that integrates the knowledge base",
        "title_es": "Desarrollar un diseño robusto que integre la base de conocimiento",
        "summary": "Diseño robusto multi-criterio que integre contexto técnico, social, ambiental y económico, considere clasificación de consecuencias y demuestre factibilidad de cierre seguro.",
        "requirements_count": 8,
        "skills": "Ingeniería multidisciplinaria (geotec, hidro, geoquímica, civil)",
        "ley_chile": "Diseños de ingeniería con nivel creciente según fase del plan (conceptual → detalle).",
    },
    6: {
        "title": "Plan, build and operate the facility to manage risk at all phases",
        "title_es": "Planificar, construir y operar la instalación para manejar riesgo en todas las fases",
        "summary": "Operación del depósito bajo Tailings Management System (TMS) y Environmental & Social Management System (ESMS). Manejo activo de agua, balance hídrico, monitoreo continuo.",
        "requirements_count": 8,
        "skills": "Operaciones + geotec + agua + ambiental",
        "ley_chile": "Manual operación DS 248; programas de seguimiento ambiental RCA.",
    },
    7: {
        "title": "Design, implement and operate monitoring systems",
        "title_es": "Diseñar, implementar y operar sistemas de monitoreo",
        "summary": "Sistema de vigilancia (surveillance) con instrumentación, inspecciones, análisis y reporte oportuno. Critical controls con owners definidos.",
        "requirements_count": 4,
        "skills": "Geotec + instrumentación",
        "ley_chile": "Programa de monitoreo geotécnico y geoquímico del plan de cierre.",
    },
    8: {
        "title": "Establish policies, systems and accountabilities",
        "title_es": "Establecer políticas, sistemas y rendición de cuentas",
        "summary": "Accountable Executive designado a nivel ejecutivo. Políticas corporativas de gestión de relaves. Responsible Tailings Facility Engineer (RTFE) designado por sitio.",
        "requirements_count": 3,
        "skills": "Gobernanza corporativa",
        "ley_chile": "No existe figura equivalente en normativa chilena — gap identificable.",
    },
    9: {
        "title": "Appoint an Engineer of Record (EOR)",
        "title_es": "Designar un Engineer of Record (EOR)",
        "summary": "Firma de ingeniería responsable de confirmar que el diseño, construcción y desmantelamiento cumplen los estándares. Puede delegar responsabilidad, no accountability.",
        "requirements_count": 1,
        "skills": "Ingeniería geotécnica",
        "ley_chile": "Figura no formalizada en Chile — equivalente parcial: firma responsable del proyecto ante SERNAGEOMIN.",
    },
    10: {
        "title": "Establish levels of review as part of a risk management system",
        "title_es": "Establecer niveles de revisión en el sistema de gestión de riesgos",
        "summary": "Independent Tailings Review Board (ITRB) para depósitos High/Very High/Extreme, cada 3 años como mínimo. Senior Independent Technical Reviewer (15+ años experiencia) para otros.",
        "requirements_count": 3,
        "skills": "Revisión independiente multidisciplinaria",
        "ley_chile": "No requerido por normativa chilena — gap. Incorporable como buena práctica voluntaria.",
    },
    11: {
        "title": "Develop an organisational culture that promotes learning",
        "title_es": "Desarrollar cultura organizacional de aprendizaje",
        "summary": "Cultura de aprendizaje, comunicación y reconocimiento temprano de problemas. Incorporar lecciones de incidentes internos y externos con foco en factores humanos y organizacionales.",
        "requirements_count": 4,
        "skills": "Gestión organizacional",
        "ley_chile": "Requisito indirecto del sistema de gestión de riesgos del plan de cierre.",
    },
    12: {
        "title": "Establish a process for reporting and addressing concerns",
        "title_es": "Proceso para reportar y abordar preocupaciones",
        "summary": "Mecanismo formal para que trabajadores, contratistas y comunidad puedan reportar preocupaciones sobre seguridad del depósito, con protección contra represalias.",
        "requirements_count": 2,
        "skills": "Socio-económico / RRHH",
        "ley_chile": "Ley del Trabajador; mecanismo de PAC/reclamos del SEA.",
    },
    13: {
        "title": "Prepare for emergency response",
        "title_es": "Prepararse para respuesta a emergencias",
        "summary": "Emergency Preparedness and Response Plan (EPRP) sitio-específico basado en escenarios creíbles de falla por flujo. Co-desarrollo con comunidades vulnerables. Drills periódicos.",
        "requirements_count": 4,
        "skills": "Gestión de emergencias / riesgo",
        "ley_chile": "Manual de emergencias del DS 248 (contenido k del PAS art.137).",
    },
    14: {
        "title": "Prepare for long-term recovery",
        "title_es": "Prepararse para recuperación de largo plazo",
        "summary": "Plan de recuperación de largo plazo tras un evento de falla, incluyendo restauración ambiental, compensación y retorno de comunidades.",
        "requirements_count": 2,
        "skills": "Ambiental + socio-económico + ingeniería",
        "ley_chile": "No existe requisito explícito — gap claro, incorporable como valor agregado.",
    },
    15: {
        "title": "Publicly disclose and provide access to information",
        "title_es": "Divulgación pública y acceso a información",
        "summary": "Divulgación pública de información material sobre seguridad e integridad del depósito. Transparencia con project-affected people. Participación en iniciativas de transparencia global.",
        "requirements_count": 3,
        "skills": "Comunicaciones + ambiental",
        "ley_chile": "Ley 20.285 sobre Acceso a Información Pública; publicaciones SERNAGEOMIN.",
    },
}


# =============================================================================
# CORRELACIÓN SERNAGEOMIN ↔ ICMM ↔ GISTM
# =============================================================================
CORRELACION = [
    {
        "Sección Plan de Cierre (SERNAGEOMIN)": "1. Resumen Ejecutivo",
        "Elemento ICMM": "Closure Vision, Principles and Objectives (3)",
        "Principio GISTM": "—",
        "Recomendación": "Incluir Closure Vision Statement explícito aunque el formato SERNAGEOMIN no lo exija.",
    },
    {
        "Sección Plan de Cierre (SERNAGEOMIN)": "4. Descripción de la faena y entorno",
        "Elemento ICMM": "Knowledge Base (2)",
        "Principio GISTM": "Principio 2 — Knowledge Base",
        "Recomendación": "Estructurar como base de conocimiento iterativa con línea base social + ambiental + técnica y plan de actualización quinquenal.",
    },
    {
        "Sección Plan de Cierre (SERNAGEOMIN)": "5. Resumen RCAs y compromisos ambientales",
        "Elemento ICMM": "Engagement for Closure Plan Development (5)",
        "Principio GISTM": "Principio 1 — Rights of PAP",
        "Recomendación": "Cruzar compromisos RCA con matriz de stakeholders ICMM y grievance mechanism GISTM.",
    },
    {
        "Sección Plan de Cierre (SERNAGEOMIN)": "6. Informe Vida Útil (Ley 20.235)",
        "Elemento ICMM": "Integration into LoM Planning (1) + Closure Costs (11)",
        "Principio GISTM": "—",
        "Recomendación": "Incluir escenarios de cierre temporal/repentino ICMM elemento 15 en el informe.",
    },
    {
        "Sección Plan de Cierre (SERNAGEOMIN)": "7. Metodología Evaluación de Riesgos (ISO 31000)",
        "Elemento ICMM": "Identifying Risks and Opportunities (6)",
        "Principio GISTM": "Principios 3, 4, 7",
        "Recomendación": "Usar Guía Metodológica Riesgos SERNAGEOMIN 2014 como base + matriz ICMM risk/opportunity + Consequence Classification GISTM Anexo 2.",
    },
    {
        "Sección Plan de Cierre (SERNAGEOMIN)": "8. Descripción de instalaciones",
        "Elemento ICMM": "Knowledge Base (2) — Domain model",
        "Principio GISTM": "Principio 2",
        "Recomendación": "Aplicar Tool 1 ICMM (Domain model) para estructurar instalaciones como closure domains.",
    },
    {
        "Sección Plan de Cierre (SERNAGEOMIN)": "9. Evaluación de Riesgos por instalación",
        "Elemento ICMM": "Identifying Risks and Opportunities (6)",
        "Principio GISTM": "Principios 4, 5, 7",
        "Recomendación": "Para depósitos de relaves, aplicar clasificación de consecuencias GISTM Anexo 2 además de la matriz SERNAGEOMIN.",
    },
    {
        "Sección Plan de Cierre (SERNAGEOMIN)": "10. Medidas y actividades de cierre",
        "Elemento ICMM": "Closure Activities (7) + Post-closure Land Use (4)",
        "Principio GISTM": "Principio 5",
        "Recomendación ": "Vincular medidas a success criteria cuantitativos (ICMM 8) y a uso post-cierre definido.",
    },
    {
        "Sección Plan de Cierre (SERNAGEOMIN)": "11. Programación de cierre",
        "Elemento ICMM": "Progressive Closure (9) + Closure Execution Plan (12)",
        "Principio GISTM": "Principio 6",
        "Recomendación": "Maximizar cierre progresivo para liberar garantías anticipadamente (Art. 28 Ley 20.551 + Principio GISTM 6).",
    },
    {
        "Sección Plan de Cierre (SERNAGEOMIN)": "12. Monitoreo y post-cierre",
        "Elemento ICMM": "Monitoring, Maintenance and Management (13)",
        "Principio GISTM": "Principio 7",
        "Recomendación": "Programa de monitoreo con triggers, thresholds y surveillance plan estilo GISTM.",
    },
    {
        "Sección Plan de Cierre (SERNAGEOMIN)": "13. Estabilidad física",
        "Elemento ICMM": "Closure Activities (7)",
        "Principio GISTM": "Principios 4, 5, 7",
        "Recomendación": "Incluir análisis de consecuencias para relaves bajo GISTM Anexo 2 (extreme post-closure loading).",
    },
    {
        "Sección Plan de Cierre (SERNAGEOMIN)": "14. Estabilidad química",
        "Elemento ICMM": "Closure Activities (7) + Knowledge Base (2)",
        "Principio GISTM": "Principio 6",
        "Recomendación": "Usar Guía Estabilidad Química SERNAGEOMIN 2015 + caracterización MEND / GARD Guide.",
    },
    {
        "Sección Plan de Cierre (SERNAGEOMIN)": "15. Garantías financieras",
        "Elemento ICMM": "Closure Costs (11)",
        "Principio GISTM": "—",
        "Recomendación": "Construir estimación AACE class 3 o mejor; considerar liberaciones vía cierre progresivo y crédito art. 50 DGA.",
    },
    {
        "Sección Plan de Cierre (SERNAGEOMIN)": "16. Información estratégica",
        "Elemento ICMM": "Post-closure Land Use (4)",
        "Principio GISTM": "Principio 15",
        "Recomendación": "Divulgación pública alineada a Ley 20.285 + requisitos GISTM 15.",
    },
    {
        "Sección Plan de Cierre (SERNAGEOMIN)": "17. Programa de difusión",
        "Elemento ICMM": "Stakeholder Engagement (17) + Social Transition (10)",
        "Principio GISTM": "Principios 1, 12, 15",
        "Recomendación": "Incluir grievance mechanism UNGP-compliant y plan de transición social estilo ICMM cap. 11.",
    },
    {
        "Sección Plan de Cierre (SERNAGEOMIN)": "(Transversal) Gobernanza del cierre",
        "Elemento ICMM": "Closure Governance (16)",
        "Principio GISTM": "Principios 8, 9, 10, 11",
        "Recomendación": "Proponer Accountable Executive + RTFE + ITRB como buenas prácticas voluntarias (gap vs. normativa chilena).",
    },
]


# =============================================================================
# ROADMAP DE CUMPLIMIENTO
# =============================================================================
ROADMAP = [
    {
        "Fase": "0. Diagnóstico",
        "Duración": "1–2 meses",
        "Actividades clave": [
            "Gap assessment Ley 20.551 vs ICMM GPG vs GISTM",
            "Inventario de instalaciones y clasificación por procedimiento (tpm)",
            "Revisión documental: RCAs, permisos sectoriales, plan de cierre vigente",
            "Mapa de stakeholders y análisis de contexto social",
        ],
        "Entregable": "Informe de brechas con priorización de acciones",
    },
    {
        "Fase": "1. Planificación",
        "Duración": "3–6 meses",
        "Actividades clave": [
            "Definir Closure Vision, principios y objetivos (ICMM 3)",
            "Estructurar knowledge base (ICMM 2 / GISTM 2)",
            "Definir uso post-cierre consensuado (ICMM 4)",
            "Plan de engagement y grievance mechanism (ICMM 5 / GISTM 1, 12)",
            "Estimación preliminar de costos clase 5/4 (ICMM 11)",
        ],
        "Entregable": "Plan de cierre conceptual + charter de gobernanza",
    },
    {
        "Fase": "2. Diseño e ingeniería",
        "Duración": "6–12 meses",
        "Actividades clave": [
            "Evaluación de riesgos ISO 31000 + consequence classification GISTM",
            "Diseño de medidas de cierre (ICMM 7) nivel pre-factibilidad",
            "Definir success criteria por dominio (ICMM 8)",
            "Análisis de estabilidad física y química (SERNAGEOMIN)",
            "Designación EOR y ITRB/STR (GISTM 9, 10)",
        ],
        "Entregable": "Plan de cierre de ingeniería (pre-factibilidad/factibilidad)",
    },
    {
        "Fase": "3. Aprobación regulatoria",
        "Duración": "6–18 meses",
        "Actividades clave": [
            "Ingreso a SEA (PAS 137) si aplica",
            "Presentación formal ante SERNAGEOMIN",
            "Constitución inicial de garantía financiera (20% VPT primer año)",
            "Revisión de examen admisibilidad y fondo",
            "Respuesta a observaciones ICE/ICSARA",
        ],
        "Entregable": "Resolución aprobatoria SERNAGEOMIN",
    },
    {
        "Fase": "4. Implementación progresiva",
        "Duración": "Vida útil restante",
        "Actividades clave": [
            "Ejecutar cierre progresivo por dominios (ICMM 9)",
            "Actualización quinquenal de plan y riesgos (GISTM 3)",
            "Auditorías periódicas cada 5 años por auditor RPAE (Ley 20.551 art. 18)",
            "Monitoreo continuo y reporte a stakeholders (ICMM 13)",
            "Ajuste de garantía por progresivo y cierres parciales (Art. 28)",
        ],
        "Entregable": "Informes anuales + auditorías quinquenales",
    },
    {
        "Fase": "5. Cierre final",
        "Duración": "1–3 años post-operación",
        "Actividades clave": [
            "Ejecución de medidas de cierre final",
            "Plan de transición social y workforce (ICMM 10)",
            "Auditoría final Ley 20.551",
            "Verificación de cumplimiento de success criteria",
            "Desmovilización de garantías conforme a liberaciones aprobadas",
        ],
        "Entregable": "Certificado de cierre final SERNAGEOMIN",
    },
    {
        "Fase": "6. Post-cierre y relinquishment",
        "Duración": "5–30+ años",
        "Actividades clave": [
            "Monitoreo y mantenimiento post-cierre (ICMM 13)",
            "Gestión de medidas perpetuas (ej. tratamiento drenaje ácido)",
            "Preparación para relinquishment (ICMM 14)",
            "Transferencia formal a tercero o Estado",
            "Liberación total de garantías",
        ],
        "Entregable": "Relinquishment formal + cierre administrativo",
    },
]


# =============================================================================
# NAVEGACIÓN
# =============================================================================
PAGES = {
    "🏠 Inicio": "inicio",
    "📜 Marco regulatorio Chile": "sernageomin",
    "🌍 ICMM Integrated Mine Closure": "icmm",
    "🏔️ GISTM Global Tailings Standard": "gistm",
    "🔗 Matriz de correlación": "correlacion",
    "🗺️ Roadmap de cumplimiento": "roadmap",
    "✅ Checklist + Gap Assessment PDF": "checklist",
    "💰 Calculadora de Garantía": "garantia",
    "📍 Auditorías 2026 — Lead Tracker": "auditorias",
    "📚 Referencias y descargas": "referencias",
}

with st.sidebar:
    st.markdown(
        f'<div style="background:{BRAND_DARK};border-radius:10px;padding:10px 14px;'
        f'margin-bottom:2px;">'
        f'<span style="color:#aab0bb;font-size:0.68rem;letter-spacing:0.5px;">'
        f'Patricio Santos</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("### Navegación")
    page_name = st.radio(
        "Ir a:",
        list(PAGES.keys()),
        label_visibility="collapsed",
    )
    page = PAGES[page_name]
    st.markdown("---")
    st.caption(
        "Guía interactiva del estado del arte en cierre de minas. "
        "Integra SERNAGEOMIN Ley 20.551, ICMM 2019 e ICMM-GISTM 2020."
    )
    st.caption("Patricio Santos · v1.0")


# =============================================================================
# PÁGINA: INICIO
# =============================================================================
if page == "inicio":

    # ── Hero banner — estilo landing web ────────────────────────────────────
    st.markdown(
        f"""
        <div style="
            width:100%;
            background:linear-gradient(135deg, {BRAND_DARK} 0%, #243547 55%, {BRAND_SLATE} 100%);
            border-radius:16px;
            padding:64px 48px 56px 48px;
            margin-bottom:0;
            box-shadow:0 12px 40px rgba(0,0,0,0.35);
            position:relative;
            overflow:hidden;
            text-align:center;
        ">
          <!-- Círculos decorativos de fondo -->
          <div style="
              position:absolute; top:-60px; right:-60px;
              width:280px; height:280px; border-radius:50%;
              background:radial-gradient(circle, {BRAND_ORANGE} 0%, transparent 70%);
              opacity:0.08;
          "></div>
          <div style="
              position:absolute; bottom:-80px; left:-40px;
              width:320px; height:320px; border-radius:50%;
              background:radial-gradient(circle, #4A9E6A 0%, transparent 70%);
              opacity:0.07;
          "></div>

          <!-- Contenido -->
          <p style="
              color:{BRAND_ORANGE}; font-weight:700; font-size:0.78rem;
              letter-spacing:4px; text-transform:uppercase;
              margin:0 0 16px 0;
          ">Marco regulatorio, estandares y mejores prácticas · Patricio Santos</p>

          <h1 style="
              color:white; font-size:2.6rem; font-weight:800;
              line-height:1.15; margin:0 0 18px 0;
              letter-spacing:-0.5px;
          ">
            Guía Interactiva de<br>
            <span style="color:{BRAND_ORANGE};">Cierre de Minas</span>
          </h1>

          <p style="
              color:#B0C0CC; font-size:1.05rem; margin:0 auto 28px auto;
              max-width:600px; line-height:1.65;
          ">
            Integra el marco regulatorio chileno <strong style="color:white;">Ley 20.551</strong>,
            los 17 elementos <strong style="color:white;">ICMM 2019</strong>
            y los 15 principios <strong style="color:white;">GISTM 2020</strong>
            en una sola herramienta de trabajo.
          </p>

          <!-- Badges -->
          <div style="display:flex; gap:10px; justify-content:center; flex-wrap:wrap;">
            <span style="background:rgba(193,74,31,0.2); color:#E8856A; border:1px solid rgba(193,74,31,0.4);
                         padding:5px 14px; border-radius:20px; font-size:0.8rem; font-weight:600;">
              📜 Ley 20.551 · DS 41/2012
            </span>
            <span style="background:rgba(255,255,255,0.08); color:#C4D0DA; border:1px solid rgba(255,255,255,0.15);
                         padding:5px 14px; border-radius:20px; font-size:0.8rem; font-weight:600;">
              🌍 ICMM 2019 · 17 elementos
            </span>
            <span style="background:rgba(74,158,106,0.15); color:#7DC99A; border:1px solid rgba(74,158,106,0.35);
                         padding:5px 14px; border-radius:20px; font-size:0.8rem; font-weight:600;">
              🏔️ GISTM 2020 · 77 requisitos
            </span>
          </div>
        </div>

        <!-- Divisor terrain -->
        <svg viewBox="0 0 1440 36" xmlns="http://www.w3.org/2000/svg"
             style="display:block;width:100%;margin-top:-2px;margin-bottom:20px;">
          <path d="M0,36 L0,18 Q120,2 240,16 Q360,30 480,12 Q600,0 720,14
                   Q840,28 960,10 Q1080,0 1200,18 Q1320,34 1440,16 L1440,36 Z"
                fill="{BRAND_SLATE}" opacity="0.3"/>
          <path d="M0,36 L0,26 Q180,8 360,24 Q540,36 720,20
                   Q900,6 1080,22 Q1260,36 1440,24 L1440,36 Z"
                fill="{BRAND_ORANGE}" opacity="0.15"/>
        </svg>
        """,
        unsafe_allow_html=True,
    )

    # ── Módulos — fila 1: marcos regulatorios ────────────────────────────────
    st.markdown(
        f'<p style="color:{BRAND_SLATE};font-size:0.75rem;font-weight:700;letter-spacing:2px;'
        f'text-transform:uppercase;margin-bottom:10px;">Marcos normativos y estándares</p>',
        unsafe_allow_html=True,
    )

    # SVG icons mine-closure themed (inline, scalable)
    SVG_SERNAGEOMIN = """<svg viewBox="0 0 48 48" width="38" height="38" xmlns="http://www.w3.org/2000/svg">
      <rect x="4" y="30" width="40" height="14" rx="3" fill="#1F2E3D"/>
      <polygon points="24,4 8,30 40,30" fill="#C14A1F"/>
      <rect x="20" y="32" width="8" height="12" fill="#4A5A6A"/>
    </svg>"""

    SVG_ICMM = """<svg viewBox="0 0 48 48" width="38" height="38" xmlns="http://www.w3.org/2000/svg">
      <circle cx="24" cy="24" r="20" fill="none" stroke="#1F2E3D" stroke-width="2.5"/>
      <path d="M10,34 Q18,10 24,20 Q30,30 38,14" fill="none" stroke="#C14A1F" stroke-width="2.5" stroke-linecap="round"/>
      <circle cx="24" cy="24" r="3.5" fill="#C14A1F"/>
    </svg>"""

    SVG_GISTM = """<svg viewBox="0 0 48 48" width="38" height="38" xmlns="http://www.w3.org/2000/svg">
      <rect x="4" y="18" width="40" height="22" rx="3" fill="#1F2E3D"/>
      <path d="M4,20 Q12,8 20,16 Q28,24 36,10 Q40,5 44,12" fill="none" stroke="#C14A1F" stroke-width="2.5" stroke-linecap="round"/>
      <path d="M4,38 L44,38" stroke="#4A5A6A" stroke-width="1"/>
      <rect x="10" y="28" width="5" height="10" fill="#4A9E6A" rx="1"/>
      <rect x="20" y="24" width="5" height="14" fill="#4A9E6A" rx="1"/>
      <rect x="30" y="30" width="5" height="8" fill="#C14A1F" rx="1"/>
    </svg>"""

    SVG_CORR = """<svg viewBox="0 0 48 48" width="38" height="38" xmlns="http://www.w3.org/2000/svg">
      <rect x="4" y="4" width="18" height="18" rx="3" fill="#1F2E3D"/>
      <rect x="26" y="4" width="18" height="18" rx="3" fill="#C14A1F" opacity="0.8"/>
      <rect x="4" y="26" width="18" height="18" rx="3" fill="#4A5A6A"/>
      <rect x="26" y="26" width="18" height="18" rx="3" fill="#1F2E3D" opacity="0.6"/>
      <line x1="22" y1="13" x2="26" y2="13" stroke="white" stroke-width="2"/>
      <line x1="13" y1="22" x2="13" y2="26" stroke="white" stroke-width="2"/>
    </svg>"""

    SVG_ROADMAP = """<svg viewBox="0 0 48 48" width="38" height="38" xmlns="http://www.w3.org/2000/svg">
      <path d="M6,40 Q14,28 22,32 Q30,36 38,20 L42,10" fill="none" stroke="#1F2E3D" stroke-width="3" stroke-linecap="round"/>
      <circle cx="6"  cy="40" r="4" fill="#4A5A6A"/>
      <circle cx="22" cy="32" r="4" fill="#4A9E6A"/>
      <circle cx="38" cy="20" r="4" fill="#C14A1F"/>
      <circle cx="42" cy="10" r="4" fill="#1F2E3D"/>
    </svg>"""

    SVG_CHECKLIST = """<svg viewBox="0 0 48 48" width="38" height="38" xmlns="http://www.w3.org/2000/svg">
      <rect x="6" y="4" width="36" height="40" rx="4" fill="#F4F6F8" stroke="#1F2E3D" stroke-width="2"/>
      <line x1="14" y1="16" x2="34" y2="16" stroke="#4A5A6A" stroke-width="2"/>
      <line x1="14" y1="24" x2="34" y2="24" stroke="#4A5A6A" stroke-width="2"/>
      <line x1="14" y1="32" x2="26" y2="32" stroke="#4A5A6A" stroke-width="2"/>
      <path d="M28,28 L32,34 L40,22" fill="none" stroke="#4A9E6A" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>"""

    SVG_GARANTIA = """<svg viewBox="0 0 48 48" width="38" height="38" xmlns="http://www.w3.org/2000/svg">
      <path d="M24,4 L40,10 L40,28 Q40,40 24,46 Q8,40 8,28 L8,10 Z" fill="#1F2E3D"/>
      <path d="M24,10 L34,14 L34,28 Q34,36 24,40 Q14,36 14,28 L14,14 Z" fill="#C14A1F" opacity="0.7"/>
      <path d="M17,26 L22,31 L31,19" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>"""

    SVG_AUDIT = """<svg viewBox="0 0 48 48" width="38" height="38" xmlns="http://www.w3.org/2000/svg">
      <circle cx="20" cy="20" r="14" fill="none" stroke="#1F2E3D" stroke-width="3"/>
      <line x1="30" y1="30" x2="42" y2="42" stroke="#C14A1F" stroke-width="3.5" stroke-linecap="round"/>
      <line x1="14" y1="20" x2="26" y2="20" stroke="#4A9E6A" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="20" y1="14" x2="20" y2="26" stroke="#4A9E6A" stroke-width="2.5" stroke-linecap="round"/>
    </svg>"""

    def feature_card(svg_icon, title, description, accent=BRAND_ORANGE):
        return f"""
        <div style="
            background:white;
            border:1px solid #E1E8F0;
            border-top: 3px solid {accent};
            border-radius:10px;
            padding:18px 16px 16px 16px;
            height:100%;
            box-shadow:0 2px 8px rgba(31,46,61,0.07);
            transition:box-shadow 0.2s;
        ">
          <div style="margin-bottom:10px;">{svg_icon}</div>
          <h4 style="color:{BRAND_DARK};margin:0 0 7px 0;font-size:0.95rem;font-weight:700;">{title}</h4>
          <p style="color:{BRAND_SLATE};margin:0;font-size:0.83rem;line-height:1.55;">{description}</p>
        </div>"""

    r1 = st.columns(3)
    r1[0].markdown(feature_card(SVG_SERNAGEOMIN, "Marco Regulatorio Chile",
        "Ley 20.551, DS 41/2012, clasificación de planes por tpm, garantías financieras, auditorías RPAE y las 12 guías metodológicas de SERNAGEOMIN."), unsafe_allow_html=True)
    r1[1].markdown(feature_card(SVG_ICMM, "ICMM 2019 — 17 Elementos",
        "Integrated Mine Closure Good Practice Guide: cada elemento con descripción, entregables típicos y fase del Life of Asset correspondiente."), unsafe_allow_html=True)
    r1[2].markdown(feature_card(SVG_GISTM, "GISTM 2020 — 15 Principios",
        "Global Industry Standard on Tailings Management: 77 requisitos auditables organizados en 6 tópicos, con referencia cruzada a la normativa chilena."), unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    r2 = st.columns(3)
    r2[0].markdown(feature_card(SVG_CORR, "Matriz de Correlación",
        "Cruza cada sección del plan SERNAGEOMIN con el elemento ICMM y el principio GISTM correspondiente, con recomendaciones de incorporación concretas.",
        accent="#4A5A6A"), unsafe_allow_html=True)
    r2[1].markdown(feature_card(SVG_ROADMAP, "Roadmap de Cumplimiento",
        "7 fases desde el diagnóstico inicial hasta el relinquishment, con actividades clave y entregables formales por cada etapa del ciclo de vida.",
        accent="#4A5A6A"), unsafe_allow_html=True)
    r2[2].markdown(feature_card(SVG_CHECKLIST, "Checklist + Gap Assessment PDF",
        "Autoevalúa tu plan contra los tres marcos, obtén tu score de cumplimiento y descarga un informe PDF.",
        accent="#4A9E6A"), unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    r3 = st.columns(3)
    r3[0].markdown(feature_card(SVG_GARANTIA, "Calculadora de Garantía",
        "Proyecta el cronograma de constitución según DS 41/2012, visualiza el efecto de cierres progresivos y descarga la tabla UF año a año.",
        accent=BRAND_ORANGE), unsafe_allow_html=True)
    r3[1].markdown(feature_card(SVG_AUDIT, "Auditorías 2026 — Lead Tracker",
        "Pipeline comercial con las 20 faenas levantadas, mapeadas geográficamente sobre Chile con estado, prioridad, contacto y próximo paso editable.",
        accent=BRAND_ORANGE), unsafe_allow_html=True)
    r3[2].markdown(
        f"""<div style="
            background:linear-gradient(135deg,{BRAND_DARK} 0%,{BRAND_SLATE} 100%);
            border-radius:10px;padding:18px 16px;height:100%;
            box-shadow:0 2px 8px rgba(31,46,61,0.15);
        ">
          <p style="color:{BRAND_ORANGE};font-weight:700;font-size:0.72rem;letter-spacing:2px;
                    text-transform:uppercase;margin:0 0 12px 0;">Patricio Santos</p>
          <div style="display:flex;gap:20px;flex-wrap:wrap;margin-bottom:12px;">
            <div style="text-align:center;">
              <div style="color:white;font-size:1.6rem;font-weight:800;line-height:1;">3</div>
              <div style="color:#8A9AAA;font-size:0.72rem;">marcos</div>
            </div>
            <div style="text-align:center;">
              <div style="color:{BRAND_ORANGE};font-size:1.6rem;font-weight:800;line-height:1;">17</div>
              <div style="color:#8A9AAA;font-size:0.72rem;">elementos ICMM</div>
            </div>
            <div style="text-align:center;">
              <div style="color:white;font-size:1.6rem;font-weight:800;line-height:1;">15</div>
              <div style="color:#8A9AAA;font-size:0.72rem;">principios GISTM</div>
            </div>
            <div style="text-align:center;">
              <div style="color:{BRAND_ORANGE};font-size:1.6rem;font-weight:800;line-height:1;">77</div>
              <div style="color:#8A9AAA;font-size:0.72rem;">requisitos audit.</div>
            </div>
          </div>
          <p style="color:#8A9AAA;font-size:0.78rem;margin:0;line-height:1.5;">
            Consultoría especializada en cierre de minas y gestión de pasivos ambientales — Chile.
          </p>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── Terrain cross-section visual + callout ────────────────────────────────
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <svg viewBox="0 0 900 60" xmlns="http://www.w3.org/2000/svg"
             style="width:100%;display:block;margin-bottom:-4px;">
          <defs>
            <linearGradient id="terr" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="{BRAND_SLATE}" stop-opacity="0.25"/>
              <stop offset="100%" stop-color="{BRAND_DARK}" stop-opacity="0.9"/>
            </linearGradient>
          </defs>
          <!-- Strata layers -->
          <path d="M0,40 Q100,20 200,35 Q300,50 450,28 Q600,10 750,32 Q840,45 900,30 L900,60 L0,60 Z"
                fill="{BRAND_SLATE}" opacity="0.2"/>
          <path d="M0,50 Q150,38 300,48 Q450,58 600,42 Q750,30 900,46 L900,60 L0,60 Z"
                fill="{BRAND_ORANGE}" opacity="0.15"/>
          <path d="M0,58 Q200,50 450,56 Q700,60 900,54 L900,60 L0,60 Z"
                fill="{BRAND_DARK}" opacity="0.5"/>
          <!-- Vegetation dots -->
          <circle cx="80"  cy="38" r="3" fill="#4A9E6A" opacity="0.7"/>
          <circle cx="160" cy="32" r="4" fill="#4A9E6A" opacity="0.6"/>
          <circle cx="310" cy="45" r="3" fill="#4A9E6A" opacity="0.5"/>
          <circle cx="520" cy="25" r="5" fill="#4A9E6A" opacity="0.65"/>
          <circle cx="680" cy="29" r="3" fill="#4A9E6A" opacity="0.6"/>
          <circle cx="820" cy="42" r="4" fill="#4A9E6A" opacity="0.5"/>
        </svg>
        <div style="
            background:linear-gradient(135deg, {BRAND_DARK} 0%, #162230 100%);
            border-left:4px solid {BRAND_ORANGE};
            padding:16px 22px; border-radius:0 8px 8px 0;
        ">
          <span style="color:{BRAND_ORANGE};font-weight:700;font-size:0.8rem;
                       letter-spacing:1px;text-transform:uppercase;">Uso recomendado</span>
          <p style="color:#C4D0DA;margin:6px 0 0 0;font-size:0.88rem;line-height:1.6;">
            Diseñada para <strong style="color:white;">consultores, auditores RPAE, gerentes de sustentabilidad y equipos regulatorios</strong>.
            Úsala para orientar la elaboración de planes de cierre nuevos, la actualización quinquenal de planes existentes,
            o auditorías periódicas bajo <strong style="color:white;">Ley 20.551</strong>.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# PÁGINA: SERNAGEOMIN
# =============================================================================
elif page == "sernageomin":
    render_header("Marco regulatorio chileno — Ley 20.551")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Clasificación de planes", "Contenidos plan general", "Garantías financieras", "Auditorías RPAE", "Guías metodológicas"]
    )

    with tab1:
        st.markdown("### Clasificación de planes de cierre según capacidad productiva")
        st.markdown(
            "La Ley 20.551 divide los planes de cierre en **dos procedimientos** según la capacidad de "
            "extracción o beneficio mensual de mineral bruto. Esta clasificación determina el nivel de "
            "ingeniería exigido, el plazo de revisión, la obligación de auditoría externa y la magnitud "
            "de la garantía financiera."
        )
        df_clas = pd.DataFrame(CLASIFICACION_PLANES)
        st.dataframe(df_clas, use_container_width=True, hide_index=True)

        st.markdown(
            f"""
        <div class="callout">
        <b>Nota importante:</b> Las faenas preexistentes a noviembre de 2012 con capacidad ≤ 10.000 tpm
        mantienen vigente su plan de cierre aprobado bajo el antiguo Título X del Reglamento de Seguridad
        Minera hasta que experimenten una <i>modificación sustancial</i>. Esto genera un stock latente
        de actualizaciones.
        </div>
        """,
            unsafe_allow_html=True,
        )

    with tab2:
        st.markdown("### Contenidos mínimos del Plan de Cierre — Procedimiento General (> 10.000 tpm)")
        st.markdown("Según la Guía Metodológica SERNAGEOMIN 2025:")
        for seccion in CONTENIDOS_PLAN_GENERAL:
            st.markdown(f"- {seccion}")

    with tab3:
        st.markdown("### Garantías financieras (Art. 3 letra j Ley 20.551)")
        st.markdown(
            "La garantía financiera es la caución que el titular debe constituir ante SERNAGEOMIN "
            "para asegurar al Estado la ejecución íntegra del plan de cierre y post-cierre."
        )

        st.markdown("#### Fórmula oficial de cálculo")
        st.latex(r"C_i = VPT_i \times 0{,}2 + VPT_i \times 0{,}8 \times \frac{i-1}{N-1} \quad \text{para } i \leq N")
        st.latex(r"C_i = VPT_i \quad \text{para } i > N")

        st.markdown(
            """
        Donde:
        - $C_i$ = Garantía para el año $i$ del proyecto
        - $VPT_i$ = Valor Presente del costo de cierre de la faena al año $i$
        - $N$ = Plazo de disposición (años desde inicio de operación hasta término de operación)
        - Tasa de descuento = Tasa BCU (Banco Central, bonos en UF)
        """
        )

        st.markdown("#### Instrumentos admisibles")
        st.markdown(
            """
        - Boletas bancarias de garantía a la vista (USD, CLP, UF o EUR)
        - Cartas de crédito standby
        - Bonos, depósitos a plazo, seguros de garantía
        - Prendas sobre flujos futuros calificables por el Servicio
        - Beneficiario: **Servicio Nacional de Geología y Minería** (RUT 61.702.000-9)
        """
        )

        st.markdown("#### Mecanismos de liberación (Art. 28)")
        st.markdown(
            """
        - **Cierre parcial ejecutado y certificado**: liberación proporcional del 100% del valor de cada medida.
        - **Liberación adicional hasta 30%** del valor enterado al completar hitos significativos.
        - **Garantía mínima remanente**: 40% del valor total del plan hasta cierre final.
        - **Crédito art. 50**: rebaja cuando existen garantías ante DGA por obras hidráulicas.
        """
        )

    with tab4:
        st.markdown("### Auditorías externas — Registro Público de Auditores Externos (RPAE)")
        st.markdown(
            """
        **Ley 20.551, Título IV · DS 41/2012, Título IV**
        
        Todas las faenas bajo procedimiento de aplicación general (> 10.000 tpm) deben auditar su plan
        de cierre **cada 5 años**, a su costo, según el programa anual publicado por SERNAGEOMIN en el
        Diario Oficial en enero.
        """
        )

        st.markdown("#### Tipos de auditoría")
        st.markdown(
            """
        | Tipo | Cuándo | Base legal |
        |---|---|---|
        | Periódica | Cada 5 años según programa SERNAGEOMIN | Art. 18 Ley |
        | Final | Al término de ejecución del plan total | Art. 19 Ley |
        | Extraordinaria | Ordenada por el Servicio ante problemas graves | Art. 19 Ley |
        | Voluntaria | A iniciativa del titular | Art. 19 Ley |
        """
        )

        st.markdown("#### Requisitos para inscripción en el RPAE")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Persona natural**")
            st.markdown(
                """
            - Título profesional en ciencias vinculadas a minería (ingeniería de minas, geología, etc.)
            - **Mínimo 10 años** de experiencia en industria minera acreditada
            - No estar acusado ni condenado por delito con pena aflictiva
            - Declaración jurada de veracidad
            - Autorización notarial para verificación de antecedentes
            """
            )
        with c2:
            st.markdown("**Persona jurídica (EAE)**")
            st.markdown(
                """
            - Sociedad constituida conforme a ley chilena (SpA, EIRL, Ltda., S.A.)
            - Objeto social debe incluir auditorías de planes de cierre
            - Profesionales integrantes con 10+ años de experiencia minera
            - Ningún socio ni trabajador con condenas por pena aflictiva
            - Certificado Dirección del Trabajo (no condenas antisindicales, sin deudas previsionales)
            - Poderes vigentes del representante legal
            """
            )

    with tab5:
        st.markdown("### Guías metodológicas vigentes de SERNAGEOMIN")
        df_guias = pd.DataFrame(GUIAS_SERNAGEOMIN, columns=["Guía", "Año", "Aplicable a"])
        st.dataframe(df_guias, use_container_width=True, hide_index=True)
        st.caption("Fuente: www.sernageomin.cl/ambiental-cierre")


# =============================================================================
# PÁGINA: ICMM
# =============================================================================
elif page == "icmm":
    render_header("ICMM Integrated Mine Closure Good Practice Guide (2019)")

    st.markdown(
        """
    El **International Council on Mining and Metals (ICMM)** publicó en 2019 la segunda edición de su
    guía de buenas prácticas para cierre integrado de minas. Presenta 17 elementos que deben integrarse
    iterativamente a lo largo del ciclo de vida de la mina (*Life of Asset*), desde diseño y permisos
    hasta post-cierre y relinquishment.
    """
    )

    st.markdown("### Framework del ciclo de vida")
    st.markdown(
        """
    ```
    Diseño & permisos → Construcción → Operación + cierre progresivo → Cierre → Post-cierre → Relinquishment
                         ↑                                                                    ↑
                         └────────── Stakeholder engagement (transversal) ──────────────────┘
                         └────────── Planning & implementing social transition ─────────────┘
    ```
    """
    )

    st.markdown("### Los 17 elementos del cierre integrado")

    # Filtros
    col_f1, col_f2 = st.columns([2, 3])
    with col_f1:
        fases_unicas = sorted(set(e["Fase LoA"] for e in ICMM_ELEMENTOS))
        fase_filtro = st.multiselect("Filtrar por fase del Life of Asset:", fases_unicas, default=fases_unicas)

    elementos_filtrados = [e for e in ICMM_ELEMENTOS if e["Fase LoA"] in fase_filtro]

    for elem in elementos_filtrados:
        with st.expander(f"**{elem['N°']}. {elem['Elemento']}** — {elem['Traducción']}", expanded=False):
            st.markdown(f"**Descripción:** {elem['Descripción']}")
            st.markdown(f"**Entregable típico:** {elem['Entregable típico']}")
            st.markdown(f"**Fase del Life of Asset:** `{elem['Fase LoA']}`")

    st.markdown("---")
    st.markdown("### Herramientas (Tools) incluidas en la guía ICMM 2019")
    tools = [
        ("Tool 1", "The domain model"),
        ("Tool 2", "Monitoring, measurement and inspections"),
        ("Tool 3", "Objective setting"),
        ("Tool 4", "Screening alternatives for repurposing"),
        ("Tool 5", "Key messages for social transition"),
        ("Tool 6", "Social transition activities checklist"),
        ("Tool 7", "Climate change and mine closure concerns"),
        ("Tool 8", "Risk/opportunity assessment and management"),
        ("Tool 9", "Closure activities for transversal issues"),
        ("Tool 10", "Closure activities for domain-specific issues"),
        ("Tool 11", "Social investment for closure"),
        ("Tool 12", "Closure plan documentation"),
    ]
    df_tools = pd.DataFrame(tools, columns=["Tool", "Descripción"])
    st.dataframe(df_tools, use_container_width=True, hide_index=True)


# =============================================================================
# PÁGINA: GISTM
# =============================================================================
elif page == "gistm":
    render_header("GISTM — Global Industry Standard on Tailings Management (2020)")

    st.markdown(
        """
    El **Global Industry Standard on Tailings Management** fue publicado en agosto de 2020 como resultado
    del trabajo conjunto de ICMM, PNUMA y Principles for Responsible Investment (PRI) tras el colapso
    de Brumadinho (Brasil, 2019). Establece **15 principios** agrupados en **6 topics**, con un total de
    **77 requisitos auditables** mediante los *Conformance Protocols* publicados por ICMM.
    """
    )

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Topics", "6")
    col_m2.metric("Principios", "15")
    col_m3.metric("Requisitos auditables", "77")

    st.markdown("### Navegación por Topics")

    topic_seleccionado = st.selectbox(
        "Selecciona un Topic del GISTM:",
        list(GISTM_TOPICS.keys()),
    )

    principios_del_topic = GISTM_TOPICS[topic_seleccionado]

    st.markdown(f"#### {topic_seleccionado}")
    st.markdown(f"*Incluye los principios: {', '.join(map(str, principios_del_topic))}*")

    for p_num in principios_del_topic:
        p = GISTM_PRINCIPIOS[p_num]
        with st.expander(
            f"**Principio {p_num}** — {p['title_es']}",
            expanded=False,
        ):
            st.markdown(f"**Título original:** *{p['title']}*")
            st.markdown(f"**Resumen:** {p['summary']}")
            st.markdown(f"**Skillset requerido para auditoría:** `{p['skills']}`")
            st.markdown(f"**N° de requisitos:** {p['requirements_count']}")
            st.info(f"**Referencia a normativa chilena:** {p['ley_chile']}")

    st.markdown("---")
    st.markdown("### Vista completa de los 15 principios")
    df_gistm = pd.DataFrame(
        [
            {
                "N°": num,
                "Topic": next(t for t, ps in GISTM_TOPICS.items() if num in ps),
                "Principio (ES)": data["title_es"],
                "Requisitos": data["requirements_count"],
            }
            for num, data in GISTM_PRINCIPIOS.items()
        ]
    )
    st.dataframe(df_gistm, use_container_width=True, hide_index=True)

    st.markdown("### Clasificación de consecuencias GISTM (Anexo 2)")
    st.markdown(
        """
    | Clase | Pérdida de vidas | Impacto ambiental | Infraestructura / economía |
    |---|---|---|---|
    | **Low** | No anticipada | Mínimo, restringido al sitio | Baja pérdida económica |
    | **Significant** | Improbable | Áreas localizadas, reversible | Daño limitado a infraestructura |
    | **High** | 1–10 víctimas potenciales | Significativo, recuperable | Daño mayor a infraestructura |
    | **Very High** | 10–100 víctimas potenciales | Grave, parcialmente reversible | Pérdida crítica |
    | **Extreme** | >100 víctimas potenciales | Catastrófico, irreversible | Pérdida económica masiva |
    
    *La clasificación debe basarse en modos de falla creíbles. Los operadores pueden optar por
    adoptar criterios de carga "Extreme" como enfoque más conservador.*
    """
    )


# =============================================================================
# PÁGINA: CORRELACIÓN
# =============================================================================
elif page == "correlacion":
    render_header("Matriz de correlación SERNAGEOMIN ↔ ICMM ↔ GISTM")

    st.markdown(
        """
    Esta matriz es el corazón de la guía: cruza cada sección del plan de cierre chileno con el elemento
    ICMM y el principio GISTM que debe incorporarse, más una recomendación concreta de cómo
    incorporarlo en la elaboración o actualización del plan.
    """
    )

    df_corr = pd.DataFrame(CORRELACION)

    # Búsqueda
    busqueda = st.text_input("🔍 Buscar en la matriz:", "")
    if busqueda:
        mask = df_corr.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
        df_filtrado = df_corr[mask]
    else:
        df_filtrado = df_corr

    st.dataframe(df_filtrado, use_container_width=True, hide_index=True, height=600)

    st.markdown(
        f"""
    <div class="callout">
    <b>Cómo usar esta matriz:</b> En la fase de redacción del plan, cada vez que abordes una sección
    del índice SERNAGEOMIN, consulta la fila correspondiente para identificar qué elemento ICMM
    y qué principio GISTM debería quedar explícitamente referenciado en el texto. Esto convierte
    tu plan de cierre chileno en un documento dual-compliant que también responde a las expectativas
    de empresas afiliadas a ICMM (Codelco, BHP, Anglo American, Antofagasta, Teck, Glencore).
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Descarga de la matriz
    csv = df_corr.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Descargar matriz en CSV",
        data=csv,
        file_name="matriz_correlacion_cierre_minas.csv",
        mime="text/csv",
    )


# =============================================================================
# PÁGINA: ROADMAP
# =============================================================================
elif page == "roadmap":
    render_header("Roadmap de cumplimiento integrado")

    st.markdown(
        """
    Hoja de ruta en **7 fases** para implementar un plan de cierre que cumpla simultáneamente la
    Ley 20.551 chilena, las buenas prácticas ICMM y los principios GISTM. Cada fase tiene
    actividades clave y un entregable concreto.
    """
    )

    for i, fase in enumerate(ROADMAP):
        with st.expander(
            f"**{fase['Fase']}** · Duración: {fase['Duración']}",
            expanded=(i == 0),
        ):
            st.markdown("**Actividades clave:**")
            for act in fase["Actividades clave"]:
                st.markdown(f"- {act}")
            st.success(f"**Entregable:** {fase['Entregable']}")


# =============================================================================
# PÁGINA: CHECKLIST
# =============================================================================
elif page == "checklist":
    render_header("Checklist auto-evaluable de cumplimiento")

    st.markdown(
        """
    Marca los ítems cumplidos en tu plan de cierre actual. Al final obtendrás un score por marco y
    podrás identificar las brechas a cerrar.
    """
    )

    checklist_items = {
        "SERNAGEOMIN (Ley 20.551)": [
            "Plan de cierre presentado ante SERNAGEOMIN con todas las secciones del índice",
            "Clasificación correcta del procedimiento (general / simplificado) por tpm",
            "Informe de vida útil certificado por Persona Competente Ley 20.235",
            "Evaluación de riesgos ISO 31000 aplicada a cada instalación",
            "Estudios de estabilidad física de instalaciones remanentes",
            "Estudios de estabilidad química y manejo de drenajes",
            "Cálculo de garantía financiera con tasa BCU y fórmula oficial",
            "Instrumentos de garantía constituidos ante SERNAGEOMIN",
            "Cronograma de cierre y post-cierre formalizado",
            "Auditoría externa por auditor RPAE (si aplica a procedimiento general)",
        ],
        "ICMM Integrated Mine Closure (2019)": [
            "Closure Vision Statement documentado y consensuado con stakeholders",
            "Knowledge base estructurada con actualización periódica",
            "Post-closure land use definido explícitamente",
            "Stakeholder engagement plan activo con registro de consultas",
            "Matriz de riesgos y oportunidades con owners asignados",
            "Success criteria cuantitativos por dominio",
            "Programa de cierre progresivo en ejecución",
            "Plan de transición social para trabajadores y comunidad",
            "Closure cost estimate con clase AACE ≥ 3",
            "Closure execution plan con WBS y cronograma",
            "Monitoring, maintenance & management plan",
            "Closure governance charter con comité de cierre",
            "Escenarios de cierre temporal/repentino evaluados",
        ],
        "GISTM (solo si hay depósitos de relaves)": [
            "Principio 1 — Grievance mechanism UNGP-compliant operativo",
            "Principio 2 — Knowledge base interdisciplinaria (actualización ≤5 años)",
            "Principio 3 — Integración de cambio climático en decisiones",
            "Principio 4 — Consequence classification aplicada (Anexo 2)",
            "Principio 5 — Design Basis Report (DBR) con multi-criteria analysis",
            "Principio 6 — Tailings Management System (TMS) implementado",
            "Principio 7 — Surveillance plan con critical controls",
            "Principio 8 — Accountable Executive designado a nivel ejecutivo",
            "Principio 9 — Engineer of Record (EOR) formalmente designado",
            "Principio 10 — ITRB o Senior Independent Technical Reviewer activo",
            "Principio 11 — Cultura de aprendizaje y reporte de incidentes",
            "Principio 12 — Canal formal de reporte de preocupaciones",
            "Principio 13 — Emergency Preparedness and Response Plan (EPRP)",
            "Principio 14 — Long-term recovery plan ante escenario de falla",
            "Principio 15 — Divulgación pública de información material",
        ],
    }

    scores = {}
    for marco, items in checklist_items.items():
        st.markdown(f"### {marco}")
        cumplidos = 0
        for item in items:
            key = f"{marco}_{item}"
            if st.checkbox(item, key=key):
                cumplidos += 1
        scores[marco] = (cumplidos, len(items))
        st.markdown("---")

    st.markdown("### 📊 Resultado de la auto-evaluación")
    cols = st.columns(len(scores))
    for i, (marco, (cump, total)) in enumerate(scores.items()):
        pct = (cump / total * 100) if total > 0 else 0
        cols[i].metric(
            label=marco.split(" (")[0],
            value=f"{cump}/{total}",
            delta=f"{pct:.0f}%",
        )

    total_cump = sum(s[0] for s in scores.values())
    total_items = sum(s[1] for s in scores.values())
    pct_global = (total_cump / total_items * 100) if total_items > 0 else 0

    st.progress(pct_global / 100)
    st.markdown(f"**Cumplimiento global:** {total_cump}/{total_items} ({pct_global:.1f}%)")

    if pct_global < 40:
        st.error("⚠️ Nivel crítico. Recomendación: iniciar gap assessment completo y plan de cierre de brechas estructurado.")
    elif pct_global < 70:
        st.warning("⚠️ Nivel intermedio. Plan en curso con brechas significativas en ICMM/GISTM.")
    elif pct_global < 90:
        st.info("✓ Nivel avanzado. Plan alineado; afinar elementos pendientes y documentar buenas prácticas.")
    else:
        st.success("✓✓ Nivel de excelencia. Plan dual-compliant (Chile + estándares internacionales).")

    st.markdown("---")
    st.markdown("### 📄 Generar informe Gap Assessment en PDF")
    col_a, col_b = st.columns(2)
    with col_a:
        empresa_pdf = st.text_input("Empresa / Faena", placeholder="Ej: Minera Los Bronces")
    with col_b:
        responsable_pdf = st.text_input("Responsable", placeholder="Ej: Juan Pérez")

    if st.button("Generar PDF", type="primary"):
        try:
            pdf_bytes = generate_gap_pdf(empresa_pdf, responsable_pdf, checklist_items, scores)
            if pdf_bytes:
                nombre_archivo = f"gap_assessment_(solo como referencia y prueba)_{date.today().strftime('%Y%m%d')}.pdf"
                st.download_button(
                    label="⬇ Descargar Gap Assessment PDF",
                    data=pdf_bytes,
                    file_name=nombre_archivo,
                    mime="application/pdf",
                )
            else:
                st.error("No se pudo generar el PDF. Verifica que reportlab esté instalado: `pip install reportlab`")
        except Exception as e:
            st.error(f"Error al generar PDF: {e}")


# =============================================================================
# PÁGINA: CALCULADORA DE GARANTÍA FINANCIERA
# =============================================================================
elif page == "garantia":
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go

    render_header("Calculadora de Garantía Financiera — Ley 20.551")

    st.markdown(
        """
        Calcula el cronograma de constitución de la garantía según la fórmula del **DS 41/2012 Art. 21**,
        proyecta el efecto del cierre progresivo sobre la garantía vigente, y genera la tabla año a año.
        """
    )

    st.markdown("### ⚙️ Parámetros de entrada")
    c1, c2, c3 = st.columns(3)
    with c1:
        vpt = float(st.number_input(
            "VPT — Valor total del Plan de Cierre (UF)",
            min_value=1000, max_value=10000000, value=50000, step=1000,
            help="Valor del Plan de Trabajo estimado en UF, conforme al cálculo de ingeniería de cierre.",
        ))
    with c2:
        vida_util = int(st.number_input(
            "Vida útil restante (años)",
            min_value=2, max_value=50, value=15, step=1,
            help="Años de operación hasta el cierre final de la faena.",
        ))
    with c3:
        tasa_bcu = float(st.number_input(
            "Tasa BCU real anual (%)",
            min_value=0.1, max_value=10.0, value=2.5, step=0.1,
            help="Tasa de los Bonos del Banco Central en UF (BCU) vigente, usada para actualización financiera.",
        ))

    st.markdown("---")
    st.markdown("### 📅 Cierres progresivos (opcional)")
    st.markdown("Agrega instalaciones que se cierran anticipadamente — reducen la garantía exigible de ese año en adelante.")

    prog_df = st.data_editor(
        pd.DataFrame({
            "Año de cierre":            pd.array([None], dtype="Int64"),
            "% VPT que representa":     pd.array([None], dtype="Float64"),
            "Instalación / Descripción": [""],
        }),
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Año de cierre": st.column_config.NumberColumn(
                "Año de cierre", min_value=1, max_value=vida_util, step=1
            ),
            "% VPT que representa": st.column_config.NumberColumn(
                "% VPT que representa", min_value=0.0, max_value=100.0, step=0.5
            ),
        },
    )

    # ── Cálculo del cronograma ───────────────────────────────────────────────
    r = tasa_bcu / 100.0
    N = vida_util
    cuota_base_pct = 80.0 / (N - 1) if N > 1 else 80.0

    reducciones = {}
    for _, prow in prog_df.iterrows():
        try:
            anio = int(prow["Año de cierre"])
            pct  = float(prow["% VPT que representa"])
            if 1 <= anio <= N and pct > 0:
                reducciones[anio] = reducciones.get(anio, 0.0) + pct
        except (TypeError, ValueError):
            pass

    rows_calc = []
    garantia_acum_pct = 0.0
    vpt_residual = vpt

    for t in range(1, N + 1):
        red_pct = 0.0
        if t in reducciones:
            red_pct = reducciones[t]
            vpt_residual = max(0.0, vpt_residual - vpt * (red_pct / 100.0))

        cuota_pct = 20.0 if t == 1 else cuota_base_pct
        garantia_acum_pct = min(100.0, garantia_acum_pct + cuota_pct)
        garantia_nominal = vpt_residual * (garantia_acum_pct / 100.0)
        factor_act = (1.0 + r) ** (N - t)
        garantia_actualizada = garantia_nominal / factor_act if factor_act else garantia_nominal

        rows_calc.append({
            "Año":                        t,
            "VPT residual (UF)":          round(vpt_residual, 0),
            "Cuota año (%)":              round(cuota_pct, 2),
            "Garantía acum. (%)":         round(garantia_acum_pct, 2),
            "Garantía nominal (UF)":      round(garantia_nominal, 0),
            "Garantía actualiz. BCU (UF)":round(garantia_actualizada, 0),
            "Cierre progresivo (% VPT)":  round(red_pct, 2),
        })

    df_garantia = pd.DataFrame(rows_calc)

    # ── KPIs rápidos ─────────────────────────────────────────────────────────
    m1, m2, m3 = st.columns(3)
    m1.metric("Garantía año 1 (nominal)", f"{df_garantia['Garantía nominal (UF)'].iloc[0]:,.0f} UF",
              f"20% de {vpt:,.0f} UF")
    m2.metric("Garantía año final (nominal)", f"{df_garantia['Garantía nominal (UF)'].iloc[-1]:,.0f} UF",
              f"100% del VPT residual")
    m3.metric("Cuota anual (años 2-{N})", f"{cuota_base_pct:.2f}% VPT/año",
              f"{vpt * cuota_base_pct / 100:,.0f} UF/año")

    # ── Gráfico con doble eje via make_subplots ───────────────────────────────
    st.markdown("### 📊 Cronograma de constitución")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=df_garantia["Año"],
            y=df_garantia["Garantía nominal (UF)"],
            name="Garantía nominal (UF)",
            marker_color="#1F2E3D",
            opacity=0.85,
            hovertemplate="Año %{x}<br>Garantía nominal: %{y:,.0f} UF<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df_garantia["Año"],
            y=df_garantia["Garantía actualiz. BCU (UF)"],
            name="Valor actualiz. BCU (UF)",
            mode="lines+markers",
            line=dict(color="#C14A1F", width=2.5),
            marker=dict(size=7, symbol="circle"),
            hovertemplate="Año %{x}<br>Valor actualiz.: %{y:,.0f} UF<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df_garantia["Año"],
            y=df_garantia["Garantía acum. (%)"],
            name="% acumulado exigible",
            mode="lines",
            line=dict(color="#4A9E6A", width=2, dash="dot"),
            hovertemplate="Año %{x}<br>% acumulado: %{y:.1f}%<extra></extra>",
        ),
        secondary_y=True,
    )

    # Líneas de cierre progresivo
    for a in df_garantia[df_garantia["Cierre progresivo (% VPT)"] > 0]["Año"].tolist():
        fig.add_vline(
            x=a, line_width=1.5, line_dash="dash", line_color="#C14A1F",
            annotation_text=f"Cierre prog.",
            annotation_font_size=10,
            annotation_position="top right",
        )

    fig.update_yaxes(
        title_text="Garantía (UF)",
        title_font_color="#1F2E3D",
        secondary_y=False,
        tickformat=",",
    )
    fig.update_yaxes(
        title_text="% acumulado exigible",
        title_font_color="#4A9E6A",
        secondary_y=True,
        range=[0, 110],
        ticksuffix="%",
    )
    fig.update_xaxes(title_text="Año de operación", dtick=1)
    fig.update_layout(
        title=dict(
            text=f"Garantía financiera — VPT: {vpt:,.0f} UF  |  Vida útil: {N} años  |  BCU: {tasa_bcu:.1f}%",
            font=dict(size=13, color="#1F2E3D"),
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#F4F6F8",
        paper_bgcolor="white",
        hovermode="x unified",
        height=440,
        margin=dict(t=80, b=50, l=60, r=60),
        barmode="overlay",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Tabla detalle ────────────────────────────────────────────────────────
    st.markdown("### 📋 Tabla detallada año a año")
    st.dataframe(df_garantia, use_container_width=True, hide_index=True)

    csv_gar = df_garantia.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇ Descargar cronograma CSV",
        data=csv_gar,
        file_name=f"garantia_financiera_{int(vpt)}UF_{N}a.csv",
        mime="text/csv",
    )

    with st.expander("ℹ️ Notas metodológicas"):
        st.markdown(
            f"""
            - **Base legal:** DS 41/2012, Art. 21 — Cronograma de constitución de garantía.
            - **Constitución inicial:** 20 % del VPT en el primer año a partir de la aprobación del plan.
            - **Cuotas anuales:** El 80 % restante se divide en **{N-1}** cuotas iguales de **{cuota_base_pct:.2f} % VPT/año**.
            - **Tasa BCU:** Se usa para calcular el valor actualizado de la obligación futura ({tasa_bcu:.1f}% real anual).
            - **Cierre progresivo (Art. 28):** Cada instalación certificada como cerrada reduce el VPT residual y, con ello, la garantía exigible desde ese año en adelante.
            - **Instrumentos admisibles:** Boleta bancaria, póliza de seguro, hipoteca, prenda, fideicomiso u otros aprobados por SERNAGEOMIN.
            """
        )


# =============================================================================
# PÁGINA: PROGRAMA AUDITORÍAS 2026
# =============================================================================
elif page == "auditorias":
    try:
        import folium
        from streamlit_folium import st_folium
        FOLIUM_OK = True
    except ImportError:
        FOLIUM_OK = False

    render_header("Programa de Auditorías 2026 — Lead Tracker Comercial")

    st.markdown(
        "Pipeline interno de las 20 faenas levantadas como oportunidad de auditoría externa (RPAE) "
        "y/o consultoría de cierre. Actualiza el estado desde la tabla — el mapa se actualiza en tiempo real."
    )

    # ── Dataset de faenas ────────────────────────────────────────────────────
    FAENAS_BASE = [
        {"Faena": "Los Bronces",          "Empresa": "Anglo American",      "Región": "Metropolitana",   "Mineral": "Cobre",    "Lat": -33.15, "Lon": -70.28, "Etapa": "En negociación",    "Contacto": "Felipe Rojas",      "Prioridad": "Alta",   "Próximo paso": "Enviar propuesta técnica"},
        {"Faena": "El Teniente",           "Empresa": "Codelco",             "Región": "O'Higgins",       "Mineral": "Cobre",    "Lat": -34.07, "Lon": -70.36, "Etapa": "Propuesta enviada", "Contacto": "Carmen Valdés",     "Prioridad": "Alta",   "Próximo paso": "Seguimiento semana 15"},
        {"Faena": "Chuquicamata",          "Empresa": "Codelco",             "Región": "Antofagasta",     "Mineral": "Cobre",    "Lat": -22.31, "Lon": -68.93, "Etapa": "Contacto inicial",  "Contacto": "Jorge Pizarro",     "Prioridad": "Alta",   "Próximo paso": "Reunión diagnóstico"},
        {"Faena": "Escondida",             "Empresa": "BHP",                 "Región": "Antofagasta",     "Mineral": "Cobre",    "Lat": -24.27, "Lon": -69.07, "Etapa": "Propuesta enviada", "Contacto": "Ana Morales",       "Prioridad": "Alta",   "Próximo paso": "Respuesta pendiente"},
        {"Faena": "Collahuasi",            "Empresa": "JX / Anglo / Marubeni","Región": "Tarapacá",       "Mineral": "Cobre",    "Lat": -20.98, "Lon": -68.71, "Etapa": "Prospecto",         "Contacto": "—",                 "Prioridad": "Media",  "Próximo paso": "Identificar contacto Closure"},
        {"Faena": "Spence",                "Empresa": "BHP",                 "Región": "Antofagasta",     "Mineral": "Cobre",    "Lat": -22.61, "Lon": -69.38, "Etapa": "Prospecto",         "Contacto": "—",                 "Prioridad": "Media",  "Próximo paso": "Revisión plan cierre vigente"},
        {"Faena": "Radomiro Tomic",        "Empresa": "Codelco",             "Región": "Antofagasta",     "Mineral": "Cobre",    "Lat": -22.20, "Lon": -68.90, "Etapa": "Contacto inicial",  "Contacto": "Luis Fuentes",      "Prioridad": "Alta",   "Próximo paso": "Enviar perfil de servicios"},
        {"Faena": "Sierra Gorda",          "Empresa": "KGHM / Sumitomo",     "Región": "Antofagasta",     "Mineral": "Cobre-Mo", "Lat": -22.88, "Lon": -69.36, "Etapa": "Propuesta enviada", "Contacto": "María Soto",        "Prioridad": "Alta",   "Próximo paso": "Presentación técnica 20-abr"},
        {"Faena": "Candelaria",            "Empresa": "Lundin Mining",       "Región": "Atacama",         "Mineral": "Cobre",    "Lat": -27.37, "Lon": -70.22, "Etapa": "Contratado",        "Contacto": "Pablo Jara",        "Prioridad": "Alta",   "Próximo paso": "Inicio auditoría may-2026"},
        {"Faena": "Cerro Negro Norte",     "Empresa": "CAP Minería",         "Región": "Atacama",         "Mineral": "Hierro",   "Lat": -27.10, "Lon": -70.15, "Etapa": "En negociación",    "Contacto": "Rodrigo Castro",    "Prioridad": "Media",  "Próximo paso": "Afinar alcance contractual"},
        {"Faena": "Pelambres",             "Empresa": "Antofagasta Minerals", "Región": "Coquimbo",       "Mineral": "Cobre-Mo", "Lat": -31.77, "Lon": -70.57, "Etapa": "Contacto inicial",  "Contacto": "Cristina Leiva",    "Prioridad": "Alta",   "Próximo paso": "Workshop gap assessment"},
        {"Faena": "El Romeral",            "Empresa": "CAP Minería",         "Región": "Coquimbo",        "Mineral": "Hierro",   "Lat": -30.03, "Lon": -71.03, "Etapa": "Prospecto",         "Contacto": "—",                 "Prioridad": "Baja",   "Próximo paso": "Evaluar convocatoria licitación"},
        {"Faena": "Atacama Kozan",         "Empresa": "Kozan Mining",        "Región": "Atacama",         "Mineral": "Cobre",    "Lat": -26.50, "Lon": -69.80, "Etapa": "Prospecto",         "Contacto": "—",                 "Prioridad": "Media",  "Próximo paso": "Contacto via SONAMI"},
        {"Faena": "Esperanza (Centinela)", "Empresa": "Antofagasta Minerals", "Región": "Antofagasta",    "Mineral": "Cobre-Au", "Lat": -22.33, "Lon": -69.52, "Etapa": "Contacto inicial",  "Contacto": "Daniela Núñez",     "Prioridad": "Alta",   "Próximo paso": "Reunión técnica planificada"},
        {"Faena": "Zaldívar",              "Empresa": "Antofagasta / Barrick","Región": "Antofagasta",    "Mineral": "Cobre",    "Lat": -23.97, "Lon": -69.47, "Etapa": "Propuesta enviada", "Contacto": "Sebastián Ríos",    "Prioridad": "Alta",   "Próximo paso": "Seguimiento propuesta RPAE"},
        {"Faena": "Mantos Blancos",        "Empresa": "Amsa (Antofagasta M.)","Región": "Antofagasta",    "Mineral": "Cobre",    "Lat": -23.15, "Lon": -70.07, "Etapa": "En negociación",    "Contacto": "Verónica Díaz",     "Prioridad": "Media",  "Próximo paso": "Revisión propuesta económica"},
        {"Faena": "Teck Carmen de Andacollo","Empresa": "Teck",              "Región": "Coquimbo",        "Mineral": "Cobre-Au", "Lat": -30.23, "Lon": -71.09, "Etapa": "Contratado",        "Contacto": "Marco Espinoza",    "Prioridad": "Alta",   "Próximo paso": "Plan de trabajo aprobado"},
        {"Faena": "Quebrada Blanca",       "Empresa": "Teck / ENAMI",        "Región": "Tarapacá",        "Mineral": "Cobre",    "Lat": -20.98, "Lon": -68.88, "Etapa": "Prospecto",         "Contacto": "—",                 "Prioridad": "Media",  "Próximo paso": "Revisión vencimiento RPAE actual"},
        {"Faena": "Punta de Lobos",        "Empresa": "SQM",                 "Región": "Tarapacá",        "Mineral": "Yodo/Nitr","Lat": -21.22, "Lon": -70.08, "Etapa": "Contacto inicial",  "Contacto": "Ignacio Vera",      "Prioridad": "Baja",   "Próximo paso": "Definir si aplica Ley 20.551"},
        {"Faena": "Ministro Hales",        "Empresa": "Codelco",             "Región": "Antofagasta",     "Mineral": "Cobre",    "Lat": -22.62, "Lon": -69.05, "Etapa": "En negociación",    "Contacto": "Teresa Gómez",      "Prioridad": "Alta",   "Próximo paso": "Cierre negociación abr-2026"},
    ]

    ETAPA_COLOR = {
        "Prospecto":         "#4A5A6A",
        "Contacto inicial":  "#2196F3",
        "Propuesta enviada": "#FF9800",
        "En negociación":    "#9C27B0",
        "Contratado":        "#4CAF50",
    }
    PRIORIDAD_COLOR = {"Alta": "#C14A1F", "Media": "#FF9800", "Baja": "#4A5A6A"}

    if "faenas_df" not in st.session_state:
        st.session_state.faenas_df = pd.DataFrame(FAENAS_BASE)

    # ── Filtros ──────────────────────────────────────────────────────────────
    st.markdown("### 🔎 Filtros")
    f1, f2, f3 = st.columns(3)
    with f1:
        etapas_sel = st.multiselect(
            "Etapa", options=list(ETAPA_COLOR.keys()), default=list(ETAPA_COLOR.keys())
        )
    with f2:
        prio_sel = st.multiselect(
            "Prioridad", options=["Alta", "Media", "Baja"], default=["Alta", "Media", "Baja"]
        )
    with f3:
        region_sel = st.multiselect(
            "Región", options=sorted(st.session_state.faenas_df["Región"].unique()),
            default=sorted(st.session_state.faenas_df["Región"].unique()),
        )

    mask = (
        st.session_state.faenas_df["Etapa"].isin(etapas_sel) &
        st.session_state.faenas_df["Prioridad"].isin(prio_sel) &
        st.session_state.faenas_df["Región"].isin(region_sel)
    )
    df_vis = st.session_state.faenas_df[mask].copy()

    # ── KPIs ─────────────────────────────────────────────────────────────────
    st.markdown("### 📊 Pipeline 2026")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total faenas", len(df_vis))
    k2.metric("Contratadas", int((df_vis["Etapa"] == "Contratado").sum()))
    k3.metric("En negociación", int((df_vis["Etapa"] == "En negociación").sum()))
    k4.metric("Propuestas enviadas", int((df_vis["Etapa"] == "Propuesta enviada").sum()))
    k5.metric("Alta prioridad", int((df_vis["Prioridad"] == "Alta").sum()))

    # ── Mapa ─────────────────────────────────────────────────────────────────
    st.markdown("### 🗺️ Mapa de faenas")
    if FOLIUM_OK:
        m = folium.Map(location=[-26.0, -69.5], zoom_start=5, tiles="CartoDB positron")
        for _, row in df_vis.iterrows():
            color = ETAPA_COLOR.get(row["Etapa"], "#4A5A6A")
            # Popup con fondo blanco y texto negro explícito — evita herencia de tema oscuro
            popup_html = f"""
            <div style="background:#ffffff;color:#1F2E3D;padding:10px 12px;
                        border-radius:6px;font-family:sans-serif;font-size:13px;
                        min-width:200px;line-height:1.6;">
              <div style="font-weight:700;font-size:14px;margin-bottom:4px;
                          border-bottom:2px solid {color};padding-bottom:4px;">
                {row['Faena']}
              </div>
              <div style="color:#4A5A6A;font-size:11px;margin-bottom:6px;">{row['Empresa']}</div>
              <table style="width:100%;border-collapse:collapse;font-size:12px;">
                <tr><td style="color:#888;padding:1px 4px 1px 0;">Mineral</td>
                    <td style="color:#1F2E3D;font-weight:600;">{row['Mineral']}</td></tr>
                <tr><td style="color:#888;padding:1px 4px 1px 0;">Etapa</td>
                    <td style="color:{color};font-weight:700;">{row['Etapa']}</td></tr>
                <tr><td style="color:#888;padding:1px 4px 1px 0;">Prioridad</td>
                    <td style="color:#1F2E3D;">{row['Prioridad']}</td></tr>
                <tr><td style="color:#888;padding:1px 4px 1px 0;">Contacto</td>
                    <td style="color:#1F2E3D;">{row['Contacto']}</td></tr>
              </table>
              <div style="margin-top:7px;padding-top:6px;border-top:1px solid #eee;
                          color:#555;font-size:11px;font-style:italic;">
                &#8594; {row['Próximo paso']}
              </div>
            </div>"""
            folium.CircleMarker(
                location=[row["Lat"], row["Lon"]],
                radius=10 if row["Prioridad"] == "Alta" else 7,
                color="white",
                weight=1.5,
                fill=True,
                fill_color=color,
                fill_opacity=0.9,
                popup=folium.Popup(popup_html, max_width=280),
                tooltip=folium.Tooltip(
                    f"<span style='background:white;color:#1F2E3D;padding:3px 8px;"
                    f"border-radius:4px;font-size:12px;font-weight:600;'>"
                    f"{row['Faena']}</span>",
                    sticky=True,
                ),
            ).add_to(m)

        st_folium(m, width=None, height=500, returned_objects=[])

        # Leyenda debajo del mapa como componente Streamlit (no dentro del iframe)
        st.markdown(
            f"""
            <div style="display:flex;flex-wrap:wrap;gap:12px;padding:10px 14px;
                        background:#F4F6F8;border-radius:8px;border:1px solid #E1E8F0;
                        font-size:12px;margin-top:6px;">
              <span style="font-weight:700;color:#1F2E3D;">Etapa:</span>
              <span><span style="color:#4A5A6A;font-size:16px;">●</span> <span style="color:#1F2E3D;">Prospecto</span></span>
              <span><span style="color:#2196F3;font-size:16px;">●</span> <span style="color:#1F2E3D;">Contacto inicial</span></span>
              <span><span style="color:#FF9800;font-size:16px;">●</span> <span style="color:#1F2E3D;">Propuesta enviada</span></span>
              <span><span style="color:#9C27B0;font-size:16px;">●</span> <span style="color:#1F2E3D;">En negociación</span></span>
              <span><span style="color:#4CAF50;font-size:16px;">●</span> <span style="color:#1F2E3D;">Contratado</span></span>
              &nbsp;·&nbsp;
              <span style="font-weight:700;color:#1F2E3D;">Tamaño:</span>
              <span style="color:#4A5A6A;">⬤ grande = Alta prioridad</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning(
            "Mapa no disponible. Instala `folium` y `streamlit-folium`:\n"
            "```\npip install folium streamlit-folium\n```"
        )

    # ── Tabla editable ────────────────────────────────────────────────────────
    st.markdown("### ✏️ Editar pipeline")
    df_edit = st.data_editor(
        df_vis.drop(columns=["Lat", "Lon"]),
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "Etapa": st.column_config.SelectboxColumn(
                "Etapa", options=list(ETAPA_COLOR.keys()), required=True
            ),
            "Prioridad": st.column_config.SelectboxColumn(
                "Prioridad", options=["Alta", "Media", "Baja"], required=True
            ),
        },
        key="edit_faenas",
    )

    # Actualizar session_state con cambios de la tabla
    for col in ["Etapa", "Prioridad", "Contacto", "Próximo paso"]:
        if col in df_edit.columns:
            st.session_state.faenas_df.loc[mask, col] = df_edit[col].values

    # Exportar
    csv_leads = st.session_state.faenas_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇ Exportar pipeline completo CSV",
        data=csv_leads,
        file_name="pipeline_auditorias_2026.csv",
        mime="text/csv",
    )


# =============================================================================
# PÁGINA: REFERENCIAS
# =============================================================================
elif page == "referencias":
    render_header("Referencias, enlaces y descargas")

    st.markdown("### 📚 Documentación regulatoria chilena")
    st.markdown(
        """
    - **Ley 20.551** — [leychile.cl](https://www.bcn.cl/leychile/navegar?idNorma=1032158)
    - **DS 41/2012** — Reglamento Ley de Cierre — [bcn.cl](https://www.bcn.cl)
    - **SERNAGEOMIN — Cierre de Faenas Mineras** — [sernageomin.cl/ambiental-cierre](https://www.sernageomin.cl/ambiental-cierre)
    - **Registro Público de Auditores Externos (RPAE)** — [sernageomin.cl](https://www.sernageomin.cl)
    - **Guía Garantía Financiera Ley 20.551** — [sernageomin.cl](https://www.sernageomin.cl/guia-metodologica-de-calculo-determinacion-y-disposicion-de-la-garantia-financiera-que-establece-la-ley-20551/)
    - **Servicio de Evaluación Ambiental (SEA)** — [sea.gob.cl](https://www.sea.gob.cl)
    """
    )

    st.markdown("### 🌍 Estándares internacionales")
    st.markdown(
        """
    - **ICMM — Integrated Mine Closure Good Practice Guide (2019)** — [icmm.com](https://www.icmm.com)
    - **ICMM — Tailings Management Good Practice Guide (2021)** — [icmm.com](https://www.icmm.com)
    - **Global Industry Standard on Tailings Management (GISTM, 2020)** — [globaltailingsreview.org](https://globaltailingsreview.org)
    - **ICMM — Conformance Protocols for GISTM (2021)** — [icmm.com](https://www.icmm.com)
    - **ISO 31000** — Risk Management Principles and Guidelines
    - **ICOLD** — International Commission on Large Dams — [icold-cigb.org](https://www.icold-cigb.org)
    - **INAP — GARD Guide** — [gardguide.com](https://www.gardguide.com)
    - **MEND — Mine Environment Neutral Drainage** — [mend-nedem.org](https://www.mend-nedem.org)
    """
    )

    st.markdown("### 🏛️ Gremios, ferias y redes profesionales")
    st.markdown(
        """
    - **Consejo Minero Chile** — [consejominero.cl](https://www.consejominero.cl)
    - **SONAMI** — Sociedad Nacional de Minería — [sonami.cl](https://www.sonami.cl)
    - **COCHILCO** — Comisión Chilena del Cobre — [cochilco.cl](https://www.cochilco.cl)
    - **CHCOLD** — Comité Chileno de Grandes Presas
    - **Gecamin** — Conferencias técnicas (Tailings, Paste, Mine Closure, Water in Mining) — [gecamin.com](https://www.gecamin.com)
    - **Mine Closure Conference (ACG)** — [acg.uwa.edu.au](https://www.acg.uwa.edu.au)
    - **Tailings and Mine Waste Conference** — [tailingsandminewaste.com](https://tailingsandminewaste.com)
    """
    )

    st.markdown("---")
    st.markdown("### 📥 Descargas desde esta herramienta")

    # Export de correlación
    df_corr = pd.DataFrame(CORRELACION)
    csv_corr = df_corr.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Matriz de correlación (CSV)",
        data=csv_corr,
        file_name="matriz_correlacion.csv",
        mime="text/csv",
    )

    # Export de ICMM
    df_icmm = pd.DataFrame(ICMM_ELEMENTOS)
    csv_icmm = df_icmm.to_csv(index=False).encode("utf-8")
    st.download_button(
        "ICMM 17 elementos (CSV)",
        data=csv_icmm,
        file_name="icmm_elementos.csv",
        mime="text/csv",
    )

    # Export de GISTM
    df_gistm_full = pd.DataFrame(
        [
            {
                "N°": num,
                "Topic": next(t for t, ps in GISTM_TOPICS.items() if num in ps),
                "Título EN": data["title"],
                "Título ES": data["title_es"],
                "Resumen": data["summary"],
                "Requisitos": data["requirements_count"],
                "Skills": data["skills"],
                "Referencia Chile": data["ley_chile"],
            }
            for num, data in GISTM_PRINCIPIOS.items()
        ]
    )
    csv_gistm = df_gistm_full.to_csv(index=False).encode("utf-8")
    st.download_button(
        "GISTM 15 principios (CSV)",
        data=csv_gistm,
        file_name="gistm_principios.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.caption(
        "Esta guía interactiva es de referencia general y no reemplaza la asesoría especialista."
    )
