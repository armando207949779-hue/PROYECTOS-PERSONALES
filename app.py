"""Editor de CV y carta de presentación. Ejecutar: streamlit run app.py"""

from __future__ import annotations

import hashlib
import html
import json
import re
import unicodedata
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer


# Todos los datos iniciales son ficticios. Cambia este diccionario si deseas
# personalizar la plantilla que aparece al iniciar una sesión nueva.
DEFAULTS = {
    "name": "Alex Pérez",
    "role": "Analista de operaciones",
    "email": "alex.perez@example.com",
    "phone": "+56 9 1234 5678",
    "location": "Santiago, Chile",
    "links": "linkedin.com/in/tu-perfil",
    "summary": (
        "Profesional con experiencia en coordinación administrativa, análisis de "
        "información y mejora de procesos. Me caracterizo por la organización, "
        "la comunicación clara y el trabajo en equipo. Busco aportar a una "
        "organización orientada a la calidad y la mejora continua."
    ),
    "experience": (
        "Analista de operaciones | Empresa Ejemplo | 2023 - Actualidad\n"
        "- Coordino tareas operativas y el seguimiento de solicitudes internas.\n"
        "- Elaboro reportes para apoyar la planificación y la toma de decisiones.\n"
        "- Colaboro con distintas áreas para mejorar procedimientos.\n\n"
        "Asistente administrativo | Organización Ejemplo | 2021 - 2023\n"
        "- Gestioné documentación y mantuve actualizados los registros del área.\n"
        "- Apoyé la atención de clientes y la coordinación de actividades."
    ),
    "education": (
        "Administración de Empresas | Instituto Ejemplo | 2017 - 2021\n"
        "Formación en gestión, planificación y análisis de información."
    ),
    "skills": "Excel · Análisis de datos · Organización · Comunicación · Trabajo en equipo",
    "languages": "Español: nativo. Inglés: intermedio.",
    "additional": "",
    "company": "Empresa Ejemplo",
    "job": "Analista de operaciones",
    "recipient": "Equipo de selección",
    "letter_date": "Santiago, [fecha de envío]",
    "greeting": "Estimado equipo de selección:",
    "letter_body": (
        "Me interesa postular al cargo de Analista de operaciones en Empresa "
        "Ejemplo. Mi experiencia en coordinación administrativa y seguimiento "
        "de procesos se relaciona con las responsabilidades de esta posición.\n\n"
        "En mis experiencias anteriores he apoyado la elaboración de reportes, "
        "la gestión de documentación y la coordinación entre equipos. Me "
        "caracterizo por trabajar con orden, comunicarme con claridad y buscar "
        "oportunidades de mejora en las tareas diarias.\n\n"
        "Me motiva la posibilidad de aportar mis conocimientos y seguir "
        "desarrollándome profesionalmente en su organización. Quedo disponible "
        "para conversar sobre cómo mi perfil puede contribuir a su equipo.\n\n"
        "Gracias por su tiempo y consideración."
    ),
    "closing": "Atentamente,",
}

FIELD_LIMITS = {
    "name": 120, "role": 160, "email": 254, "phone": 80,
    "location": 160, "links": 500, "summary": 3000,
    "experience": 12000, "education": 6000, "skills": 2000,
    "languages": 1000, "additional": 4000, "company": 200,
    "job": 200, "recipient": 200, "letter_date": 160,
    "greeting": 300, "letter_body": 12000, "closing": 200,
}

CV_SECTIONS = (
    ("Perfil profesional", "summary", False),
    ("Experiencia profesional", "experience", True),
    ("Formación académica", "education", True),
    ("Habilidades", "skills", False),
    ("Idiomas", "languages", False),
    ("Información adicional", "additional", False),
)
SHARED_KEYS = ("name", "email", "phone", "location", "links")
LETTER_KEYS = SHARED_KEYS + (
    "company", "job", "recipient", "letter_date", "greeting", "letter_body", "closing"
)
CV_KEYS = SHARED_KEYS + ("role",) + tuple(section[1] for section in CV_SECTIONS)

CSS = """
<style>
.stApp { background: white; color: black; }
.block-container { max-width: 1320px; padding-top: 2rem; }
h1, h2, h3 { letter-spacing: -.03em; }
.cv-sheet {
    background: white; color: black; border: 1px solid #ddd;
    padding: 38px 40px; font-family: Arial, sans-serif; font-size: 13px;
    line-height: 1.6; overflow-wrap: anywhere;
}
.cv-sheet h1 { font-size: 28px; margin: 0; line-height: 1.2; color: black; }
.cv-sheet .role { font-size: 15px; margin: 6px 0; }
.cv-sheet .contact { font-size: 11px; line-height: 1.6; }
.cv-sheet hr { border: 0; border-top: 1px solid black; margin: 18px 0 20px; }
.cv-sheet h2 {
    font-size: 11px; text-transform: uppercase; letter-spacing: 1.4px;
    margin: 21px 0 8px; color: black;
}
.cv-sheet p { margin: 0 0 10px; }
.cv-sheet .entry { margin-bottom: 12px; }
.cv-sheet .bullet { padding-left: 13px; text-indent: -10px; margin: 3px 0; }
.cv-sheet .date { text-align: right; margin-bottom: 25px; }
.cv-sheet .recipient { margin-bottom: 20px; }
.cv-sheet .signature { margin-top: 23px; }
@media (max-width: 700px) {
    .cv-sheet { padding: 24px 20px; }
    .block-container { padding-top: 1rem; }
}
</style>
"""


def clean(text: str) -> str:
    """Normaliza saltos, espacios y caracteres de control para ambos formatos."""
    text = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", "    ").replace("\xa0", " ")
    text = text.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
    return "".join(c for c in text if c == "\n" or unicodedata.category(c) != "Cc").strip()


def paragraphs(text: str) -> list[list[str]]:
    return [
        [line.strip() for line in block.splitlines() if line.strip()]
        for block in re.split(r"\n\s*\n", clean(text)) if block.strip()
    ]


def is_bullet(line: str) -> bool:
    return line.startswith(("- ", "• "))


def text_html(text: str, structured: bool = False) -> str:
    blocks = []
    for lines in paragraphs(text):
        rendered = []
        for index, line in enumerate(lines):
            if is_bullet(line):
                rendered.append(f'<div class="bullet">• {html.escape(line[2:])}</div>')
            elif structured and index == 0:
                rendered.append(f"<strong>{html.escape(line)}</strong>")
            else:
                rendered.append(f"<div>{html.escape(line)}</div>")
        blocks.append('<div class="entry">' + "".join(rendered) + "</div>")
    return "".join(blocks)


def contact_lines(data: dict) -> list[str]:
    return [
        " | ".join(data[key] for key in ("location", "phone", "email") if data[key]),
        data["links"],
    ]


def preview_html(data: dict, kind: str) -> str:
    contact = "<br>".join(html.escape(line) for line in contact_lines(data) if line)
    result = '<article class="cv-sheet">'
    result += f'<h1>{html.escape(data["name"])}</h1>'
    if kind == "cv" and data["role"]:
        result += f'<div class="role">{html.escape(data["role"])}</div>'
    result += f'<div class="contact">{contact}</div><hr>'
    if kind == "cv":
        for title, key, structured in CV_SECTIONS:
            if data[key]:
                result += f"<h2>{title}</h2>" + text_html(data[key], structured)
    else:
        result += f'<div class="date">{html.escape(data["letter_date"])}</div>'
        recipient = "<br>".join(html.escape(data[k]) for k in ("recipient", "company") if data[k])
        result += f'<div class="recipient">{recipient}</div>'
        if data["job"]:
            result += f'<p><strong>Postulación: {html.escape(data["job"])}</strong></p>'
        result += text_html(data["greeting"]) + text_html(data["letter_body"])
        result += '<div class="signature">' + text_html(data["closing"])
        result += f'<strong>{html.escape(data["name"])}</strong></div>'
    return result + "</article>"


def register_fonts() -> None:
    """Las fuentes vienen con ReportLab: no hay descargas ni binarios externos."""
    folder = Path(reportlab.__file__).parent / "fonts"
    for name, filename in (("CVSans", "Vera.ttf"), ("CVSansBold", "VeraBd.ttf")):
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(folder / filename)))


def validate_characters(data: dict, kind: str) -> None:
    keys = CV_KEYS if kind == "cv" else LETTER_KEYS
    fonts = [pdfmetrics.getFont(name).face.charToGlyph for name in ("CVSans", "CVSansBold")]
    missing = sorted({
        c for key in keys for c in data[key]
        if not c.isspace() and any(ord(c) not in glyphs for glyphs in fonts)
    })
    if missing:
        raise ValueError(
            "La fuente del PDF no incluye estos caracteres: "
            + " ".join(missing[:12])
            + ". Reemplázalos por texto simple (evita emojis)."
        )


def make_pdf(data: dict, kind: str = "cv", paper: str = "A4", font_size: int = 10) -> bytes:
    """Crea un PDF con texto seleccionable y paginación automática en memoria."""
    if kind not in ("cv", "letter"):
        raise ValueError("Tipo de documento no válido.")
    data = {key: clean(str(data.get(key, ""))) for key in DEFAULTS}
    register_fonts()
    validate_characters(data, kind)
    buffer = BytesIO()
    body = ParagraphStyle(
        "Body", fontName="CVSans", fontSize=font_size, leading=font_size * 1.48,
        spaceAfter=5, textColor=colors.black, splitLongWords=True,
    )
    bold = ParagraphStyle("Bold", parent=body, fontName="CVSansBold", spaceBefore=2)
    bullet = ParagraphStyle("Bullet", parent=body, leftIndent=10, firstLineIndent=0,
                            bulletIndent=0, bulletFontName="CVSans", bulletFontSize=font_size)
    name = ParagraphStyle("Name", parent=bold, fontSize=23, leading=28, spaceAfter=5)
    role = ParagraphStyle("Role", parent=body, fontSize=11, leading=16)
    contact = ParagraphStyle("Contact", parent=body, fontSize=8.3, leading=12)
    section = ParagraphStyle("Section", parent=bold, fontSize=9, leading=13,
                             spaceBefore=12, spaceAfter=7, keepWithNext=True)
    date = ParagraphStyle("Date", parent=body, alignment=2, spaceAfter=20)
    story = [Paragraph(escape(data["name"]), name)]
    if kind == "cv" and data["role"]:
        story.append(Paragraph(escape(data["role"]), role))
    for line in contact_lines(data):
        if line:
            story.append(Paragraph(escape(line), contact))
    story.extend([Spacer(1, 9), HRFlowable(width="100%", thickness=.7, color=colors.black), Spacer(1, 13)])

    def add_text(text: str, structured: bool = False) -> None:
        for lines in paragraphs(text):
            for index, line in enumerate(lines):
                if is_bullet(line):
                    story.append(Paragraph(escape(line[2:]), bullet, bulletText="•"))
                elif structured and index == 0:
                    entry_style = ParagraphStyle("Entry", parent=bold, keepWithNext=len(lines) > 1)
                    story.append(Paragraph(escape(line), entry_style))
                else:
                    story.append(Paragraph(escape(line), body))
            story.append(Spacer(1, 4))

    if kind == "cv":
        for title, key, structured in CV_SECTIONS:
            if data[key]:
                story.append(Paragraph(escape(title.upper()), section))
                add_text(data[key], structured)
    else:
        if data["letter_date"]:
            story.append(Paragraph(escape(data["letter_date"]), date))
        for key in ("recipient", "company"):
            if data[key]:
                story.append(Paragraph(escape(data[key]), body))
        story.append(Spacer(1, 10))
        if data["job"]:
            story.append(Paragraph("Postulación: " + escape(data["job"]), bold))
            story.append(Spacer(1, 8))
        add_text(data["greeting"])
        add_text(data["letter_body"])
        story.append(Spacer(1, 12))
        add_text(data["closing"])
        story.append(Paragraph(escape(data["name"]), bold))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("CVSans", 8)
        canvas.setFillColor(colors.black)
        canvas.drawRightString(doc.pagesize[0] - 18 * mm, 11 * mm, str(doc.page))
        canvas.restoreState()

    title = "CV" if kind == "cv" else "Carta de presentación"
    doc = SimpleDocTemplate(
        buffer, pagesize=A4 if paper == "A4" else letter,
        rightMargin=18 * mm, leftMargin=18 * mm, topMargin=17 * mm,
        bottomMargin=19 * mm, title=f'{title} - {data["name"]}', author=data["name"],
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()


def snapshot() -> dict:
    return {key: clean(st.session_state[key]) for key in DEFAULTS}


def fingerprint(data: dict, kind: str, paper: str, font_size: int) -> str:
    keys = CV_KEYS if kind == "cv" else LETTER_KEYS
    payload = {key: data[key] for key in keys}
    payload.update(paper=paper, font_size=font_size)
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def safe_filename(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_")[:70] or "documento"


def parse_backup(raw: bytes) -> dict:
    if len(raw) > 512_000:
        raise ValueError("El respaldo debe pesar menos de 500 KB.")
    try:
        payload = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("El archivo no contiene un JSON válido.") from exc
    if not isinstance(payload, dict) or payload.get("version") != 1:
        raise ValueError("El archivo no es un respaldo compatible con esta app.")
    fields = payload.get("fields")
    if not isinstance(fields, dict) or set(fields) - set(DEFAULTS):
        raise ValueError("El respaldo contiene campos no válidos.")
    if any(not isinstance(value, str) or len(value) > FIELD_LIMITS[key]
           for key, value in fields.items()):
        raise ValueError("El respaldo contiene textos no válidos o demasiado extensos.")
    # Un respaldo incompleto no debe mezclar sus datos con los de otra persona.
    return {key: clean(fields.get(key, "")) for key in DEFAULTS}


def import_backup() -> None:
    uploaded = st.session_state.get("backup_upload")
    if uploaded is None:
        st.session_state["_import_message"] = (False, "Selecciona un archivo JSON primero.")
        return
    try:
        values = parse_backup(uploaded.getvalue())
    except ValueError as exc:
        st.session_state["_import_message"] = (False, str(exc))
        return
    st.session_state.update(values)
    st.session_state.pop("_pdf_cv", None)
    st.session_state.pop("_pdf_letter", None)
    st.session_state["_import_message"] = (True, "Textos cargados. Revisa los datos antes de generar el PDF.")


def export_controls(data: dict, kind: str, paper: str, font_size: int) -> None:
    label = "CV" if kind == "cv" else "carta"
    current = fingerprint(data, kind, paper, font_size)
    state_key = "_pdf_" + kind
    previous = st.session_state.get(state_key)
    if previous and previous["fingerprint"] != current:
        st.session_state.pop(state_key)
        previous = None
        st.info("El contenido cambió. Confirma la nueva versión para descargarla.")
    if st.button(f"Confirmar y generar PDF del {label}" if kind == "cv" else "Confirmar y generar PDF de la carta",
                 key="generate_" + kind, type="primary", width="stretch"):
        error = ""
        if not data["name"]:
            error = "Completa tu nombre en la pestaña CV."
        elif kind == "cv" and not any(data[key] for _, key, _ in CV_SECTIONS):
            error = "Completa al menos una sección del CV."
        elif kind == "letter" and not all(data[key] for key in ("company", "job", "letter_body")):
            error = "Completa empresa, cargo y cuerpo de la carta."
        if error:
            st.error(error)
        else:
            try:
                pdf = make_pdf(data, kind, paper, font_size)
            except ValueError as exc:
                st.error(str(exc))
            else:
                previous = {"fingerprint": current, "data": pdf}
                st.session_state[state_key] = previous
    if previous:
        target = data["role"] if kind == "cv" else data["company"]
        filename = f'{label}_{safe_filename(data["name"])}_{safe_filename(target)}.pdf'
        st.success("PDF listo. Puedes descargarlo abajo.")
        st.download_button(f"Descargar {label} en PDF", previous["data"], filename,
                           mime="application/pdf", key="download_" + kind, width="stretch")


def main() -> None:
    st.set_page_config(page_title="Mi CV | Editor de postulaciones", layout="wide")
    st.html(CSS)
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)

    with st.sidebar:
        st.title("Mi CV")
        st.caption("Textos claros. Diseño simple.")
        paper = st.selectbox("Tamaño de página", ("A4", "Carta"))
        font_size = st.select_slider("Tamaño de texto del PDF", options=(9, 10, 11), value=10)
        st.divider()
        st.markdown("**Recuperar mis textos**")
        st.file_uploader("Cargar respaldo JSON", type=("json",), key="backup_upload")
        st.button("Aplicar respaldo", on_click=import_backup, width="stretch")
        message = st.session_state.pop("_import_message", None)
        if message:
            (st.success if message[0] else st.error)(message[1])
        backup_slot = st.empty()
        st.caption("Guarda un respaldo antes de cerrar. Los textos se mantienen solo durante la sesión.")
        st.caption("La app no guarda tus datos en GitHub ni usa servicios de IA. Los campos iniciales son ficticios.")

    st.title("Una postulación, a tu medida.")
    st.write("Edita tus textos, revisa el resultado y confirma para generar el PDF.")
    cv_tab, letter_tab = st.tabs(("CV", "Carta de presentación"))

    with cv_tab:
        editor, preview = st.columns((1, 1.05), gap="large")
        with editor:
            st.subheader("Datos personales")
            st.text_input("Nombre completo", key="name", max_chars=FIELD_LIMITS["name"])
            st.text_input("Título profesional / cargo objetivo", key="role", max_chars=FIELD_LIMITS["role"])
            st.text_input("Correo electrónico", key="email", max_chars=FIELD_LIMITS["email"])
            st.text_input("Teléfono", key="phone", max_chars=FIELD_LIMITS["phone"])
            st.text_input("Ciudad y país", key="location", max_chars=FIELD_LIMITS["location"])
            st.text_input("LinkedIn / portafolio / sitio web", key="links", max_chars=FIELD_LIMITS["links"])
            st.subheader("Contenido del CV")
            st.caption("Deja un campo vacío para omitir esa sección del PDF.")
            for title, key, structured in CV_SECTIONS:
                height = 250 if key == "experience" else 120
                help_text = (
                    "Separa cada experiencia o estudio con una línea en blanco. "
                    "La primera línea de cada bloque irá en negrita. Usa - al inicio para viñetas."
                    if structured else "Puedes usar párrafos separados por una línea en blanco."
                )
                st.text_area(title, key=key, height=height, max_chars=FIELD_LIMITS[key], help=help_text)
        cv_data = snapshot()
        with preview:
            st.subheader("Vista previa del CV")
            st.caption("Vista orientativa. El PDF determina los márgenes y saltos de página finales.")
            st.html(preview_html(cv_data, "cv"))
            export_controls(cv_data, "cv", paper, font_size)

    with letter_tab:
        editor, preview = st.columns((1, 1.05), gap="large")
        with editor:
            st.subheader("Tu carta")
            st.caption("Nombre y contacto se toman de la pestaña CV. Personaliza el texto para cada empresa.")
            st.text_input("Empresa", key="company", max_chars=FIELD_LIMITS["company"])
            st.text_input("Cargo al que postulas", key="job", max_chars=FIELD_LIMITS["job"])
            st.text_input("Destinatario / área", key="recipient", max_chars=FIELD_LIMITS["recipient"])
            st.text_input("Lugar y fecha", key="letter_date", max_chars=FIELD_LIMITS["letter_date"])
            st.text_input("Saludo", key="greeting", max_chars=FIELD_LIMITS["greeting"])
            st.text_area("Cuerpo de la carta", key="letter_body", height=390, max_chars=FIELD_LIMITS["letter_body"],
                         help="Separa los párrafos con una línea en blanco. El texto se edita manualmente.")
            st.text_input("Despedida", key="closing", max_chars=FIELD_LIMITS["closing"])
        letter_data = snapshot()
        with preview:
            st.subheader("Vista previa de la carta")
            st.caption("Revisa empresa, cargo y fecha antes de confirmar.")
            st.html(preview_html(letter_data, "letter"))
            export_controls(letter_data, "letter", paper, font_size)

    with backup_slot:
        backup = json.dumps({"version": 1, "fields": snapshot()}, ensure_ascii=False, indent=2)
        st.download_button("Guardar mis textos (JSON)", backup.encode("utf-8"),
                           "mis_textos_cv.json", mime="application/json", width="stretch")


if __name__ == "__main__":
    main()
