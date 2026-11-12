"""CV y carta de presentación independientes — diseño clásico inspirado en LaTeX.

Diseño A4 de una columna con títulos centrados y reglas horizontales.
Streamlit: Principal + Detalles, dos descargas independientes en PDF.

Instalación: pip install streamlit reportlab
Ejecución:    streamlit run app.py

El contenido se basa en el CV proporcionado por Enrique. Comprueba fechas,
ubicaciones, nombres de unidades y competencias antes de cada postulación.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
import html
import re
from io import BytesIO
from xml.sax.saxutils import escape

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, KeepTogether, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

# -----------------------------------------------------------------------------
# CONTENIDO — versión completa
# -----------------------------------------------------------------------------
PERSONA = {
    "nombre": "Enrique Brun Urrutia",
    "titulo": "Ingeniero Civil Químico",
    "subtitulo": "Ingeniería de Procesos  /  Analítica Industrial  /  Transformación Digital",
    "ciudad": "Santiago de Chile",
    "telefono": "+56 9 6359 6523",
    "correo": "enrique.brun@usm.cl",
    "linkedin": "linkedin.com/in/enrique-brun-248a02261/",
}

# Conservado para actualizar automáticamente el antiguo texto de ejemplo sin
# sobrescribir el perfil de quienes ya lo editaron en la aplicación.
PERFIL_ANTERIOR = (
    "Ingeniero Civil Químico de la Universidad Técnica Federico Santa María, "
    "con experiencia en minería, refinación, manufactura y abastecimiento. "
    "Integro ingeniería de procesos y analítica industrial para convertir datos "
    "operacionales en decisiones técnicas. He desarrollado modelos predictivos "
    "de capacidad y consumo energético en molienda SAG y trabajado con Python, "
    "DCS, AVEVA PI, SAP y Power BI. Combino análisis de datos con trabajo en planta "
    "para identificar desviaciones y oportunidades de mejora operacional."
)

# Versión previa del perfil para migrar solo el texto predeterminado de la app.
PERFIL_BASE_ANTERIOR = (
    "Ingeniero Civil Químico de la Universidad Técnica Federico Santa María, "
    "con experiencia en minería, energía, manufactura y abastecimiento. "
    "Integro ingeniería de procesos, analítica de datos y automatización para "
    "transformar información operacional en decisiones, desde modelos predictivos "
    "para molienda SAG hasta indicadores y reportes de gestión. Me caracteriza la "
    "curiosidad por comprender cómo funcionan los procesos, explorar nuevas "
    "herramientas y aprender continuamente. Abordo cada desafío con iniciativa, "
    "rigurosidad y compromiso con el cumplimiento de objetivos y la entrega de "
    "resultados concretos. Creo en el potencial de la industria nacional y busco "
    "desafíos exigentes para contribuir a su desarrollo y superarme cada día."
)

# Valor técnico en el primer párrafo y motivación personal en el segundo.
# Se evitan porcentajes o ahorros que no estén acreditados.
PERFIL_BASE = (
    "Ingeniero Civil Químico de la Universidad Técnica Federico Santa María, "
    "orientado a la analítica de datos, inteligencia de negocios y optimización "
    "de procesos industriales. Experiencia en minería, energía, manufactura y "
    "abastecimiento, combinando trabajo en planta y análisis de información "
    "operacional. He desarrollado modelos predictivos para molienda SAG e "
    "indicadores y automatizaciones que apoyan decisiones de procesos y gestión, "
    "utilizando herramientas como Python, Power BI y SAP.\n\n"
    "Me caracteriza la curiosidad por comprender cómo funcionan las cosas, "
    "explorar nuevas soluciones y aprender continuamente. Asumo cada desafío "
    "con iniciativa, rigurosidad y compromiso con los objetivos y resultados. "
    "Creo en el potencial de la industria nacional y busco contribuir a su "
    "desarrollo en entornos que me impulsen a mejorar y superarme cada día."
)

# Se respeta el nombre de cada empresa y la unidad mencionada en el CV fuente.
# Dos aportes por experiencia, basados en actividades descritas por el titular.
EXPERIENCIAS = [
    {
        "empresa": "ENAEX S.A.",
        "area": "Gerencia de Abastecimiento",
        "cargo": "Práctica profesional · Analítica y automatización de compras",
        "lugar": "Las Condes, Santiago",
        "fechas": "abr. – ago. 2026",
        "logros": [
            "Integré datos de SAP ERP y SAP Ariba con fuentes externas (SII, Banco Central e indicadores financieros) para analizar compras, contratos y proveedores con mayor trazabilidad.",
            "Desarrollé automatizaciones y tableros de indicadores para disminuir tareas manuales y facilitar el seguimiento de proveedores y el control de gestión.",
        ],
    },
    {
        "empresa": "CCU",
        "area": "Planta Modelo Renca · Operaciones",
        "cargo": "Práctica industrial · Indicadores y mejora de procesos",
        "lugar": "Renca, Santiago",
        "fechas": "mar. – ago. 2026",
        "logros": [
            "Analicé variables operacionales y condiciones de elaboración y envasado de bebidas para identificar pérdidas y brechas de desempeño en planta.",
            "Desarrollé indicadores y tableros de control; combiné análisis de causa raíz y automatización de reportes para apoyar iniciativas de mejora continua.",
        ],
    },
    {
        "empresa": "Minera Los Pelambres",
        "area": "Planta Concentradora · Ingeniería de Procesos",
        "cargo": "Práctica profesional · Ingeniería de procesos · Turno 4x3",
        "lugar": "Salamanca, Chile",
        "fechas": "ene. – mar. 2026",
        "logros": [
            "Analicé datos históricos del DCS y variables de molienda SAG para evaluar estabilidad operacional, desempeño y consumo energético del circuito.",
            "Contrasté tendencias de datos con observaciones en faena y condiciones de los equipos durante turnos 4x3 para identificar patrones y desviaciones operacionales.",
        ],
    },
    {
        "empresa": "SQM",
        "area": "International Lithium · Gestión del Conocimiento",
        "cargo": "Práctica · Gestión y transferencia de información técnica",
        "lugar": "Modalidad remota",
        "fechas": "sept. – dic. 2025",
        "logros": [
            "Clasifiqué y estandaricé documentación técnica de operaciones, procesos, automatización y otras áreas para facilitar su consulta y reutilización.",
            "Organicé planos, informes y otros antecedentes con criterios de trazabilidad para preservar conocimiento y apoyar su transferencia a equipos de proyectos en Australia y China.",
        ],
    },
    {
        "empresa": "Antofagasta Minerals",
        "area": "División de Procesos · Proyecto de Título",
        "cargo": "Proyecto de título · Machine learning para molienda SAG",
        "lugar": "Las Condes, Santiago",
        "fechas": "abr. – nov. 2025",
        "logros": [
            "Construí y evalué modelos predictivos con datos históricos de Minera Los Pelambres para analizar la capacidad de procesamiento y el consumo específico de energía en molienda SAG.",
            "Identifiqué variables críticas y escenarios de operación con potencial de mejora, aportando antecedentes técnicos para apoyar decisiones de optimización.",
        ],
    },
    {
        "empresa": "ENAP",
        "area": "Refinería Aconcagua · División de Procesos",
        "cargo": "Práctica industrial · Monitoreo y analítica de procesos",
        "lugar": "Concón, Chile",
        "fechas": "ene. – mar. 2025",
        "logros": [
            "Analicé datos históricos de procesos de refinación con AVEVA PI, integrando interpretación de PFD y P&ID y observaciones de planta.",
            "Preparé análisis estadísticos, visualizaciones y reportes de tendencias para apoyar el monitoreo operacional y detectar oportunidades de mejora.",
        ],
    },
]

FORMACION = (
    "Universidad Técnica Federico Santa María",
    "Ingeniería Civil Química · Casa Central, Valparaíso, Chile · 2020–2026",
)

# Orden de lectura internacional: competencias nucleares primero.
# El resto se resume sin transmitir que todas las herramientas tienen el mismo
# nivel de dominio. Se conserva el foco industrial del CV fuente.
COMPETENCIAS = [
    ("Herramientas clave", "Python (pandas, scikit-learn), Power BI (Power Query y DAX), SQL, Microsoft Azure / Fabric y SAP ERP / Ariba."),
    ("Analítica aplicada", "Machine learning, modelos predictivos, análisis estadístico, automatización de reportes y visualización de indicadores."),
    ("Ingeniería de procesos", "Molienda SAG, eficiencia energética, sistemas DCS y AVEVA PI, interpretación de PFD / P&ID y mejora continua."),
    ("Herramientas complementarias", "Excel avanzado, Power Automate, Aspen Plus / HYSYS, JKSimMet / IES, Databricks y Git / GitHub."),
    ("Idiomas", "Español nativo · Inglés C1 Advanced (EF SET, jul. 2025)."),
]

CERTIFICACIONES = [
    "JKSimMet · Simulación y optimización de conminución — The University of Queensland · 2025",
    "Integrated Extraction Simulator (IES) · Conminución — Orica · 2025",
    "Power BI y Excel — SERGROUP · 2025",
    "EF SET English Certificate · C1 Advanced · jul. 2025",
]

DOCENCIA = [
    ("Universidad Técnica Federico Santa María", "Ayudante y coordinador, 2021–2025 · Diseño y Análisis de Procesos, Cristalización, Química y Física General I, entre otras asignaturas."),
    ("Preuniversitario CPECH", "Docente de Matemáticas, Química, Biología y Física para preparación PAES · Viña del Mar, Chile."),
]

ACTIVIDADES = (
    "AIESEC Chile: vicepresidente de Marketing · PREUSM: docente y coordinador "
    "de voluntariado PAES · Escuela Santa María: voluntariado de Matemáticas · "
    "CETAM: Expedición Científica Andes."
)

ARCHIVO_PDF = "CV_Enrique_Brun_Urrutia.pdf"
ARCHIVO_CARTA = "Carta_de_Presentacion_Enrique_Brun_Urrutia.pdf"
ZONA_HORARIA = ZoneInfo("America/Santiago")

# El usuario puede adaptar el texto a cada postulación. Los campos de cargo y
# empresa se colocan en el encabezado del PDF, no se insertan en el texto libre.
CARTA_BASE = (
    "Soy Ingeniero Civil Químico de la Universidad Técnica Federico Santa María "
    "y me interesa aportar en desafíos de ingeniería de procesos, analítica de "
    "datos y mejora operacional. Mi experiencia en minería, energía, manufactura "
    "y abastecimiento me ha permitido conectar el conocimiento de los procesos "
    "industriales con herramientas analíticas para apoyar decisiones técnicas "
    "y de gestión.\n\n"
    "En Antofagasta Minerals y Minera Los Pelambres trabajé en el análisis "
    "de datos históricos de molienda SAG y en modelos predictivos relacionados "
    "con la capacidad de procesamiento y el consumo energético. En ENAEX y CCU "
    "participé en el desarrollo de indicadores, automatizaciones y reportes "
    "para facilitar el seguimiento y la mejora de procesos. Mis experiencias "
    "en ENAP y SQM complementaron esta visión desde el monitoreo de operaciones "
    "y la gestión de información técnica.\n\n"
    "Me caracterizan la curiosidad, las ganas de descubrir nuevas soluciones "
    "y el aprendizaje continuo. Trabajo con responsabilidad, rigurosidad y "
    "compromiso con los objetivos que asumo. Creo en el potencial de la "
    "industria nacional y busco desafíos que me exijan superarme cada día, "
    "aprender de equipos diversos y contribuir con resultados concretos.\n\n"
    "Agradezco la consideración de mi postulación y quedo disponible para "
    "conversar sobre cómo podría aportar a su equipo."
)

# -----------------------------------------------------------------------------
# ESTILO CLÁSICO / LATEX (una columna, sin cajas, sin iconos)
# La versión de Streamlit usa ReportLab para no requerir TeX Live en el servidor.
# Referencias de estilo: Jake's Resume (Overleaf) y guías de Harvard MCS.
# -----------------------------------------------------------------------------
NAVY = colors.HexColor("#1A334F")
INK = colors.HexColor("#1E2730")
SECONDARY = colors.HexColor("#4D5964")
MUTED = colors.HexColor("#677481")
RULE = colors.HexColor("#33485C")
PAGE_W, PAGE_H = A4
MARGIN_X = 18 * mm
MARGIN_TOP = 17.5 * mm
MARGIN_BOTTOM = 16 * mm
CONTENT_W = PAGE_W - 2 * MARGIN_X


def esc(value: str) -> str:
    return escape(str(value))


def text_style(name, size, leading, color=INK, font="Helvetica",
               align=TA_LEFT, before=0, after=0, indent=0,
               bullet_indent=0, keep=False):
    return ParagraphStyle(
        name, fontName=font, fontSize=size, leading=leading,
        textColor=color, alignment=align, spaceBefore=before,
        spaceAfter=after, leftIndent=indent, bulletIndent=bullet_indent,
        bulletFontName="Helvetica", bulletFontSize=8.5,
        allowWidows=0, allowOrphans=0, keepWithNext=keep,
        justifyLastLine=0, justifyBreaks=0, splitLongWords=1,
    )


STYLES = {
    "strap": text_style("strap", 9.0, 12.8, SECONDARY, "Helvetica-Bold", TA_CENTER, after=1),
    "contact": text_style("contact", 8.8, 12.8, INK, align=TA_CENTER),
    "profile": text_style("profile", 10.05, 14.3, INK, align=TA_JUSTIFY, after=5.5),
    "organization": text_style("organization", 10.55, 13.4, INK, keep=True),
    "dates": text_style("dates", 9.15, 13.4, NAVY, "Helvetica-Bold", TA_RIGHT),
    "role": text_style("role", 9.1, 12.0, SECONDARY, keep=True),
    "location": text_style("location", 8.6, 12.0, MUTED, align=TA_RIGHT),
    "bullet": text_style("bullet", 9.7, 13.3, INK, align=TA_JUSTIFY, indent=14, bullet_indent=2, after=3.2),
    "body": text_style("body", 9.5, 13.1, INK, align=TA_LEFT, after=3.0),
    "small": text_style("small", 9.25, 12.7, INK, align=TA_LEFT, after=3.0),
    "education": text_style("education", 9.9, 13.2, INK, "Helvetica-Bold"),
}


class NameHeading(Flowable):
    """Mayúsculas con interletrado tipográfico y alineación centrada."""
    def __init__(self, title: str):
        super().__init__()
        self.title = title.upper()
        self.height = 38

    def wrap(self, available_width, available_height):
        self.width = available_width
        return self.width, self.height

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        fs, tracking = 24.2, 0.55
        measured = pdfmetrics.stringWidth(self.title, "Helvetica-Bold", fs) + tracking * max(0, len(self.title) - 1)
        text = canvas.beginText((self.width - measured) / 2, 7.5)
        text.setFont("Helvetica-Bold", fs)
        text.setCharSpace(tracking)
        text.setFillColor(NAVY)
        text.textOut(self.title)
        canvas.drawText(text)
        canvas.restoreState()


class SectionHeading(Flowable):
    """Sección centrada con raya horizontal: referencia clásica Canva/LaTeX."""
    def __init__(self, title: str, compact: bool = False):
        super().__init__()
        self.title = title.upper()
        self.height = 32 if not compact else 27
        self.spaceBefore = 4 if not compact else 2
        self.keepWithNext = True

    def wrap(self, available_width, available_height):
        self.width = available_width
        return self.width, self.height

    def draw(self):
        canv = self.canv
        canv.saveState()
        size, charspace = 10.3, .47
        width = pdfmetrics.stringWidth(self.title, "Helvetica-Bold", size) + charspace * max(0, len(self.title) - 1)
        label = canv.beginText((self.width - width) / 2, 14 if self.height == 32 else 11)
        label.setFont("Helvetica-Bold", size)
        label.setFillColor(NAVY)
        label.setCharSpace(charspace)
        label.textOut(self.title)
        canv.drawText(label)
        canv.setStrokeColor(RULE)
        canv.setLineWidth(.8)
        canv.line(0, 7 if self.height == 32 else 4, self.width, 7 if self.height == 32 else 4)
        canv.restoreState()


def par(text: str, style: str) -> Paragraph:
    return Paragraph(esc(text), STYLES[style])


def bloques_perfil(text: str) -> list[str]:
    """Párrafos editables sin perder los saltos de línea del usuario."""
    normalized = text.strip().replace("\r\n", "\n").replace("\r", "\n")
    return [" ".join(p.split()) for p in re.split(r"\n\s*\n", normalized) if p.strip()]


def header() -> list:
    email = esc(PERSONA["correo"])
    linkedin = esc(PERSONA["linkedin"])
    return [
        NameHeading(PERSONA["nombre"]),
        Paragraph(esc(PERSONA["titulo"]) + " &nbsp;|&nbsp; Ingeniería de Procesos &nbsp;|&nbsp; Analítica Industrial", STYLES["strap"]),
        Paragraph(esc(PERSONA["ciudad"]) + " &nbsp;·&nbsp; " + esc(PERSONA["telefono"]) +
                  f' &nbsp;·&nbsp; <link href="mailto:{email}" color="#1A334F">{email}</link>', STYLES["contact"]),
        Paragraph(f'<link href="https://{linkedin}" color="#1A334F"><u>{linkedin}</u></link>', STYLES["contact"]),
        Spacer(1, 7),
    ]


def paired_heading(first: Paragraph, right: Paragraph, second: Paragraph | None = None,
                   last: Paragraph | None = None) -> Table:
    rows = [[first, right]]
    if second is not None:
        rows.append([second, last or ""])
    tbl = Table(rows, colWidths=[CONTENT_W - 133, 133], hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return tbl


def experience(item: dict) -> KeepTogether:
    employer = Paragraph(
        f'<b>{esc(item["empresa"])}</b> <font color="#526170" size="8.8">· {esc(item["area"])}</font>',
        STYLES["organization"],
    )
    date = par(item["fechas"], "dates")
    role = par(item["cargo"], "role")
    location = par(item["lugar"], "location")
    content = [paired_heading(employer, date, role, location), Spacer(1, 3.8)]
    for achievement in item["logros"]:
        content.append(Paragraph(esc(achievement), STYLES["bullet"], bulletText="•"))
    content.append(Spacer(1, 11.5))
    return KeepTogether(content)


def skill(text: tuple[str, str]) -> Paragraph:
    category, detail = text
    return Paragraph(f'<b>{esc(category)}:</b> {esc(detail)}', STYLES["small"])


def page_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.7)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(PAGE_W - MARGIN_X, 10 * mm, f"{doc.page}")
    if doc.page > 1:
        canvas.setFont("Helvetica", 8.0)
        canvas.drawString(MARGIN_X, PAGE_H - 11.7 * mm, PERSONA["nombre"])
        canvas.setStrokeColor(colors.HexColor("#CFD7DE"))
        canvas.setLineWidth(.4)
        canvas.line(MARGIN_X, PAGE_H - 13.8 * mm, PAGE_W - MARGIN_X, PAGE_H - 13.8 * mm)
    canvas.restoreState()


@st.cache_data(show_spinner=False)
def generar_pdf(perfil: str) -> bytes:
    """CV completo: perfil y logros justificados; listas legibles sin espacios forzados."""
    paragraphs = bloques_perfil(perfil)
    if not paragraphs:
        raise ValueError("El perfil profesional no puede estar vacío.")
    output = BytesIO()
    doc = BaseDocTemplate(
        output, pagesize=A4, leftMargin=MARGIN_X, rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOTTOM,
        title="CV | Enrique Brun Urrutia", author=PERSONA["nombre"],
        subject="Ingeniería de procesos · Analítica industrial", pageCompression=1,
    )
    body = Frame(
        MARGIN_X, MARGIN_BOTTOM, CONTENT_W,
        PAGE_H - MARGIN_TOP - MARGIN_BOTTOM,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id="body",
    )
    doc.addPageTemplates(PageTemplate(id="CV tradicional", frames=[body], onPage=page_footer))

    story = header()
    story.append(SectionHeading("Perfil profesional"))
    story.extend(par(p, "profile") for p in paragraphs)
    story.append(Spacer(1, 2))
    story.append(SectionHeading("Experiencia profesional"))
    # Cuatro experiencias en la primera página; las otras dos y formación en la segunda.
    # Este salto consciente evita dejar una empresa cortada entre páginas.
    for item in EXPERIENCIAS[:4]:
        story.append(experience(item))
    story.append(PageBreak())
    story.append(SectionHeading("Experiencia profesional · continuación", compact=True))
    for item in EXPERIENCIAS[4:]:
        story.append(experience(item))

    story.append(SectionHeading("Educación", compact=True))
    school, degree = FORMACION
    story.append(par(school, "education"))
    story.append(par(degree, "body"))
    story.append(Spacer(1, 5))

    story.append(SectionHeading("Competencias técnicas e idiomas", compact=True))
    story.extend(skill(record) for record in COMPETENCIAS)
    story.append(Spacer(1, 6))

    story.append(SectionHeading("Certificaciones", compact=True))
    for certification in CERTIFICACIONES:
        story.append(Paragraph(esc(certification), STYLES["small"], bulletText="•"))
    story.append(Spacer(1, 5))

    story.append(SectionHeading("Docencia y actividades", compact=True))
    for institution, text in DOCENCIA:
        story.append(Paragraph(f'<b>{esc(institution)}</b> · {esc(text)}', STYLES["small"]))
    story.append(Paragraph(f'<b>Otras actividades:</b> {esc(ACTIVIDADES)}', STYLES["small"]))

    doc.build(story)
    return output.getvalue()


# -----------------------------------------------------------------------------
# CARTA: PDF A4 independiente, con el mismo lenguaje visual del CV.
# -----------------------------------------------------------------------------
LETTER_STYLES = {
    "date": text_style("letter_date", 9.3, 14, SECONDARY, align=TA_RIGHT),
    "recipient": text_style("letter_recipient", 10.0, 15.2, INK, "Helvetica-Bold", after=5),
    "subject": text_style("letter_subject", 9.65, 14.0, NAVY, "Helvetica-Bold", after=4),
    "salutation": text_style("letter_salutation", 10.2, 16.2, INK, after=12),
    "body": text_style("letter_body", 10.15, 16.6, INK, align=TA_JUSTIFY, after=13),
    "signoff": text_style("letter_signoff", 10.2, 15.7, INK, after=1),
    "signature": text_style("letter_signature", 10.2, 15.4, NAVY, "Helvetica-Bold"),
}


def fecha_larga(fecha: datetime) -> str:
    meses = (
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    )
    return f"{fecha.day} de {meses[fecha.month - 1]} de {fecha.year}"


def generar_pdf_carta(texto: str, cargo: str = "", empresa: str = "",
                      fecha: datetime | None = None) -> bytes:
    """Genera únicamente la carta. Nunca combina ni modifica el CV."""
    parrafos = bloques_perfil(texto)
    if not parrafos:
        raise ValueError("La carta de presentación no puede estar vacía.")
    fecha = fecha or datetime.now(ZONA_HORARIA)
    cargo, empresa = cargo.strip(), empresa.strip()
    output = BytesIO()
    doc = BaseDocTemplate(
        output, pagesize=A4,
        leftMargin=22 * mm, rightMargin=22 * mm,
        topMargin=21 * mm, bottomMargin=19 * mm,
        title="Carta de presentación | Enrique Brun Urrutia",
        author=PERSONA["nombre"], subject="Carta de postulación", pageCompression=1,
    )
    body = Frame(
        doc.leftMargin, doc.bottomMargin,
        PAGE_W - doc.leftMargin - doc.rightMargin,
        PAGE_H - doc.topMargin - doc.bottomMargin,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id="letter_body",
    )
    doc.addPageTemplates(PageTemplate(id="Carta", frames=[body]))
    email = esc(PERSONA["correo"])
    story = [
        NameHeading(PERSONA["nombre"]),
        Paragraph(
            esc(PERSONA["titulo"]) + " &nbsp;|&nbsp; Ingeniería de Procesos &nbsp;|&nbsp; Analítica Industrial",
            STYLES["strap"],
        ),
        Paragraph(
            esc(PERSONA["ciudad"]) + " &nbsp;·&nbsp; " + esc(PERSONA["telefono"]) +
            f' &nbsp;·&nbsp; <link href="mailto:{email}" color="#1A334F">{email}</link>',
            STYLES["contact"],
        ),
        Spacer(1, 7),
        SectionHeading("Carta de presentación"),
        Spacer(1, 10),
        Paragraph("Santiago de Chile, " + fecha_larga(fecha), LETTER_STYLES["date"]),
        Spacer(1, 21),
    ]
    if empresa:
        story.append(Paragraph(esc(empresa), LETTER_STYLES["recipient"]))
    if cargo:
        story.append(Paragraph("Postulación: " + esc(cargo), LETTER_STYLES["subject"]))
    if cargo or empresa:
        story.append(Spacer(1, 13))
    story.append(Paragraph("Estimado equipo de selección:", LETTER_STYLES["salutation"]))
    for bloque in parrafos:
        story.append(Paragraph(esc(bloque), LETTER_STYLES["body"]))
    story.extend([
        Spacer(1, 14),
        Paragraph("Atentamente,", LETTER_STYLES["signoff"]),
        Paragraph(esc(PERSONA["nombre"]), LETTER_STYLES["signature"]),
    ])
    doc.build(story)
    return output.getvalue()


# -----------------------------------------------------------------------------
# APP: dos descargas separadas y sin ZIP, dos pestañas, sin barra lateral.
# -----------------------------------------------------------------------------
APP_CSS = """
<style>
.stApp {background: #FCFCFD; color: #1E2730;}
.block-container {max-width: 820px; padding-top: 3.3rem; padding-bottom: 3.0rem;}
[data-testid="stHeader"] {background: transparent;}
#MainMenu, footer, [data-testid="stDecoration"] {display: none;}
.cv-h1 {font-family: Georgia, serif; font-size: clamp(2rem, 4vw, 2.5rem);
        font-weight: 700; line-height: 1.17; color: #1A334F; text-align: center;}
.cv-sub {color: #536171; font-size: .93rem; text-align: center; margin-top: .6rem;}
.cv-rule {border: 0; border-top: 1px solid #718090; margin: 1.8rem 0 1.15rem;}
.cv-section {text-align: center; font-size: .77rem; letter-spacing: .075em;
             color: #1A334F; font-weight: 750; margin: .7rem 0 .6rem;}
.cv-profile {font-size: .97rem; line-height: 1.8; color: #2D3742;
             text-align: justify; text-justify: inter-word; hyphens: auto; margin: .65rem 0 1.45rem;}
.cv-profile p {margin: .65rem 0 .85rem;}
.cv-detail {padding: .88rem 0; border-bottom: 1px solid #E9EDF1;}
.cv-company {font-weight: 750; color: #1A334F; font-size: .94rem;}
.cv-meta {font-size: .80rem; color: #647280; margin-top: .18rem;}
[data-testid="stDownloadButton"] button {
  width: 100%; border-radius: 5px !important; background: #1A334F !important;
  color: #FFFFFF !important; border: 1px solid #1A334F !important;
  min-height: 3.15rem; font-size: 1rem; font-weight: 700;
}
[data-testid="stDownloadButton"] button:hover {background: #294968 !important;}
[data-testid="stTextArea"] textarea {background: #FFFFFF; border-radius: 5px; line-height: 1.6;}
button[data-baseweb="tab"] {font-weight: 600;}
@media(max-width: 650px) { .block-container {padding-top: 2.1rem;} }
</style>
"""


def main() -> None:
    st.set_page_config(page_title="Postulaciones | Enrique Brun Urrutia", layout="centered")
    st.markdown(APP_CSS, unsafe_allow_html=True)

    # Conserva perfiles personalizados en sesiones existentes.
    if st.session_state.get("_perfil_revision") != "industria-justificado-02":
        actual = st.session_state.get("perfil_profesional", PERFIL_BASE_ANTERIOR)
        if actual in (PERFIL_ANTERIOR, PERFIL_BASE_ANTERIOR):
            st.session_state["perfil_profesional"] = PERFIL_BASE
        st.session_state["_perfil_revision"] = "industria-justificado-02"
    st.session_state.setdefault("perfil_profesional", PERFIL_BASE)
    st.session_state.setdefault("texto_carta", CARTA_BASE)
    st.session_state.setdefault("cargo_postulacion", "")
    st.session_state.setdefault("empresa_postulacion", "")

    st.markdown(
        '<div class="cv-h1">ENRIQUE BRUN URRUTIA</div>'
        '<div class="cv-sub">Ingeniería de Procesos &nbsp;·&nbsp; Analítica Industrial &nbsp;·&nbsp; Optimización</div>',
        unsafe_allow_html=True,
    )
    principal, detalles = st.tabs(["Principal", "Detalles"])
    with principal:
        perfil = st.session_state["perfil_profesional"].strip()
        vista_previa = "".join(
            f"<p>{html.escape(p)}</p>" for p in bloques_perfil(perfil)
        )
        st.markdown(
            '<div class="cv-section">PERFIL PROFESIONAL</div><hr class="cv-rule">'
            f'<div class="cv-profile" lang="es">{vista_previa}</div>',
            unsafe_allow_html=True,
        )
        cv_col, carta_col = st.columns(2, gap="medium")
        with cv_col:
            if perfil:
                st.download_button(
                    "Generar CV (PDF)", data=generar_pdf(perfil),
                    file_name=ARCHIVO_PDF, mime="application/pdf",
                    type="primary", use_container_width=True, key="descargar_cv",
                )
            else:
                st.info("Completa el perfil en Detalles.")
        with carta_col:
            texto_carta = st.session_state["texto_carta"].strip()
            if texto_carta:
                try:
                    carta_pdf = generar_pdf_carta(
                        texto_carta,
                        cargo=st.session_state["cargo_postulacion"],
                        empresa=st.session_state["empresa_postulacion"],
                    )
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    st.download_button(
                        "Generar carta (PDF)", data=carta_pdf,
                        file_name=ARCHIVO_CARTA, mime="application/pdf",
                        use_container_width=True, key="descargar_carta",
                    )
            else:
                st.info("Completa la carta en Detalles.")
        st.caption("Dos documentos PDF independientes. Personaliza la carta en Detalles antes de descargarla.")

    with detalles:
        st.text_area(
            "Perfil profesional del CV", key="perfil_profesional", height=220,
            max_chars=3500,
        )
        st.markdown('<div class="cv-section">CARTA DE PRESENTACIÓN</div><hr class="cv-rule">', unsafe_allow_html=True)
        cargo_col, empresa_col = st.columns(2, gap="medium")
        with cargo_col:
            st.text_input(
                "Cargo (opcional)", key="cargo_postulacion", max_chars=120,
                placeholder="Ej.: Ingeniero de Procesos",
            )
        with empresa_col:
            st.text_input(
                "Empresa (opcional)", key="empresa_postulacion", max_chars=120,
                placeholder="Ej.: Empresa objetivo",
            )
        st.text_area(
            "Texto de la carta", key="texto_carta", height=340,
            max_chars=10000, help="Separa los párrafos con una línea en blanco.",
        )
        st.markdown('<div class="cv-section">EXPERIENCIA PROFESIONAL</div><hr class="cv-rule">', unsafe_allow_html=True)
        for item in EXPERIENCIAS:
            st.markdown(
                '<div class="cv-detail">'
                f'<div class="cv-company">{html.escape(item["empresa"])}</div>'
                f'<div class="cv-meta">{html.escape(item["area"])} · {html.escape(item["fechas"])}</div>'
                '</div>', unsafe_allow_html=True,
            )
        st.caption(
            "El CV conserva sus seis experiencias, educación, competencias, certificaciones y docencia. "
            "La carta se descarga por separado."
        )


if __name__ == "__main__":
    main()
