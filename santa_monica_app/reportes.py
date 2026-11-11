"""Motor sin dependencias de Streamlit: cálculos, respaldos, adjuntos y PDF."""
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)

from datos import DEFAULTS, OPTIONS, EXPECTED

MAX_FILE = 20 * 1024 * 1024
MAX_TOTAL = 80 * 1024 * 1024
ALLOWED = {".pdf", ".doc", ".docx", ".xls", ".xlsx"}

FONT_DIR = Path(__file__).resolve().parent / "assets"
pdfmetrics.registerFont(TTFont("SantaMonica", str(FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("SantaMonica-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))


def clp(value):
    return "$ " + f"{int(value):,}".replace(",", ".")


def totals(data):
    subtotal = int(data["cantidad"]) * int(data["valor_unitario"])
    neto = subtotal + int(data["despacho"])
    iva = 0
    if data["tratamiento"] == "Afecto a IVA":
        iva = int((Decimal(neto) * Decimal(str(data["tasa_iva"])) / 100).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        ))
    return {"subtotal": subtotal, "neto": neto, "iva": iva, "total": neto + iva}


def validate_data(raw):
    """Acepta únicamente el esquema conocido, sin coerciones ni valores no finitos."""
    if not isinstance(raw, dict):
        raise ValueError("El respaldo debe contener un objeto de datos.")
    unknown = set(raw) - set(DEFAULTS)
    if unknown:
        raise ValueError("El respaldo contiene campos no reconocidos.")
    result = deepcopy(DEFAULTS)
    for key, value in raw.items():
        default = DEFAULTS[key]
        if type(default) is bool:
            valid = type(value) is bool
        elif type(default) is int:
            valid = type(value) is int and 0 <= value <= 10**12
        elif type(default) is float:
            valid = type(value) in (int, float) and 0 <= value <= 100
        else:
            valid = isinstance(value, str) and len(value) <= 30000
        if not valid:
            raise ValueError(f"Valor inválido en el campo: {key}.")
        if key in OPTIONS and value not in OPTIONS[key]:
            raise ValueError(f"Opción no reconocida en: {key}.")
        result[key] = float(value) if type(default) is float else value
    if len(result["detalle"]) > 255:
        raise ValueError("El detalle de cotización no puede superar 255 caracteres.")
    for key in ("publicacion", "cierre_1", "cierre_2"):
        try:
            dt = datetime.fromisoformat(result[key])
            if dt.tzinfo or not 2000 <= dt.year <= 2100:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError(f"Fecha y hora inválidas: {key}.") from None
    try:
        day = date.fromisoformat(result["vigencia"])
        if not 2000 <= day.year <= 2100:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("Fecha de vigencia inválida.") from None
    if result["cantidad"] < 1 or result["cupos"] < 1:
        raise ValueError("La cantidad y los cupos deben ser mayores que cero.")
    return result


def export_json(data):
    return json.dumps({"version": 1, "datos": validate_data(data)},
                      ensure_ascii=False, indent=2).encode("utf-8")


def import_json(blob):
    if len(blob) > 2 * 1024 * 1024:
        raise ValueError("El respaldo JSON supera 2 MB.")
    try:
        obj = json.loads(blob)
    except (ValueError, UnicodeDecodeError):
        raise ValueError("El archivo no es un JSON válido.") from None
    if not isinstance(obj, dict) or type(obj.get("version")) is not int or obj["version"] != 1:
        raise ValueError("Versión de respaldo no compatible.")
    return validate_data(obj.get("datos"))


def safe_name(name):
    name = str(name).replace("\\", "/").split("/")[-1]
    name = re.sub(r"[^\w .()º°-]", "_", name, flags=re.UNICODE).strip(". ")
    return name[:160] or "archivo"


def attachment(role, name, content):
    name = safe_name(name)
    if Path(name).suffix.lower() not in ALLOWED:
        raise ValueError(f"Formato no permitido: {name}.")
    if not content:
        raise ValueError(f"El archivo {name} está vacío.")
    if len(content) > MAX_FILE:
        raise ValueError(f"{name} supera el máximo de 20 MB.")
    if role == "bases" and Path(name).suffix.lower() != ".pdf":
        raise ValueError("Las bases técnicas deben ser un PDF.")
    if role == "anexo" and Path(name).suffix.lower() not in {".doc", ".docx", ".pdf"}:
        raise ValueError("El anexo debe ser DOC, DOCX o PDF.")
    return {"rol": role, "nombre": name, "contenido": bytes(content)}


def manifest(files):
    return [{"rol": f["rol"], "nombre": f["nombre"], "bytes": len(f["contenido"]),
             "sha256": sha256(f["contenido"]).hexdigest()} for f in files]


def pending(data, files):
    required = {
        "empresa": "Razón social", "rut_empresa": "RUT de empresa",
        "representante": "Representante legal", "contacto": "Contacto",
        "correo": "Correo", "telefono": "Teléfono", "identificador": "ID de oportunidad",
        "nombre": "Nombre de oportunidad", "comprador": "Organismo comprador",
        "objetivo": "Objetivo del curso", "contenidos": "Programa y contenidos",
        "metodologia": "Metodología", "cronograma": "Cronograma",
        "relatores": "Relatores y antecedentes", "evaluacion": "Evaluación y aprobación",
        "entregables": "Entregables", "cumplimiento": "Respuesta a bases técnicas",
        "condiciones": "Condiciones comerciales", "detalle": "Detalle breve de cotización",
    }
    issues = [label for key, label in required.items() if not str(data[key]).strip()]
    if data["correo"].strip() and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", data["correo"].strip()):
        issues.append("Correo electrónico válido")
    for key, label in (("horas", "Duración del curso"), ("valor_unitario", "Valor unitario")):
        if data[key] <= 0:
            issues.append(label)
    if data["modalidad"] == "Por definir":
        issues.append("Modalidad del curso")
    if data["tratamiento"] == "Por definir":
        issues.append("Tratamiento tributario de la oferta")
    roles = {f["rol"] for f in files}
    if "bases" not in roles:
        issues.append("Archivo de bases técnicas")
    if "anexo" not in roles:
        issues.append("Archivo de anexo")
    if not data["revisado"]:
        issues.append("Confirmación de revisión de bases, anexo y propuesta")
    close = datetime.fromisoformat(data["cierre_1"] if data["llamado"] == "Primer llamado" else data["cierre_2"])
    if date.fromisoformat(data["vigencia"]) < close.date():
        issues.append("Vigencia de la oferta posterior o igual al cierre seleccionado")
    if totals(data)["total"] > data["tope_publicacion"]:
        issues.append("Monto total dentro del tope informado en la publicación")
    return issues


def display_date(text, clock=False):
    return datetime.fromisoformat(text).strftime("%d-%m-%Y %H:%M:%S" if clock else "%d-%m-%Y")


def build_pdf(data, files=(), final=False):
    data = validate_data(data)
    issues = pending(data, files)
    if final and issues:
        raise ValueError("Completa los pendientes antes de emitir la propuesta final.")
    out = BytesIO()
    navy, teal = colors.HexColor("#122C43"), colors.HexColor("#087F82")
    gray, light = colors.HexColor("#536474"), colors.HexColor("#F0F5F7")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleSM", fontName="SantaMonica-Bold", fontSize=24,
                              leading=29, textColor=navy, spaceAfter=10))
    styles.add(ParagraphStyle(name="SubSM", fontName="SantaMonica-Bold", fontSize=12,
                              leading=17, textColor=teal, spaceBefore=16, spaceAfter=8,
                              keepWithNext=True))
    styles.add(ParagraphStyle(name="BodySM", fontName="SantaMonica", fontSize=9,
                              leading=14, textColor=navy, spaceAfter=6,
                              splitLongWords=True, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name="SmallSM", parent=styles["BodySM"], fontSize=8,
                              leading=11, textColor=gray))
    styles.add(ParagraphStyle(name="LabelSM", parent=styles["SmallSM"],
                              fontName="SantaMonica-Bold", keepWithNext=True))
    # Escapar contenido de usuarios evita interpretar etiquetas como marcado PDF.
    def p(text, style="BodySM"):
        text = str(text).strip() or "Pendiente de completar"
        # La aplicación está orientada a documentos en español; sustituir emojis.
        text = text.encode("cp1252", errors="replace").decode("cp1252")
        return Paragraph(escape(text).replace("\n", "<br/>"), styles[style])

    story = []
    def section(title):
        story.append(p(title, "SubSM"))

    def field(label, value):
        story.extend([p(label, "LabelSM"), p(value)])

    def grid(rows):
        table = Table([[p(a, "LabelSM"), p(b)] for a, b in rows], colWidths=[48*mm, 126*mm],
                      hAlign="LEFT", splitInRow=1)
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (0, -1), light),
            ("LINEBELOW", (0, 0), (-1, -1), .4, colors.HexColor("#DDE6EB")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(table)

    story.extend([p("SANTA MÓNICA / CAPACITACIÓN", "SubSM"),
                  p("Propuesta técnica\ny económica", "TitleSM"),
                  p(data["nombre"]), p(f"Compra Ágil {data['identificador']}", "SmallSM"),
                  p("PROPUESTA FINAL" if final else "BORRADOR / NO PRESENTAR", "SubSM"),
                  Spacer(1, 4*mm)])
    grid([("Proveedor", data["empresa"]), ("RUT proveedor", data["rut_empresa"]),
          ("Organismo comprador", data["comprador"]), ("RUT comprador", data["rut_comprador"]),
          ("Validez de oferta", display_date(data["vigencia"]))])
    if not final:
        section("Revisión pendiente")
        story.append(p("Este borrador se genera con la información ingresada. Las bases técnicas y "
                       "el anexo no se interpretan automáticamente. La oferta requiere revisión del proveedor."))
        story.append(p("; ".join(issues) if issues else "Sin campos pendientes. Puede emitir la versión final."))

    section("01 / Identificación y contacto")
    grid([("Representante legal", data["representante"]),
          ("RUT representante", data["rut_representante"] or "No informado"),
          ("Contacto", data["contacto"]), ("Correo", data["correo"]),
          ("Teléfono", data["telefono"]), ("Domicilio", data["domicilio"] or "No informado")])

    section("02 / Antecedentes de la oportunidad")
    field("Solicitud del comprador", data["descripcion"])
    grid([("Dirección de entrega", data["direccion"]),
          ("Plazo requerido", f"{data['plazo_requerido']} día(s), según publicación"),
          ("Presupuesto estimado", f"{clp(data['presupuesto'])} - {data['tipo_presupuesto']}"),
          ("Publicación", display_date(data["publicacion"], True)),
          ("Cierre primer llamado", display_date(data["cierre_1"], True)),
          ("Cierre segundo llamado", display_date(data["cierre_2"], True)),
          ("Llamado seleccionado", data["llamado"]),
          ("Categoría / ID", f"{data['categoria']} / {data['id_producto']}"),
          ("Cupos solicitados", str(data["cupos"])),
          ("Sanciones informadas", "Sí, según publicación; revisar condiciones del comprador."
           if data["sanciones"] else "No indicadas en los datos ingresados.")])
    if data["observaciones"].strip():
        field("Observaciones de la oportunidad", data["observaciones"])

    section("03 / Propuesta técnica")
    grid([("Modalidad", data["modalidad"]), ("Horas totales", str(data["horas"])),
          ("Participantes", str(data["cupos"])),
          ("Plazo ofertado", f"{data['plazo_ofertado']} día(s), según condiciones de la oferta")])
    for key, label in [("objetivo", "Objetivo y alcance"), ("contenidos", "Programa y contenidos"),
                       ("metodologia", "Metodología"), ("cronograma", "Cronograma y coordinación"),
                       ("relatores", "Relatores y antecedentes"), ("experiencia", "Experiencia del proveedor"),
                       ("evaluacion", "Evaluación y criterios de aprobación"),
                       ("entregables", "Entregables"), ("cumplimiento", "Respuesta a las bases técnicas")]:
        if key == "experiencia" and not data[key].strip():
            continue
        field(label, data[key])

    section("04 / Oferta económica")
    amount = totals(data)
    grid([("Servicio", data["item"]), ("Cantidad / unidad", f"{data['cantidad']} {data['unidad']}"),
          ("Valor unitario neto", clp(data["valor_unitario"])),
          ("Subtotal", clp(amount["subtotal"])), ("Despacho neto", clp(data["despacho"])),
          ("Valor neto", clp(amount["neto"])),
          ("Tratamiento tributario", data["tratamiento"]),
          (f"IVA ({data['tasa_iva']:g}%)" if data["tratamiento"] == "Afecto a IVA" else "IVA",
           clp(amount["iva"]) if data["tratamiento"] != "Por definir" else "Pendiente de definir"),
          ("MONTO TOTAL" if data["tratamiento"] != "Por definir" else "TOTAL PROVISIONAL",
           clp(amount["total"]))])
    story.append(p("Valores expresados en pesos chilenos. El valor unitario corresponde a la unidad "
                   "de compra indicada; no al precio por participante.", "SmallSM"))
    field("Detalle breve para Mercado Público", data["detalle"])
    field("Condiciones comerciales y de ejecución", data["condiciones"])
    field("Vigencia de cotización", display_date(data["vigencia"]))

    section("05 / Documentos complementarios")
    story.append(p("Los archivos se entregan por separado en el expediente ZIP; no están incrustados "
                   "en este PDF. El anexo mantiene el contenido que cargó el usuario y debe completarse "
                   "y firmarse cuando corresponda."))
    if files:
        for index, f in enumerate(files, 1):
            story.append(p(f"{index}. {f['nombre']} ({len(f['contenido']) / 1024:.1f} KB)", "SmallSM"))
    else:
        story.append(p("Sin archivos cargados. Se esperan los siguientes originales:"))
        for name in EXPECTED.values():
            story.append(p(name, "SmallSM"))
    if final:
        story.append(Spacer(1, 8*mm))
        field("Responsable de la propuesta", data["representante"])
        story.append(p("Documento generado a partir de antecedentes ingresados y revisados por el proveedor. "
                       "No contiene firma electrónica ni acredita envío a Mercado Público.", "SmallSM"))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(teal)
        canvas.line(18*mm, 18*mm, 192*mm, 18*mm)
        canvas.setFont("SantaMonica", 7)
        canvas.setFillColor(gray)
        label = safe_name(data["identificador"])[:55].encode("cp1252", "replace").decode("cp1252")
        canvas.drawString(18*mm, 13*mm, f"SANTA MONICA | {label} | {'FINAL' if final else 'BORRADOR'}")
        canvas.drawRightString(192*mm, 13*mm, f"Página {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(out, pagesize=(210*mm, 297*mm), leftMargin=18*mm,
                            rightMargin=18*mm, topMargin=16*mm, bottomMargin=25*mm,
                            title=f"Propuesta - {data['identificador']}", author=data["empresa"])
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return out.getvalue()


def build_package(data, files, final=False):
    pdf = build_pdf(data, files, final)
    out = BytesIO()
    with ZipFile(out, "w", ZIP_DEFLATED) as archive:
        archive.writestr("propuesta_final.pdf" if final else "propuesta_borrador.pdf", pdf)
        archive.writestr("respaldo.json", export_json(data))
        archive.writestr("indice_adjuntos.json", json.dumps(manifest(files), ensure_ascii=False, indent=2))
        for index, f in enumerate(files, 1):
            archive.writestr(f"adjuntos/{index:02d}_{safe_name(f['nombre'])}", f["contenido"])
        archive.writestr("LEEME.txt", (
            "EXPEDIENTE SANTA MONICA\n\n"
            "El ZIP organiza la propuesta y los originales; suba los documentos individuales "
            "en los formatos admitidos por Mercado Público.\n"
            "El respaldo JSON guarda los campos, no los adjuntos. Vuelva a cargarlos al importar.\n"
            "Verifique las bases y complete/firme el anexo cuando corresponda. "
            "Este expediente no envía ninguna cotización.\n"
        ))
    return pdf, out.getvalue()
