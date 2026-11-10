# Mi CV · Streamlit

Editor en español para adaptar rápidamente tu CV y tu carta de presentación a cada postulación. Diseño minimalista en blanco y negro, sin claves API ni servicios de IA.

## Archivos

```text
app.py
requirements.txt
.streamlit/
  config.toml
.gitignore
README.md
ejemplos/
  cv_generico.pdf
  carta_generica.pdf
```

`app.py` contiene toda la lógica. `requirements.txt` instala las dos dependencias directas. `.streamlit/config.toml` configura el diseño claro y monocromático. Los PDF de `ejemplos/` son muestras ficticias y no son necesarios para ejecutar la app.

## Subir a GitHub y desplegar

1. Crea un repositorio en GitHub, por ejemplo `mi-cv-streamlit`.
2. Sube el contenido de esta carpeta. Deja `app.py` y `requirements.txt` en la raíz del repositorio. No subas el ZIP como único archivo.
3. Conserva la carpeta `.streamlit` con su archivo `config.toml`: configura el tema blanco y negro.
4. Abre [Streamlit Community Cloud](https://share.streamlit.io/) e inicia sesión con GitHub.
5. Pulsa **Create app**, selecciona tu repositorio y la rama que contiene los archivos.
6. En **Main file path**, escribe `app.py`. En las opciones avanzadas, utiliza **Python 3.12**.
7. Pulsa **Deploy**.

Si dejas todo dentro de una subcarpeta del repositorio, ajusta la ruta principal, por ejemplo `cv-streamlit/app.py`. Para simplificar la configuración del tema, se recomienda copiar el contenido a la raíz.

Guía oficial: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app

## Ejecutar en tu equipo

Requiere Python 3.12. Desde la carpeta del proyecto:

```bash
python -m venv .venv
```

Activa el entorno virtual:

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

Instala las dependencias e inicia la app:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Cómo usarla

1. En **CV**, reemplaza los datos ficticios y adapta el título profesional, perfil, experiencia y habilidades al empleo.
2. En experiencia y formación, separa cada entrada con una línea en blanco. La primera línea de cada bloque aparece en negrita. Las líneas que empiezan con `- ` se convierten en viñetas.
3. Deja vacías las secciones que quieras omitir.
4. Revisa la vista previa. Los campos se aplican al salir del cuadro de texto o al pulsar Enter en un campo de una línea.
5. Pulsa **Confirmar y generar PDF del CV** y luego **Descargar CV en PDF**.
6. En **Carta de presentación**, adapta empresa, cargo, fecha, saludo, cuerpo y despedida. Nombre y contacto se comparten con el CV. Los cambios en empresa o cargo no reescriben automáticamente el cuerpo: debes editarlo.
7. Confirma la carta y descarga su PDF.
8. Descarga **Guardar mis textos (JSON)** para conservar tus textos. En otra sesión, carga ese archivo y pulsa **Aplicar respaldo**.

La barra lateral permite escoger A4 o Carta y texto de 9, 10 u 11 puntos. Los PDF crean páginas adicionales según el contenido; no se fuerza todo a una página ni se recortan los textos. La vista web es orientativa: revisa el PDF descargado para ver la paginación final.

Cada PDF se genera después de confirmar. Si cambias un dato de ese documento, su descarga anterior se oculta y debes generar una nueva versión. Los textos son seleccionables y se conservan los acentos y la ñ. La fuente incluida cubre texto latino; si un carácter no está disponible (por ejemplo, un emoji), la app te pide reemplazarlo.

## Datos y personalización

- Los valores iniciales del diccionario `DEFAULTS` son ficticios. Puedes modificarlos para cambiar la plantilla inicial.
- Los datos introducidos se procesan en el servidor donde se ejecuta Streamlit y se mantienen en la sesión de cada usuario. La app no tiene base de datos ni escribe los CV o respaldos en el servidor.
- No se utiliza caché compartida para datos personales. Los PDF se generan en memoria.
- El repositorio contiene el código y la plantilla inicial. Lo que escribes en la web no se sube a GitHub.
- El respaldo JSON es un archivo de texto sin cifrar: guárdalo en tu equipo y úsalo para recuperar tus textos si la sesión termina o se pierde la conexión.
- Esta versión es un editor manual con plantillas: no redacta ni adapta el contenido mediante IA.
- No hacen falta `packages.txt`, Chrome, wkhtmltopdf, una base de datos ni secretos.

Versiones verificadas: Streamlit 1.67.0, ReportLab 4.4.9 y Python 3.12. Documentación: [widgets de Streamlit](https://docs.streamlit.io/develop/api-reference/widgets) y [fuentes de ReportLab](https://docs.reportlab.com/reportlab/userguide/ch3_fonts/).
