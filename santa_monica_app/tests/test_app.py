from datetime import date
from pathlib import Path

from streamlit.testing.v1 import AppTest

from datos import DEFAULTS
from reportes import build_pdf

APP = Path(__file__).resolve().parents[1] / "app.py"


def button(app, label):
    return next(item for item in app.button if item.label == label)


def test_initial_draft_generation_edit_and_reset():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    assert button(app, "Generar propuesta final").disabled
    button(app, "Generar borrador PDF").click().run()
    assert not app.exception
    assert app.session_state["generated"]["pdf"].startswith(b"%PDF")
    assert any("Versión borrador generada" in item.value for item in app.success)
    app.number_input(key="f_valor_unitario").set_value(2000000).run()
    app.selectbox(key="f_tratamiento").select("Exento").run()
    assert not app.exception
    assert any("Los datos o los adjuntos cambiaron" in item.value for item in app.info)
    assert any(item.value == "$ 2.000.000" for item in app.metric)
    app.date_input(key="d_cierre_1_0").set_value(date(2026, 11, 12)).run()
    app.date_input(key="d_cierre_1_0").set_value(date(2026, 11, 11)).run()
    assert app.session_state["f_cierre_1"].startswith("2026-11-11")
    button(app, "Restablecer ejemplo").click().run()
    assert not app.exception
    assert app.session_state["f_valor_unitario"] == 0
    assert app.session_state["upload_epoch"] == 1


def test_complete_final_flow_with_local_originals(tmp_path):
    folder = tmp_path / "adjuntos"
    folder.mkdir()
    (folder / "bases.pdf").write_bytes(build_pdf(DEFAULTS))
    (folder / "anexo.docx").write_bytes(b"Archivo simulado solo para pruebas de descarga")
    source = APP.read_text().replace("ROOT = Path(__file__).resolve().parent", f"ROOT = Path({str(tmp_path)!r})")
    app = AppTest.from_string(source, default_timeout=30).run()
    assert not app.exception
    assert any("Descargar bases.pdf" == item.label for item in app.get("download_button"))
    for key in ("representante", "contacto", "telefono"):
        app.text_input(key="f_" + key).set_value("Dato de prueba")
    app.text_input(key="f_correo").set_value("prueba@example.com")
    for key in ("objetivo", "contenidos", "metodologia", "cronograma", "relatores", "evaluacion", "entregables", "cumplimiento", "condiciones", "detalle"):
        app.text_area(key="f_" + key).set_value("Contenido de prueba; no presentar.")
    app.number_input(key="f_horas").set_value(16)
    app.number_input(key="f_valor_unitario").set_value(2000000)
    app.selectbox(key="f_modalidad").select("En línea en vivo")
    app.selectbox(key="f_tratamiento").select("Exento")
    app.checkbox(key="f_revisado").check().run()
    assert not app.exception
    assert not button(app, "Generar propuesta final").disabled
    button(app, "Generar propuesta final").click().run()
    assert not app.exception
    assert app.session_state["generated"]["final"] is True
    assert app.session_state["generated"]["zip"].startswith(b"PK")
