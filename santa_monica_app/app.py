"""Ejecutar: streamlit run app.py"""
from copy import deepcopy
from datetime import date, datetime
from hashlib import sha256
from pathlib import Path
import json

import streamlit as st

from datos import DEFAULTS, OPTIONS, EXPECTED
from reportes import (
    MAX_TOTAL, attachment, build_package, clp, export_json, import_json,
    manifest, pending, safe_name, totals,
)

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Santa Mónica | Propuestas", page_icon="📄", layout="wide")
st.markdown("""
<style>
.block-container {max-width:1200px; padding-top:2rem;}
.hero {background:#122c43; border-radius:16px; padding:28px 32px; margin-bottom:24px;}
.hero .eyebrow {color:#70d7d1; letter-spacing:2px; font-size:12px; font-weight:700;}
.hero h1 {color:white; font-size:32px; padding:8px 0; margin:0;}
.hero p {color:#d9e6ed; margin:0; font-size:15px;}
div[data-testid="stMetric"] {border:1px solid #dbe6eb; border-radius:12px; padding:16px;}
</style>
<div class="hero"><div class="eyebrow">SANTA MÓNICA · CAPACITACIÓN</div>
<h1>Tu próxima propuesta, paso a paso.</h1>
<p>Completa los antecedentes y prepara tu propuesta técnica y económica en PDF.</p></div>
""", unsafe_allow_html=True)

if "upload_epoch" not in st.session_state:
    st.session_state.upload_epoch = 0
for key, value in DEFAULTS.items():
    st.session_state.setdefault("f_" + key, deepcopy(value))


def current_data():
    return {key: st.session_state["f_" + key] for key in DEFAULTS}


def reset_example():
    for key, value in DEFAULTS.items():
        st.session_state["f_" + key] = deepcopy(value)
    st.session_state.upload_epoch += 1
    st.session_state.pop("generated", None)
    st.session_state["notice"] = ("success", "Se restableció la oportunidad de ejemplo.")


def restore():
    upload = st.session_state.get("restore_file")
    if upload is None:
        st.session_state["notice"] = ("error", "Selecciona primero un respaldo JSON.")
        return
    try:
        data = import_json(upload.getvalue())
        data["revisado"] = False
        for key, value in data.items():
            st.session_state["f_" + key] = value
        st.session_state.upload_epoch += 1
        st.session_state.pop("generated", None)
        st.session_state["notice"] = ("success", "Avance recuperado. Carga nuevamente los adjuntos y confirma la revisión.")
    except ValueError as exc:
        st.session_state["notice"] = ("error", str(exc))


def text(label, key, help=None, area=False, height=110, limit=None):
    fn = st.text_area if area else st.text_input
    args = {"key": "f_" + key, "help": help, "max_chars": limit or 30000}
    if area:
        args["height"] = height
    return fn(label, **args)


def number(label, key, minimum=0, help=None):
    return st.number_input(label, min_value=minimum, max_value=10**12,
                           step=1, key="f_" + key, help=help)


def select(label, key):
    return st.selectbox(label, OPTIONS[key], key="f_" + key)


def date_time(label, key):
    dt = datetime.fromisoformat(st.session_state["f_" + key])
    left, right = st.columns([3, 2])
    # Una nueva importación o reinicio crea controles limpios con sus fechas recuperadas.
    with left:
        day = st.date_input(label, value=dt.date(), min_value=date(2000, 1, 1),
                            max_value=date(2100, 12, 31), key=f"d_{key}_{st.session_state.upload_epoch}")
    with right:
        clock_text = st.text_input("Hora (HH:MM:SS)", value=dt.strftime("%H:%M:%S"),
                                    key=f"t_{key}_{st.session_state.upload_epoch}", max_chars=8)
    try:
        clock = datetime.strptime(clock_text, "%H:%M:%S").time()
    except ValueError:
        st.error(f"Revisa la hora de {label.lower()}: usa HH:MM:SS, por ejemplo 09:01:00.")
        st.stop()
    st.session_state["f_" + key] = datetime.combine(day, clock).isoformat()


with st.sidebar:
    st.subheader("Mesa de propuestas")
    st.caption("CENTRO DE CAPACITACION SANTA MONICA LIMITADA · 76.176.857-3")
    st.info("El avance permanece en esta sesión. Descarga el respaldo JSON antes de salir.")
    st.file_uploader("Recuperar avance (.json)", type=["json"], key="restore_file")
    st.button("Cargar respaldo", on_click=restore, use_container_width=True)
    save_slot = st.empty()
    st.divider()
    st.button("Restablecer ejemplo", on_click=reset_example, use_container_width=True)
    st.caption("Los archivos que subes se usan en tu sesión. Los originales incluidos en el repositorio están disponibles para todos los usuarios de la app.")

if "notice" in st.session_state:
    level, message = st.session_state.pop("notice")
    getattr(st, level)(message)

tabs = st.tabs(["1 · Oportunidad", "2 · Empresa", "3 · Propuesta técnica", "4 · Cotización", "5 · Adjuntos y PDF"])

with tabs[0]:
    st.subheader("Antecedentes de la Compra Ágil")
    st.caption("Datos iniciales transcritos del texto proporcionado. Puedes editarlos para otra oportunidad. Fechas y horas según la publicación, hora de Chile.")
    a, b = st.columns([1, 2])
    with a:
        text("ID de cotización", "identificador")
    with b:
        text("Nombre de la oportunidad", "nombre")
    a, b = st.columns(2)
    with a:
        text("Organismo comprador", "comprador")
        text("RUT comprador", "rut_comprador")
    with b:
        number("Presupuesto estimado (CLP)", "presupuesto")
        text("Tipo de presupuesto", "tipo_presupuesto")
    text("Descripción de la solicitud", "descripcion", area=True, height=140)
    text("Dirección de entrega", "direccion")
    a, b, c = st.columns(3)
    with a:
        number("Plazo requerido (días)", "plazo_requerido")
    with b:
        number("Cupos solicitados", "cupos", minimum=1)
    with c:
        select("Llamado a preparar", "llamado")
    a, b, c = st.columns(3)
    with a:
        date_time("Publicación", "publicacion")
    with b:
        date_time("Cierre primer llamado", "cierre_1")
    with c:
        date_time("Cierre segundo llamado", "cierre_2")
    a, b = st.columns([3, 1])
    with a:
        text("Categoría", "categoria")
    with b:
        text("ID del producto", "id_producto")
    number("Tope informado en la publicación (CLP)", "tope_publicacion",
           help="El ejemplo usa $7.244.000, equivalencia de 100 UTM informada en el texto recibido. Actualízalo para cada proceso.")
    st.checkbox("La publicación contempla sanciones por incumplimiento", key="f_sanciones")
    text("Observaciones de la oportunidad", "observaciones", area=True,
         help="Por ejemplo: requisitos de admisibilidad, antecedentes solicitados o condiciones del comprador.")

with tabs[1]:
    st.subheader("Identificación del proveedor")
    text("Razón social", "empresa")
    a, b = st.columns(2)
    with a:
        text("RUT empresa", "rut_empresa")
        text("Representante legal", "representante")
        text("RUT representante (opcional)", "rut_representante")
        text("Domicilio (opcional)", "domicilio")
    with b:
        text("Persona de contacto", "contacto")
        text("Correo electrónico", "correo")
        text("Teléfono", "telefono")

with tabs[2]:
    st.subheader("Propuesta técnica del curso")
    st.info("Completa esta sección a partir de las bases técnicas. La app no interpreta los documentos ni inventa requisitos, experiencia o credenciales.")
    a, b, c = st.columns(3)
    with a:
        select("Modalidad", "modalidad")
    with b:
        number("Duración total (horas)", "horas")
    with c:
        number("Plazo ofertado (días)", "plazo_ofertado",
               help="Diferencia el plazo de entrega o inicio de la duración total del curso. Explica su alcance en las condiciones.")
    for label, key, hint in [
        ("Objetivo y alcance", "objetivo", "Qué aprenderán los participantes y cómo se relaciona con el servicio solicitado."),
        ("Programa y contenidos", "contenidos", "Módulos, temas y horas. Escribe un módulo por línea."),
        ("Metodología", "metodologia", "Actividades, ejercicios prácticos, herramientas y acompañamiento."),
        ("Cronograma y coordinación", "cronograma", "Fechas propuestas, distribución de horas y coordinación con el comprador."),
        ("Relatores y antecedentes", "relatores", "Nombres, profesión y experiencia acreditable. Adjunta sus antecedentes si corresponde."),
        ("Experiencia del proveedor (opcional)", "experiencia", "Servicios o cursos efectivamente realizados y referencias verificables."),
        ("Evaluación y criterios de aprobación", "evaluacion", "Instrumentos, asistencia y requisitos para aprobar, según bases."),
        ("Entregables", "entregables", "Materiales, certificados, informes y otros productos comprometidos."),
        ("Respuesta a las bases técnicas", "cumplimiento", "Por cada requisito: indica cómo se cumple y qué documento lo respalda."),
    ]:
        text(label, key, help=hint, area=True, height=140 if key in {"contenidos", "cumplimiento"} else 110)

with tabs[3]:
    st.subheader("Oferta económica")
    st.caption("Montos en pesos chilenos enteros. El presupuesto del comprador no se usa automáticamente como precio ofertado.")
    text("Descripción del ítem", "item", area=True)
    a, b, c = st.columns(3)
    with a:
        number("Cantidad de unidades de compra", "cantidad", minimum=1,
               help="Esta compra solicita 1 Global que incluye los 20 cupos.")
    with b:
        text("Unidad de compra", "unidad")
    with c:
        number("Valor unitario neto (CLP)", "valor_unitario",
               help="Precio de una unidad Global completa; no de un cupo individual.")
    a, b, c = st.columns(3)
    with a:
        number("Despacho neto (CLP)", "despacho")
    with b:
        select("Tratamiento tributario", "tratamiento")
    with c:
        st.number_input("Tasa IVA (%)", min_value=0.0, max_value=100.0, step=0.1,
                        key="f_tasa_iva", disabled=st.session_state.f_tratamiento != "Afecto a IVA")
    amount = totals(current_data())
    cols = st.columns(4)
    for col, label, key in zip(cols, ["Subtotal", "Valor neto", "IVA", "Total provisional" if st.session_state.f_tratamiento == "Por definir" else "Monto total"], ["subtotal", "neto", "iva", "total"]):
        col.metric(label, clp(amount[key]))
    st.caption("Subtotal = cantidad × valor unitario. Neto = subtotal + despacho. IVA sobre el neto, redondeado al peso; exento usa IVA cero.")
    if st.session_state.f_tratamiento == "Por definir":
        st.warning("Define si la oferta es exenta o afecta a IVA antes de emitir la propuesta final.")
    if amount["total"] > st.session_state.f_presupuesto:
        st.warning("El total ofertado supera el presupuesto estimado ingresado.")
    if amount["total"] > st.session_state.f_tope_publicacion:
        st.error("El total supera el tope informado para esta publicación. Ajusta la oferta o verifica el dato de origen.")
    if st.session_state.f_plazo_ofertado > st.session_state.f_plazo_requerido:
        st.warning("El plazo ofertado supera el plazo requerido. Revisa su admisibilidad en las bases.")
    detail = text("Detalle breve de cotización (máximo 255 caracteres)", "detalle", area=True, limit=255)
    st.caption(f"{len(detail)}/255 caracteres · Puedes copiar este texto al formulario de Mercado Público.")
    day = st.date_input("Fecha de vigencia", value=date.fromisoformat(st.session_state.f_vigencia),
                        min_value=date(2000, 1, 1), max_value=date(2100, 12, 31),
                        key=f"vigencia_{st.session_state.upload_epoch}")
    st.session_state.f_vigencia = day.isoformat()
    text("Condiciones comerciales y de ejecución", "condiciones", area=True, height=140,
         help="Pago, coordinación, alcance del plazo ofertado y condiciones o supuestos relevantes.")

files, attachment_errors = [], []


def get_slot(role, label, types):
    st.markdown(f"**{label}**")
    st.caption("Original esperado: " + EXPECTED[role])
    candidates = [f for f in (ROOT / "adjuntos").glob(role + ".*")
                  if f.is_file() and not f.is_symlink() and f.suffix.lower().lstrip(".") in types]
    uploaded = st.file_uploader("Cargar o reemplazar " + label.lower(), type=types,
                                key=f"upload_{role}_{st.session_state.upload_epoch}")
    source = None
    try:
        if uploaded is not None:
            source = attachment(role, uploaded.name, uploaded.getvalue())
        elif candidates:
            if len(candidates) > 1:
                attachment_errors.append(f"Hay varios originales para {label}. Conserva uno o carga el archivo correcto.")
            else:
                path = candidates[0]
                if path.stat().st_size > 20 * 1024 * 1024:
                    raise ValueError(f"{path.name} supera 20 MB.")
                source = attachment(role, path.name, path.read_bytes())
        if source:
            files.append(source)
            st.download_button("Descargar " + source["nombre"], source["contenido"],
                               file_name=source["nombre"], key="download_" + role,
                               on_click="ignore", use_container_width=True)
        else:
            st.caption("Pendiente de cargar. El archivo original no está incluido en este proyecto.")
    except ValueError as exc:
        attachment_errors.append(str(exc))


with tabs[4]:
    st.subheader("Documentos y expediente descargable")
    st.caption("Máximo 20 MB por archivo; 80 MB en total. Los adjuntos conservan su contenido y se descargan individualmente o dentro del expediente ZIP.")
    a, b = st.columns(2)
    with a:
        get_slot("bases", "Bases técnicas", ["pdf"])
    with b:
        get_slot("anexo", "Anexo N.º 1", ["doc", "docx", "pdf"])
    extras = st.file_uploader("Otros documentos: anexo completado, CV, certificados o respaldos",
                              type=["pdf", "doc", "docx", "xls", "xlsx"], accept_multiple_files=True,
                              key=f"upload_extras_{st.session_state.upload_epoch}")
    for index, upload in enumerate(extras or []):
        try:
            item = attachment("respaldo", upload.name, upload.getvalue())
            files.append(item)
            st.download_button("Descargar " + item["nombre"], item["contenido"],
                               file_name=item["nombre"], key=f"extra_{index}", on_click="ignore")
        except ValueError as exc:
            attachment_errors.append(str(exc))
    if sum(len(f["contenido"]) for f in files) > MAX_TOTAL:
        attachment_errors.append("Los adjuntos superan 80 MB en total. Reduce la selección para generar el expediente.")
    for message in attachment_errors:
        st.error(message)
    st.divider()
    st.checkbox("He revisado las bases, el anexo y la propuesta; completé y firmé los documentos que corresponde presentar.",
                key="f_revisado")
    data = current_data()
    issues = pending(data, files)
    st.caption(f"{len(issues)} pendientes para emitir la propuesta final" if issues else "Propuesta lista para emitir")
    if issues:
        with st.expander("Ver campos y documentos pendientes", expanded=True):
            for issue in issues:
                st.write("• " + issue)
    else:
        st.success("Campos completos y revisión confirmada. Puedes emitir la propuesta final.")
    a, b = st.columns(2)
    mode = None
    if a.button("Generar borrador PDF", use_container_width=True, disabled=bool(attachment_errors)):
        mode = False
    if b.button("Generar propuesta final", type="primary", use_container_width=True,
                disabled=bool(issues or attachment_errors)):
        mode = True
    fingerprint = sha256(export_json(data) + json.dumps(manifest(files), sort_keys=True).encode()).hexdigest()
    if mode is not None:
        with st.spinner("Preparando PDF y expediente…"):
            try:
                pdf, package = build_package(data, files, final=mode)
                if len(pdf) > 20 * 1024 * 1024:
                    raise ValueError("El PDF generado supera 20 MB. Reduce el contenido antes de descargar.")
                st.session_state.generated = {"pdf": pdf, "zip": package, "fingerprint": fingerprint, "final": mode}
            except ValueError as exc:
                st.error(str(exc))
    generated = st.session_state.get("generated")
    if generated and generated["fingerprint"] == fingerprint and not attachment_errors:
        label = "final" if generated["final"] else "borrador"
        slug = safe_name(data["identificador"])[:70]
        st.success(f"Versión {label} generada con los datos actuales.")
        a, b = st.columns(2)
        a.download_button("Descargar PDF " + label, generated["pdf"],
                           file_name=f"propuesta_{slug}_{label}.pdf", mime="application/pdf",
                           on_click="ignore", use_container_width=True)
        b.download_button("Descargar expediente ZIP con adjuntos", generated["zip"],
                           file_name=f"expediente_{slug}_{label}.zip", mime="application/zip",
                           on_click="ignore", use_container_width=True)
        st.caption("El ZIP es una carpeta de trabajo. En Mercado Público presenta los archivos individuales admitidos. La app no envía la cotización ni firma documentos.")
    elif generated:
        st.info("Los datos o los adjuntos cambiaron. Genera nuevamente el PDF para descargar una versión actualizada.")

with save_slot.container():
    st.download_button("Guardar avance (.json)", export_json(current_data()),
                       file_name=f"avance_{safe_name(st.session_state.f_identificador)[:70]}.json",
                       mime="application/json", on_click="ignore", use_container_width=True)
    st.caption("El respaldo guarda los campos. Descarga el expediente ZIP para conservar también los adjuntos.")
