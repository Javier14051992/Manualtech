# Manualtech

![Logo de Manualtech](assets/manualtech_logo.png)

Manualtech es una aplicacion local de escritorio para Windows pensada para guardar, clasificar, indexar y buscar manuales de taller sin usar servidores, nube, APIs externas ni servicios de pago.

El objetivo es sencillo: anadir PDFs o carpetas de imagenes de manuales, extraer texto pagina por pagina, indexarlo en SQLite FTS5 y encontrar rapidamente una averia, pieza, procedimiento, codigo o sistema dentro de toda la biblioteca local.

## Estado del proyecto

Version inicial de pruebas. Ya permite instalarse y usarse en Windows, pero todavia debe revisarse bien antes de distribuirse a usuarios finales.

Este repositorio publico se publica como codigo fuente visible para revision y pruebas. Manualtech sigue siendo software propietario: no se permite copiar, revender, redistribuir, republicar ni crear versiones derivadas sin permiso escrito del titular. Consulta `LICENSE.txt`.

## Funciones principales

- Aplicacion de escritorio local creada con Python y PySide6.
- Biblioteca local de manuales en PDF.
- Importacion de PDFs individuales.
- Importacion de carpetas con imagenes JPG, PNG, BMP, TIFF o WEBP.
- Conversion local de imagenes a PDF.
- Extraccion de texto con PyMuPDF.
- OCR local opcional para PDFs escaneados o carpetas de imagenes.
- Base de datos SQLite creada automaticamente.
- Busqueda de texto completo con SQLite FTS5.
- Resultados con documento, pagina, fragmento y metadatos.
- Fragmentos con coincidencias resaltadas.
- Vista previa de la pagina encontrada renderizada como imagen.
- Apertura del PDF desde el programa, intentando abrir en la pagina encontrada cuando el visor lo permite.
- Clasificacion por categoria: coche, moto, reparacion general, electronica/diagnosis, herramientas/procedimientos, ficha propia u otro.
- Gestion de biblioteca desde un dialogo separado.
- Reindexado completo.
- Eliminacion de manuales.
- Logo e icono de Manualtech.
- Preparado para empaquetar como `.exe` con PyInstaller.
- Instalador de Windows con Inno Setup, licencia y desinstalador.

## Privacidad

Manualtech trabaja en local.

- No sube PDFs a internet.
- No necesita servidor.
- No necesita cuenta.
- No necesita suscripciones.

Los manuales, la base de datos, las previews y los logs se guardan en el equipo del usuario.

## Estructura

```text
BuscadorManualesTaller/
|-- main.py
|-- requirements.txt
|-- README.md
|-- LICENSE.txt
|-- THIRD_PARTY_NOTICES.md
|-- Manualtech.spec
|-- build_installer.ps1
|-- app/
|   |-- __init__.py
|   |-- database.py
|   |-- models.py
|   |-- paths.py
|   |-- pdf_processor.py
|   |-- pdf_viewer.py
|   |-- search_engine.py
|   `-- ui_main.py
|-- assets/
|   |-- manualtech_logo.png
|   `-- manualtech.ico
|-- data/
|   `-- tessdata/
|       |-- eng.traineddata
|       `-- spa.traineddata
`-- installer/
    `-- Manualtech.iss
```

Las carpetas de datos de usuario no deben subirse al repositorio:

- `data/manuales/`
- `data/previews/`
- `data/manuales.db`
- `logs/`
- `build/`
- `dist/`
- `installer_output/`
- `release/`

## Requisitos para desarrollo

- Windows 10 u 11.
- Python 3.11 o superior.
- SQLite con FTS5 habilitado, incluido normalmente en Python para Windows.
- Dependencias Python:
  - PySide6
  - PyMuPDF

Instalacion de dependencias:

```powershell
cd BuscadorManualesTaller
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Ejecutar en modo desarrollo

```powershell
python main.py
```

Se abre la ventana de escritorio de Manualtech.

En modo desarrollo, los datos se guardan dentro de la carpeta del proyecto:

```text
data/manuales/
data/previews/
data/manuales.db
logs/app.log
```

## Uso basico

1. Pulsa `Anadir PDF` para importar un manual en PDF.
2. Completa los metadatos disponibles: categoria, titulo, tema, marca, modelo, ano, motor, sistema, tipo, idioma y notas.
3. Manualtech copia el PDF a la biblioteca local.
4. Extrae el texto pagina por pagina.
5. Guarda las paginas en SQLite e indexa el contenido con FTS5.
6. Busca desde la barra superior.
7. Selecciona un resultado para ver la preview de la pagina.
8. Usa `Abrir PDF` para abrir el documento con el visor predeterminado.

## Carpetas de imagenes y OCR

Manualtech puede importar una carpeta de imagenes y convertirla a PDF. Es util cuando un manual esta formado por paginas sueltas en JPG o PNG.

Formatos aceptados:

- `.jpg`
- `.jpeg`
- `.png`
- `.bmp`
- `.tif`
- `.tiff`
- `.webp`

Despues de crear el PDF, Manualtech intenta aplicar OCR local para que el contenido sea buscable.

## OCR local

El OCR no usa nube ni APIs. Se hace en local mediante Tesseract/OCR integrado por PyMuPDF.

El proyecto incluye datos OCR basicos en:

```text
data/tessdata/eng.traineddata
data/tessdata/spa.traineddata
```

Si necesitas una instalacion completa de Tesseract en Windows, puedes instalarla con:

```powershell
winget install --id UB-Mannheim.TesseractOCR -e
```

El OCR es mas lento que extraer texto normal. Un manual escaneado grande puede tardar varios minutos.

## Crear el ejecutable

Instala PyInstaller:

```powershell
python -m pip install pyinstaller
```

Compila el ejecutable:

```powershell
python -m PyInstaller --noconfirm .\Manualtech.spec
```

Salida esperada:

```text
dist/Manualtech.exe
```

## Crear el instalador de Windows

Instala Inno Setup:

```powershell
winget install --id JRSoftware.InnoSetup -e
```

Despues ejecuta:

```powershell
.\build_installer.ps1
```

Salida esperada:

```text
installer_output/Manualtech_Setup.exe
```

El instalador:

- muestra la licencia antes de instalar;
- instala Manualtech en `%LOCALAPPDATA%\Programs\Manualtech`;
- crea entrada en el menu Inicio;
- puede crear acceso directo en el escritorio;
- registra el desinstalador en Windows.

En modo instalado, los datos del usuario se guardan fuera de la carpeta del programa:

```text
%LOCALAPPDATA%\Manualtech\data\
%LOCALAPPDATA%\Manualtech\logs\
```

Esto evita mezclar el ejecutable con la biblioteca personal del usuario.

## Crear un ZIP de pruebas

Cuando ya exista el instalador, puedes empaquetarlo para enviarlo a otra persona:

```powershell
Compress-Archive -Path .\installer_output\Manualtech_Setup.exe, .\LICENSE.txt, .\THIRD_PARTY_NOTICES.md -DestinationPath .\release\Manualtech_Pruebas.zip -Force
```

El ZIP debe incluir el instalador, no los PDFs privados ni la base de datos local.

## Licencia

Manualtech es software propietario. El codigo y los recursos propios se publican para revision y pruebas, pero no se concede permiso para redistribuir el programa ni crear versiones derivadas sin autorizacion escrita.

Consulta:

- `LICENSE.txt`
- `THIRD_PARTY_NOTICES.md`

## Aviso sobre dependencias

PyMuPDF/MuPDF tiene condiciones de licencia importantes. Si Manualtech va a distribuirse como producto propietario cerrado, conviene revisar la licencia comercial de PyMuPDF/MuPDF o sustituir esa dependencia por una alternativa compatible.

PySide6/Qt tambien tiene obligaciones de licencia open source/comercial que deben revisarse antes de distribuir una version final.
