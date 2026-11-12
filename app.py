"""CV profesional | Enrique Brun Urrutia.

Aplicación Streamlit deliberadamente minimalista:
- Dos pestañas: Principal y Detalles.
- Un único botón: «Generar PDF» (genera y descarga en un clic).
- Un solo currículum COMPLETO, en PDF A4 y con texto seleccionable.
- Sin imágenes, barras de habilidades, columnas complejas ni archivos auxiliares.

Instalación: pip install streamlit reportlab
Ejecución:    streamlit run app.py

La experiencia individual se redacta EXCLUSIVAMENTE desde los antecedentes
aportados por el titular. Las referencias públicas al final del archivo explican
el contexto industrial y las convenciones de redacción: NO prueban que una
persona haya realizado las actividades indicadas.
"""

from __future__ import annotations

import html
import os
import re
from io import BytesIO
from xml.sax.saxutils import escape

import streamlit as st
from reportlab import __file__ as REPORTLAB_PATH
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)


# -----------------------------------------------------------------------------
# INFORMACIÓN DEL CURRÍCULUM
# Los títulos, fechas y ubicaciones proceden del archivo aportado por el usuario.
# Verificar antes de postular, en especial fechas simultáneas ENAEX / CCU.
# -----------------------------------------------------------------------------

PERSONA = {
    "nombre": "Enrique Brun Urrutia",
    "titulo": "Ingeniero Civil Químico",
    "especialidad": "Ingeniería de procesos | Analítica industrial | Optimización",
    "ciudad": "Santiago, Chile",
    "telefono": "+56 9 6359 6523",
    "correo": "enrique.brun@usm.cl",
    "linkedin": "linkedin.com/in/enrique-brun-248a02261/",
}

PERFIL_PROFESIONAL = (
    "Ingeniero Civil Químico de la Universidad Técnica Federico Santa María, "
    "con experiencia en minería del cobre y litio, refinación, manufactura y "
    "abastecimiento. Combino ingeniería de procesos, análisis de datos "
    "operacionales y modelamiento predictivo para evaluar desempeño, capacidad "
    "de procesamiento y consumo energético, con especial foco en molienda SAG. "
    "He trabajado en planta y equipos corporativos, utilizando Python, DCS, "
    "AVEVA PI, SAP y herramientas de visualización para convertir información "
    "técnica en apoyo a decisiones de mejora continua."
)

# Orden cronológico inverso por fecha de finalización y después de inicio.
# Estructura: empresa oficial / unidad, cargo, ubicación, periodo, dos aportes.
EXPERIENCIAS = [
    {
        "empresa": "Enaex S.A.",
        "unidad": "Gerencia de Abastecimiento",
        "cargo": "Práctica profesional | Analítica de compras y automatización",
        "ubicacion": "Las Condes, Santiago, Chile",
        "periodo": "abr. 2026 - ago. 2026",
        "aportes": [
            "Integré datos de SAP ERP, SAP Ariba y fuentes externas para analizar compras, contratos y proveedores con criterios de trazabilidad y consistencia.",
            "Automaticé reportes y desarrollé tableros de indicadores para apoyar el seguimiento de proveedores y el control de gestión del abastecimiento.",
        ],
    },
    {
        "empresa": "CCU",
        "unidad": "Planta Modelo Renca | Operaciones",
        "cargo": "Práctica industrial | Indicadores y mejora de procesos",
        "ubicacion": "Renca, Santiago, Chile",
        "periodo": "mar. 2026 - ago. 2026",
        "aportes": [
            "Desarrollé indicadores y tableros para identificar brechas de desempeño en los procesos de elaboración y envasado de la planta.",
            "Analicé variables operacionales y causas de pérdidas para sustentar el diagnóstico y la priorización de oportunidades de mejora continua.",
        ],
    },
    {
        "empresa": "Minera Los Pelambres",
        "unidad": "Planta Concentradora | Ingeniería de Procesos",
        "cargo": "Práctica profesional | Ingeniería de procesos (turno 4x3)",
        "ubicacion": "Salamanca, Región de Coquimbo, Chile",
        "periodo": "ene. 2026 - mar. 2026",
        "aportes": [
            "Analicé históricos del sistema de control distribuido (DCS) para evaluar estabilidad operacional y consumo energético del circuito de molienda SAG.",
            "Contrasté tendencias del proceso con condiciones de equipos y observaciones en terreno, identificando desviaciones y oportunidades de mejora.",
        ],
    },
    {
        "empresa": "SQM",
        "unidad": "International Lithium | Gestión del Conocimiento",
        "cargo": "Práctica | Documentación y transferencia de conocimiento técnico",
        "ubicacion": "Modalidad remota | Proyectos internacionales",
        "periodo": "sept. 2025 - dic. 2025",
        "aportes": [
            "Estandaricé documentación técnica de procesos y operaciones para preservar y organizar conocimiento de proyectos internacionales de litio.",
            "Estructuré antecedentes con criterios de trazabilidad y consulta, facilitando su transferencia a equipos vinculados con Australia y China.",
        ],
    },
    {
        "empresa": "Antofagasta Minerals",
        "unidad": "División de Procesos | Proyecto de Título",
        "cargo": "Proyecto de título | Modelamiento predictivo de molienda SAG",
        "ubicacion": "Las Condes, Santiago, Chile | Oficina corporativa",
        "periodo": "abr. 2025 - nov. 2025",
        "aportes": [
            "Desarrollé y evalué modelos de machine learning para predecir capacidad de procesamiento y consumo específico de energía del circuito SAG de Minera Los Pelambres.",
            "Identifiqué variables operacionales críticas y analicé escenarios con potencial de mejora, aportando evidencia para decisiones de optimización.",
        ],
    },
    {
        "empresa": "ENAP",
        "unidad": "Refinería Aconcagua | División de Procesos",
        "cargo": "Práctica industrial | Monitoreo y análisis de procesos",
        "ubicacion": "Concón, Región de Valparaíso, Chile",
        "periodo": "ene. 2025 - mar. 2025",
        "aportes": [
            "Analicé históricos de AVEVA PI y variables de refinación, complementando el diagnóstico con interpretación de PFD, P&ID y visitas a planta.",
            "Elaboré análisis estadísticos y reportes de tendencias e indicadores para apoyar el monitoreo del desempeño operacional.",
        ],
    },
]

EDUCACION = {
    "institucion": "Universidad Técnica Federico Santa María (UTFSM)",
    "programa": "Ingeniería Civil Química",
    "ubicacion": "Casa Central, Valparaíso, Chile",
    "periodo": "2020 - 2026",
}

COMPETENCIAS = [
    (
        "Ingeniería y simulación",
        "Aspen Plus, Aspen HYSYS, JKSimMet, Integrated Extraction Simulator (IES), "
        "AVEVA PI System, interpretación de PFD y P&ID.",
    ),
    (
        "Datos y modelamiento",
        "Python (pandas, scikit-learn), SQL, estadística aplicada, machine learning "
        "y modelos predictivos.",
    ),
    (
        "Visualización y automatización",
        "Power BI (Power Query, DAX), Excel avanzado, Power Automate, "
        "Microsoft Azure y Microsoft Fabric.",
    ),
    (
        "Gestión y mejora continua",
        "SAP ERP, SAP Ariba, indicadores de desempeño, Lean, Six Sigma y análisis de causa raíz.",
    ),
    (
        "Idiomas",
        "Español nativo; inglés C1 Advanced (certificación EF SET, jul. 2025).",
    ),
]

CERTIFICACIONES = [
    "JKSimMet | Simulación y optimización de conminución, The University of Queensland | ago. 2025",
    "Integrated Extraction Simulator (IES) | Conminución, Orica | jul. 2025",
    "Power BI y Excel | SERGROUP | 2025",
    "EF SET English Certificate | C1 Advanced | jul. 2025",
]

DOCENCIA = [
    (
        "Universidad Técnica Federico Santa María",
        "Ayudante y coordinador (2021 - 2025) en Diseño y Análisis de Procesos, "
        "Cristalización, Química y Física General I, entre otras asignaturas.",
    ),
    (
        "Preuniversitario CPECH",
        "Docente de Matemáticas, Química, Biología y Física para preparación PAES | Viña del Mar, Chile.",
    ),
]

ACTIVIDADES = (
    "AIESEC Chile: vicepresidente de Marketing | PREUSM: docente y coordinador "
    "de voluntariado PAES | Escuela Santa María: voluntariado en Matemáticas | "
    "CETAM: participación en Expedición Científica Andes."
)

ARCHIVO_PDF = "CV_Enrique_Brun_Urrutia_Completo.pdf"
AZUL_MARINO = colors.HexColor("#142B45")
AZUL_MEDIO = colors.HexColor("#44617D")
GRIS_TEXTO = colors.HexColor("#263646")
GRIS_SUAVE = colors.HexColor("#607084")
LINEA = colors.HexColor("#D7DEE6")


# -----------------------------------------------------------------------------
# COMPOSICIÓN DEL PDF (una sola columna, texto real, tipografía incrustada)
# Usa tipografías Vera incluidas con ReportLab, sin archivos del proyecto.
# -----------------------------------------------------------------------------

def registrar_fuentes() -> tuple[str, str]:
    font_dir = os.path.join(os.path.dirname(REPORTLAB_PATH), "fonts")
    normal = os.path.join(font_dir, "Vera.ttf")
    negrita = os.path.join(font_dir, "VeraBd.ttf")
    if not (os.path.isfile(normal) and os.path.isfile(negrita)):
        return "Helvetica", "Helvetica-Bold"
    if "CV-Regular" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("CV-Regular", normal))
    if "CV-Bold" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("CV-Bold", negrita))
    pdfmetrics.registerFontFamily("CV-Regular", normal="CV-Regular", bold="CV-Bold")
    return "CV-Regular", "CV-Bold"


def estilos() -> dict[str, ParagraphStyle]:
    regular, bold = registrar_fuentes()
    base = ParagraphStyle(
        "base", fontName=regular, fontSize=9.1, leading=12.7,
        textColor=GRIS_TEXTO, alignment=TA_LEFT, spaceAfter=0,
    )
    return {
        "nombre": ParagraphStyle(
            "nombre", parent=base, fontName=bold, fontSize=21.5, leading=25.2,
            textColor=AZUL_MARINO, spaceAfter=5,
        ),
        "titulo": ParagraphStyle(
            "titulo", parent=base, fontName=bold, fontSize=9.7, leading=13.1,
            textColor=AZUL_MARINO, spaceAfter=3,
        ),
        "especialidad": ParagraphStyle(
            "especialidad", parent=base, fontSize=9.05, leading=12,
            textColor=AZUL_MEDIO, spaceAfter=9,
        ),
        "contacto": ParagraphStyle(
            "contacto", parent=base, fontSize=8.35, leading=12,
            textColor=GRIS_SUAVE, spaceAfter=2,
        ),
        "perfil": ParagraphStyle(
            "perfil", parent=base, fontSize=9.3, leading=13.4,
            spaceAfter=7,
        ),
        "empresa": ParagraphStyle(
            "empresa", parent=base, fontName=bold, fontSize=9.6,
            leading=12.2, textColor=AZUL_MARINO, spaceAfter=2, keepWithNext=True,
        ),
        "cargo": ParagraphStyle(
            "cargo", parent=base, fontSize=8.9,
            leading=11.5, textColor=AZUL_MEDIO, spaceAfter=2, keepWithNext=True,
        ),
        "meta": ParagraphStyle(
            "meta", parent=base, fontSize=8.05,
            leading=11, textColor=GRIS_SUAVE, spaceAfter=4, keepWithNext=True,
        ),
        "aporte": ParagraphStyle(
            "aporte", parent=base, fontSize=8.95,
            leading=12.25, leftIndent=12, firstLineIndent=-8,
            spaceAfter=4,
        ),
        "dato": ParagraphStyle(
            "dato", parent=base, fontSize=8.85, leading=12.35, spaceAfter=4,
        ),
        "reducido": ParagraphStyle(
            "reducido", parent=base, fontSize=8.65, leading=12, spaceAfter=4,
        ),
    }


class TituloSeccion(Flowable):
    """Sección sutil, sin cajas ni fondos coloreados."""

    def __init__(self, titulo: str) -> None:
        super().__init__()
        self.titulo = titulo.upper()
        self.height = 25
        self.keepWithNext = True

    def wrap(self, ancho: float, alto: float) -> tuple[float, float]:
        self.width = ancho
        return ancho, self.height

    def draw(self) -> None:
        self.canv.saveState()
        self.canv.setFillColor(AZUL_MARINO)
        self.canv.setFont("CV-Bold" if "CV-Bold" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold", 8.5)
        self.canv.drawString(0, 9.4, self.titulo)
        self.canv.setStrokeColor(LINEA)
        self.canv.setLineWidth(0.7)
        self.canv.line(0, 5, self.width, 5)
        self.canv.restoreState()


def pagina(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(LINEA)
    canvas.setLineWidth(0.45)
    canvas.line(18 * mm, 13.4 * mm, A4[0] - 18 * mm, 13.4 * mm)
    normal, _ = registrar_fuentes()
    canvas.setFont(normal, 7.25)
    canvas.setFillColor(GRIS_SUAVE)
    canvas.drawRightString(A4[0] - 18 * mm, 9.9 * mm, str(doc.page))
    canvas.restoreState()


def p(texto: str, estilo: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(texto), estilo)


def generar_pdf(perfil: str) -> bytes:
    """Genera siempre la versión COMPLETA, sin una etapa de confirmación extra."""
    if not perfil.strip():
        raise ValueError("El perfil profesional no puede estar vacío.")

    salida = BytesIO()
    doc = SimpleDocTemplate(
        salida, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=18 * mm,
        title="CV | Enrique Brun Urrutia",
        author=PERSONA["nombre"],
        subject="Ingeniería de procesos y analítica industrial",
        pageCompression=1,
    )
    s = estilos()
    story = [
        p(PERSONA["nombre"], s["nombre"]),
        p(PERSONA["titulo"], s["titulo"]),
        p(PERSONA["especialidad"], s["especialidad"]),
    ]

    telefono = re.sub(r"[^+0-9]", "", PERSONA["telefono"])
    contacto = (
        f'{escape(PERSONA["ciudad"])} &nbsp; | &nbsp; '
        f'<link href="tel:{telefono}" color="#607084">{escape(PERSONA["telefono"])}</link>'
        f' &nbsp; | &nbsp; <link href="mailto:{escape(PERSONA["correo"])}" color="#607084">'
        f'{escape(PERSONA["correo"])}</link>'
    )
    story.append(Paragraph(contacto, s["contacto"]))
    url_linkedin = "https://" + PERSONA["linkedin"]
    story.append(Paragraph(
        f'<link href="{escape(url_linkedin)}" color="#607084">'
        f'{escape(PERSONA["linkedin"].rstrip("/"))}</link>',
        s["contacto"],
    ))
    story.append(Spacer(1, 7))

    story.append(TituloSeccion("Perfil profesional"))
    for parrafo in re.split(r"\n\s*\n", perfil.strip()):
        if parrafo.strip():
            story.append(p(" ".join(parrafo.split()), s["perfil"]))

    story.append(TituloSeccion("Experiencia profesional"))
    for i, item in enumerate(EXPERIENCIAS):
        if i == 4:
            story.append(PageBreak())
            story.append(TituloSeccion("Experiencia profesional | continuación"))
        bloque = [
            p(f'{item["empresa"]}  |  {item["unidad"]}', s["empresa"]),
            p(item["cargo"], s["cargo"]),
            p(f'{item["ubicacion"]}   ·   {item["periodo"]}', s["meta"]),
        ]
        for aporte in item["aportes"]:
            bloque.append(Paragraph("<font color='#44617D'>•</font>  " + escape(aporte), s["aporte"]))
        story.append(KeepTogether(bloque))
        story.append(Spacer(1, 5))

    story.append(TituloSeccion("Formación académica"))
    story.extend([
        p(EDUCACION["institucion"], s["empresa"]),
        p(
            f'{EDUCACION["programa"]}  |  {EDUCACION["ubicacion"]}  |  {EDUCACION["periodo"]}',
            s["dato"],
        ),
    ])

    story.append(TituloSeccion("Competencias técnicas e idiomas"))
    for etiqueta, contenido in COMPETENCIAS:
        story.append(Paragraph(
            f'<b>{escape(etiqueta)}:</b> {escape(contenido)}', s["dato"],
        ))

    story.append(TituloSeccion("Certificaciones"))
    for certificado in CERTIFICACIONES:
        story.append(p(certificado, s["reducido"]))

    story.append(TituloSeccion("Docencia y liderazgo"))
    for organizacion, descripcion in DOCENCIA:
        story.append(Paragraph(
            f'<b>{escape(organizacion)}:</b> {escape(descripcion)}', s["reducido"],
        ))
    story.append(Paragraph(
        f'<b>Otras actividades:</b> {escape(ACTIVIDADES)}', s["reducido"],
    ))

    doc.build(story, onFirstPage=pagina, onLaterPages=pagina)
    return salida.getvalue()


# -----------------------------------------------------------------------------
# INTERFAZ: SOLO DOS PESTAÑAS Y UN BOTÓN DE DESCARGA/GENERACIÓN.
# -----------------------------------------------------------------------------
CSS = """
<style>
:root { color-scheme:light; }
.stApp { background: #FFFFFF; color:#142B45; }
.block-container { max-width:800px; padding-top:3rem; padding-bottom:4rem; }
#MainMenu, footer, [data-testid="stDecoration"] { visibility:hidden; }
[data-testid="stHeader"] { background:transparent; }
.cv-kicker {color:#607084; font-size:.72rem; letter-spacing:.14em;
            font-weight:700; margin-bottom:.4rem;}
.cv-name {font-size:2.05rem; letter-spacing:-.045em; line-height:1.16;
          font-weight:730; color:#142B45; margin:0 0 .35rem;}
.cv-role {font-size:1rem; color:#44617D; margin-bottom:2rem;}
.cv-profile {font-size:.98rem; line-height:1.72; color:#34465A;
             padding:1.35rem 0 .8rem; max-width:720px;}
.cv-minor {font-size:.85rem; color:#607084; line-height:1.5;}
[data-baseweb="tab-list"] { gap:1.4rem; border-bottom:1px solid #DFE4EA; }
button[data-baseweb="tab"] { font-weight:550; }
[data-testid="stDownloadButton"] button {
    background:#142B45 !important; color:white !important;
    border:1px solid #142B45 !important; border-radius:7px !important;
    box-shadow:none !important; min-height:3.05rem;
    padding:0 1.7rem !important; font-weight:650; letter-spacing:.005em;
}
[data-testid="stDownloadButton"] button:hover { background:#29445F !important; }
[data-testid="stTextArea"] textarea {
    border-radius:7px; background:#FFFFFF; color:#142B45;
    line-height:1.6; font-size:.96rem;
}
.cv-exp {padding:12px 0; border-bottom:1px solid #EBEFF3;}
.cv-exp strong {color:#142B45; font-size:.94rem;}
.cv-exp .details {color:#607084; font-size:.80rem; margin:3px 0;}
.cv-exp p {font-size:.88rem; color:#34465A; line-height:1.5; margin:3px 0;}
@media(max-width:640px) {.block-container{padding-top:2.0rem}.cv-name{font-size:1.75rem}}
</style>
"""


@st.cache_data(show_spinner=False)
def pdf_cacheado(perfil: str) -> bytes:
    return generar_pdf(perfil)


def main() -> None:
    st.set_page_config(page_title="CV | Enrique Brun Urrutia", layout="centered")
    st.markdown(CSS, unsafe_allow_html=True)
    if "perfil_cv" not in st.session_state:
        st.session_state["perfil_cv"] = PERFIL_PROFESIONAL

    st.markdown(
        '<div class="cv-kicker">CURRÍCULUM PROFESIONAL</div>'
        f'<div class="cv-name">{html.escape(PERSONA["nombre"])}</div>'
        f'<div class="cv-role">{html.escape(PERSONA["titulo"])} · '
        'Ingeniería de Procesos y Analítica Industrial</div>',
        unsafe_allow_html=True,
    )

    principal, detalles = st.tabs(["Principal", "Detalles"])

    with principal:
        perfil = st.session_state["perfil_cv"].strip()
        st.markdown(
            '<div class="cv-profile">'
            + html.escape(perfil).replace("\n", "<br>")
            + '</div>',
            unsafe_allow_html=True,
        )
        if perfil:
            # Este es el único botón de toda la aplicación.
            st.download_button(
                label="Generar PDF",
                data=pdf_cacheado(perfil),
                file_name=ARCHIVO_PDF,
                mime="application/pdf",
                type="primary",
                use_container_width=True,
                key="generar_pdf",
            )
        else:
            st.error("Completa el perfil profesional en la pestaña Detalles.")

    with detalles:
        st.text_area(
            "Perfil profesional",
            key="perfil_cv",
            height=210,
            max_chars=4000,
        )
        st.markdown('<p class="cv-minor">Experiencias incluidas en el PDF completo</p>',
                    unsafe_allow_html=True)
        for item in EXPERIENCIAS:
            aportes = "".join(f"<p>{html.escape(linea)}</p>" for linea in item["aportes"])
            st.markdown(
                '<div class="cv-exp">'
                f'<strong>{html.escape(item["empresa"])} · {html.escape(item["unidad"])}</strong>'
                f'<div class="details">{html.escape(item["cargo"])} · '
                f'{html.escape(item["ubicacion"])} · {html.escape(item["periodo"])}</div>'
                f'{aportes}</div>', unsafe_allow_html=True,
            )
        st.caption("El PDF incluye formación, herramientas, idiomas, certificaciones, docencia y liderazgo.")


# -----------------------------------------------------------------------------
# REFERENCIAS DE CONTEXTO - cuatro o más fuentes por experiencia.
# Consultadas en noviembre de 2026. NO verifican logros individuales.
# No aparecen en el CV, porque son referencias de investigación/redacción.
# -----------------------------------------------------------------------------
FUENTES_CV_INTERNACIONAL = [
    "https://capd.mit.edu/resources/resumes/",
    "https://careerservices.fas.harvard.edu/resources/create-a-strong-resume/",
    "https://ocs.yale.edu/resources/writing-impactful-resume-bullets/",
    "https://ocs.yale.edu/channels/resumes/",
    "https://www.naceweb.org/career-readiness/competencies/career-readiness-defined/",
]

FUENTES_POR_EXPERIENCIA = {
    "Enaex": [
        "https://www.enaex.com/cl/es/supplier-portal/",
        "https://www.enaex.com/br/us/enaex-international-rise/",
        "https://help.sap.com/docs/ARIBA_SOURCING",
        "https://www.sap.com/products/spend-management/supplier-management.html",
        "https://learning.sap.com/products/intelligent-spend-management/ariba/spend-analysis",
    ],
    "CCU - Planta Modelo Renca": [
        "https://laetitia.usach.cl/trabajar-en-compania-cervecerias-unidas/trabajos/practica-en-estandarizacion-sala-de-elaboracion/927071",
        "https://www.ccu.cl/wp-content/uploads/2025/04/Memoria_Integrada_CCU_2024.pdf",
        "https://www.ccu.cl/planta-temuco-de-ccu-logra-importantes-certificaciones/",
        "https://www.ccu.cl/nueva-planta-embotelladora-ccu-renca/",
        # ATENCIÓN: la última fuente documenta otra planta de CCU en Renca;
        # se utiliza para distinguirla correctamente de Planta Modelo Renca.
    ],
    "Minera Los Pelambres": [
        "https://intranet.aminerals.cl/Noticias/Detalle/2169",
        "https://consejominero.cl/nosotros/socios/antofagasta-minerals/",
        "https://www.aminerals.cl/centro-de-informacion/resultados-de-produccion",
        "https://www.sciencedirect.com/science/article/pii/S0892687525003796",
        "https://www.mdpi.com/2075-163X/16/4/412",
    ],
    "SQM - International Lithium": [
        "https://ir.sqm.com/es",
        "https://ir.sqm.com/static-files/ea38d208-65e2-4e5a-a636-afc2e2794c27",
        "https://www.iso.org/standard/68683.html",
        "https://www.apqc.org/expertise/knowledge-management/km-approaches",
        "https://www.apqc.org/How-can-knowledge-practices-improve-onboarding-and-offboarding",
    ],
    "Antofagasta Minerals": [
        "https://sr2025.antofagasta.co.uk/cl",
        "https://www.aminerals.cl/reporte-de-sustentabilidad",
        "https://intranet.aminerals.cl/Noticias/Detalle/2169",
        "https://www.sciencedirect.com/science/article/pii/S0892687525003796",
        "https://www.mdpi.com/2075-163X/16/4/412",
    ],
    "ENAP - Refinería Aconcagua": [
        "https://www.enap.cl/nuestras-operaciones/refinacion-y-comercializacion-rc/activos-nacionales/refineria-aconcagua",
        "https://www.enap.cl/nuestras-operaciones/refinacion-y-comercializacion-rc/procesos-de-transformacion/refinacion",
        "https://www.enap.cl/sala-de-prensa/comision-de-evaluacion-ambiental-aprueba-proyecto-para-mejorar-gestion-ambiental-en-refineria-aconcagua",
        "https://www.aveva.com/en/perspectives/presentations/2023/pertamina--journey-to-operational-excellence---aveva--pi-system--transformative-influence-at-pertamina/",
        "https://www.aveva.com/en/perspectives/presentations/2017/pi-system-technology-to-drive-refinery-oil-accounting/",
    ],
}


if __name__ == "__main__":
    main()
