# Santa Mónica · Generador de propuestas para Mercado Público

Aplicación Streamlit en español para completar una oportunidad, redactar la propuesta técnica, calcular una oferta y generar un PDF descargable. Preparada para **CENTRO DE CAPACITACION SANTA MONICA LIMITADA · 76.176.857-3**.

## Inicio rápido

Requiere Python 3.11 o 3.12. Desde esta carpeta:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

En Windows, activa con `.venv\Scripts\activate` en lugar de `source .venv/bin/activate`.

## GitHub + Streamlit Community Cloud

1. Crea un repositorio en GitHub y sube **el contenido de esta carpeta**, incluidas `adjuntos/` y `.streamlit/`. `app.py` y `requirements.txt` deben quedar en la raíz. No subas el ZIP como único archivo.
2. Entra a [Streamlit Community Cloud](https://share.streamlit.io/), conecta tu cuenta GitHub y selecciona **Create app**.
3. Elige repositorio, rama (por ejemplo `main`) y archivo principal **`app.py`**. En opciones avanzadas selecciona Python 3.11 o 3.12 y despliega.
4. Cuando actualices el repositorio, revisa el resultado y los registros del despliegue en Streamlit.

No requiere API keys, cuenta de Mercado Público ni servicios de IA. Este paquete entrega el código; no crea un repositorio ni publica una app por sí solo.

Documentación oficial consultada el 10-11-2026:

- [Desplegar desde GitHub](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [Dependencias de la aplicación](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)
- [Carga de archivos](https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader)
- [Botones de descarga](https://docs.streamlit.io/develop/api-reference/widgets/st.download_button)

## Uso

1. **Oportunidad:** revisa ID, comprador, descripción, plazos, presupuesto, cupos y fechas.
2. **Empresa:** completa representante legal y datos de contacto.
3. **Propuesta técnica:** redacta programa, horas, metodología, cronograma, relatores, evaluación, entregables y respuesta a requisitos.
4. **Cotización:** ingresa precio, despacho, tratamiento tributario y detalle breve de hasta 255 caracteres.
5. **Adjuntos y PDF:** carga los originales y respaldos, revisa los pendientes y genera un borrador o la propuesta final.

El PDF incluye identificación, antecedentes de la oportunidad, propuesta técnica, oferta económica y lista de documentos. El expediente ZIP contiene el PDF, un respaldo JSON, un índice de archivos con SHA-256 y los adjuntos originales. Los adjuntos no se incrustan ni se fusionan dentro del PDF.

## Oportunidad precargada

| Campo | Valor inicial |
|---|---|
| ID | 1057545-246-COT26 |
| Nombre | CURSO APLICACION DE IA Y ANALISIS DE DATOS |
| Comprador | SERVICIO DE SALUD LOS RIOS · 61.607.500-4 |
| Participantes | 20 cupos |
| Unidad de compra | 1 Global |
| Presupuesto estimado | $2.400.000 |
| Plazo requerido | 1 día, según publicación |
| Publicación | 09-11-2026 08:41:58 |
| Cierre primer llamado | 11-11-2026 09:01:00 |
| Cierre segundo llamado | 13-11-2026 09:20:01 |
| Vigencia de cotización | 10-12-2026 |
| Tope informado en el texto | $7.244.000 (100 UTM según la publicación recibida) |

Estos datos fueron transcritos del mensaje del usuario; no se consultó el proceso en línea. El tope es editable y no se actualiza automáticamente por UTM. La app no determina si un llamado está abierto, si el proveedor está habilitado o si una oferta es jurídicamente admisible.

**El precio ofertado empieza en cero.** El presupuesto estimado no es una cotización. El tratamiento tributario comienza en “Por definir”; debe seleccionarlo el proveedor. No se presume que el curso esté exento ni afecto.

## Cálculo de montos

- Subtotal = cantidad de unidades × valor unitario neto.
- Neto = subtotal + despacho neto.
- Afecto: IVA = neto × tasa / 100, redondeado al peso con criterio HALF_UP.
- Exento: IVA = 0.
- Total = neto + IVA.

Para la oportunidad de ejemplo, una unidad Global incluye los 20 cupos. El valor unitario ingresado corresponde al Global completo. Se advierte al superar el presupuesto estimado; se bloquea la versión final si el total supera el tope ingresado. Los cálculos son aritméticos sobre los datos del usuario.

## Adjuntos originales

Los archivos **ANEXO Nº 1_ COMPRAS AGILES.docx** y **BASES TECNICAS CURSO APLICACION IA Y ANALISIS DE DATOS.pdf** fueron mencionados pero no entregados. Debes subir sus originales a la app. No se incluyen sustitutos.

También puedes añadir originales permanentes a `adjuntos/`: ver [instrucciones](adjuntos/LEEME.md). Cada archivo admite hasta 20 MiB, con 80 MiB en total para el expediente. Formatos: PDF, DOC, DOCX, XLS y XLSX; bases exclusivamente PDF y anexo DOC, DOCX o PDF. La app no inspecciona contenido ni acredita firmas.

Para emitir la propuesta final se requieren los campos principales, precio, modalidad, horas, tratamiento tributario, los originales de bases y anexo, vigencia coherente y una confirmación de revisión. Estos controles son una ayuda de edición: no garantizan cumplimiento de las bases. El anexo oficial se completa/firma por separado cuando corresponda. La app no llena automáticamente archivos DOCX ni envía una cotización a Mercado Público.

## Guardar y recuperar avance

- **Guardar avance (.json)** conserva los campos del formulario.
- **Descargar expediente ZIP** conserva además el PDF y los documentos de la sesión.
- **Cargar respaldo** recupera los campos; vuelve a cargar los adjuntos y confirmar la revisión.
- Si editas datos o adjuntos después de generar el PDF, debes generarlo nuevamente. Se oculta la descarga anterior para evitar usar una versión desactualizada.

Los campos y cargas viven en la sesión Streamlit, sin base de datos ni guardado permanente del formulario en el servidor. Al cerrar, reiniciar o perder la sesión puedes perder el avance no descargado. No hay autenticación incluida. Configura el acceso del despliegue según quién deba utilizarlo; no incorpores datos confidenciales en un repositorio compartido.

## Archivos

| Archivo | Función |
|---|---|
| `app.py` | Interfaz y flujo Streamlit |
| `datos.py` | Valores iniciales y opciones |
| `reportes.py` | Cálculos, validación, PDF, JSON y ZIP |
| `requirements.txt` | Dependencias de ejecución |
| `.streamlit/config.toml` | Apariencia y límite de carga |
| `assets/` | Fuentes DejaVu incorporadas al PDF y su licencia |
| `adjuntos/` | Originales opcionales incluidos en el proyecto |
| `tests/` | Pruebas de cálculos, exportación y flujo |
| `ejemplos/propuesta_borrador.pdf` | PDF inicial de demostración; no presentar |

## Verificación local

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

El generador incorpora fuentes DejaVu para mantener una tipografía consistente en el despliegue. Admite texto en español; símbolos ajenos al juego Latin-1/Windows-1252, como emojis, se sustituyen por `?` en el PDF.
