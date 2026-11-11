from copy import deepcopy
from io import BytesIO
import json
from zipfile import ZipFile

from pypdf import PdfReader
import pytest

from datos import DEFAULTS
from reportes import (attachment, build_package, build_pdf, export_json, import_json,
                      pending, safe_name, totals)


def complete_data():
    data = deepcopy(DEFAULTS)
    for key in ("representante", "contacto", "telefono", "objetivo", "contenidos", "metodologia",
                "cronograma", "relatores", "evaluacion", "entregables", "cumplimiento", "condiciones", "detalle"):
        data[key] = "Texto de prueba, no presentar."
    data.update(correo="prueba@example.com", horas=16, valor_unitario=2000000,
                modalidad="En línea en vivo", tratamiento="Exento", revisado=True)
    return data


def test_prices_global_tax_and_rounding():
    data = deepcopy(DEFAULTS)
    data.update(valor_unitario=100000, cantidad=2, despacho=10000, tratamiento="Afecto a IVA")
    assert totals(data) == {"subtotal": 200000, "neto": 210000, "iva": 39900, "total": 249900}
    data.update(tratamiento="Exento")
    assert totals(data)["total"] == 210000
    data.update(tratamiento="Afecto a IVA", cantidad=1, valor_unitario=50, despacho=0)
    assert totals(data)["iva"] == 10  # 9.5 se redondea hacia arriba.


def test_backup_roundtrip_and_invalid_inputs():
    assert import_json(export_json(DEFAULTS)) == DEFAULTS
    for payload in [b"no-json", b"[]", b'{"version":2}',
                    b'{"version":1,"datos":{"valor_unitario":-1}}',
                    b'{"version":1,"datos":{"cantidad":true}}',
                    b'{"version":1,"datos":{"tasa_iva":NaN}}',
                    b'{"version":1,"datos":{"vigencia":"31/12/2026"}}',
                    b'{"version":1,"datos":{"tratamiento":"otro"}}']:
        with pytest.raises(ValueError):
            import_json(payload)


def test_pending_final_gate_and_vigencia():
    with pytest.raises(ValueError):
        build_pdf(DEFAULTS, final=True)
    data = complete_data()
    files = [attachment("bases", "bases.pdf", b"original de prueba"),
             attachment("anexo", "anexo.docx", b"original de prueba")]
    assert not pending(data, files)
    assert build_pdf(data, files, final=True).startswith(b"%PDF")
    data["vigencia"] = "2026-11-01"
    assert any("Vigencia" in issue for issue in pending(data, files))
    data.update(vigencia="2026-12-10", valor_unitario=8000000)
    assert any("tope" in issue for issue in pending(data, files))


def test_pdf_escapes_text_and_handles_long_content():
    data = deepcopy(DEFAULTS)
    data["contenidos"] = ("Módulo <IA> & análisis de datos: práctica, evaluación y discusión.\n" * 170)
    data["direccion"] = "Dirección extensa " * 500
    content = build_pdf(data)
    reader = PdfReader(BytesIO(content))
    extracted = "\n".join(p.extract_text() for p in reader.pages)
    assert len(reader.pages) > 2
    assert "<IA> & análisis" in extracted
    assert "BORRADOR / NO PRESENTAR" in extracted
    assert "76.176.857-3" in extracted
    assert "05 / Documentos complementarios" in extracted


def test_package_keeps_original_bytes_and_unique_paths():
    files = [attachment("bases", "../../mismo.pdf", b"contenido original A"),
             attachment("respaldo", "mismo.pdf", b"contenido original B")]
    pdf, package = build_package(DEFAULTS, files)
    with ZipFile(BytesIO(package)) as archive:
        assert archive.read("propuesta_borrador.pdf") == pdf
        assert archive.read("adjuntos/01_mismo.pdf") == b"contenido original A"
        assert archive.read("adjuntos/02_mismo.pdf") == b"contenido original B"
        assert import_json(archive.read("respaldo.json")) == DEFAULTS
        manifest = json.loads(archive.read("indice_adjuntos.json"))
        assert len(manifest[0]["sha256"]) == 64
    assert safe_name("..\\..\\archivo.pdf") == "archivo.pdf"
    with pytest.raises(ValueError):
        attachment("bases", "ejecutable.exe", b"x")
    with pytest.raises(ValueError):
        attachment("bases", "bases.pdf", b"x" * (20 * 1024 * 1024 + 1))
    with pytest.raises(ValueError):
        attachment("bases", "bases.pdf", b"")
