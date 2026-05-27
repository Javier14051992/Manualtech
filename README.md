# Manualtech

![Logo de Manualtech](assets/manualtech_logo.png)

Manualtech es una aplicación local de escritorio para Windows, propiedad de MSL
MotorSuiteLab, pensada para guardar, clasificar, indexar y buscar manuales de
taller sin usar servidores, nube ni servicios de pago.

El objetivo es sencillo: añadir PDFs o carpetas de imágenes de manuales, extraer
texto página por página, aplicar OCR local si hace falta, indexarlo en SQLite
FTS5 y encontrar rápidamente una avería, pieza, procedimiento, código o sistema
dentro de toda la biblioteca local.

## Estado comercial

Manualtech 1.0.0 está preparado como **beta comercial de pago** para un grupo
controlado de usuarios. No debe venderse todavía como producto final definitivo
hasta completar `COMMERCIAL_RELEASE_CHECKLIST.md`.

La venta y distribución autorizada debe realizarse exclusivamente a través de:

https://motorsuitelab.com

Manualtech es software propietario de MSL MotorSuiteLab. Aunque el código esté
visible en un repositorio, no se concede permiso para copiar, revender,
redistribuir, republicar ni crear versiones derivadas sin autorización escrita.
Consulta `LICENSE.txt` y `EULA.txt`.

## Entrega digital y reembolsos

Manualtech se entrega como producto digital descargable. La compra puede incluir
un archivo ZIP con el instalador y una clave de activación. Manualtech no
incluye manuales de taller. El usuario añade su propia documentación. La
política de reembolsos se basa en la entrega digital del producto y en las
condiciones aceptadas durante la compra.

## Funciones principales

- Aplicación de escritorio local creada con Python y PySide6.
- Activación local mediante serial simple, sin servidor.
- Biblioteca local de manuales en PDF.
- Importación de PDFs individuales.
- Importación de carpetas con imágenes JPG, PNG, BMP, TIFF o WEBP.
- Conversión local de imágenes a PDF.
- Extracción de texto con PyMuPDF.
- OCR local opcional para PDFs escaneados o carpetas de imágenes.
- Base de datos SQLite creada automáticamente.
- Búsqueda de texto completo con SQLite FTS5.
- Resultados con documento, página, fragmento y metadatos.
- Fragmentos con coincidencias resaltadas.
- Vista previa de la página encontrada renderizada como imagen.
- Apertura del PDF desde el programa, intentando abrir en la página encontrada
  cuando el visor lo permite.
- Clasificación por categoría: coche, moto, reparación general,
  electrónica/diagnosis, herramientas/procedimientos, ficha propia u otro.
- Gestión de biblioteca desde un diálogo separado.
- Reindexado completo.
- Eliminación de manuales.
- Logo e icono de Manualtech.
- Instalador de Windows con Inno Setup, EULA y desinstalador.

## Privacidad

Manualtech trabaja en local.

- No sube PDFs a internet.
- No necesita servidor.
- No necesita cuenta.
- No necesita suscripciones.

Los manuales, la base de datos, las previews, la activación local y los logs se
guardan en el equipo del usuario.

## Estructura

```text
BuscadorManualesTaller/
|-- main.py
|-- generar_serial.py
|-- requirements.txt
|-- README.md
|-- LICENSE.txt
|-- EULA.txt
|-- TERMS_OF_SALE.md
|-- PRIVACY_POLICY.md
|-- REFUND_POLICY.md
|-- COMMERCIAL_RELEASE_CHECKLIST.md
|-- TEST_WINDOWS_CLEAN.md
|-- TEST_DOCUMENTS_PLAN.md
|-- THIRD_PARTY_NOTICES.md
|-- Manualtech.spec
|-- build_installer.ps1
|-- app/
|   |-- __init__.py
|   |-- database.py
|   |-- licensing.py
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

Las carpetas de datos de usuario no deben subirse ni incluirse en el ZIP final:

- `data/manuales/`
- `data/previews/`
- `data/manuales.db`
- `logs/`
- `build/`
- `dist/`
- `installer_output/`
- `release/`
- `.venv/`
- `__pycache__/`

## Requisitos para desarrollo

- Windows 10 u 11.
- Python 3.11 o superior.
- SQLite con FTS5 habilitado, incluido normalmente en Python para Windows.
- Dependencias Python:
  - PySide6
  - PyMuPDF

Instalación de dependencias:

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

Al iniciar, si Manualtech no está activado, aparecerá la ventana de activación.
Introduce un serial válido con formato:

```text
MT-XXXX-XXXX-XXXX-XXXX
```

En modo desarrollo, los datos se guardan dentro de la carpeta del proyecto:

```text
data/manuales/
data/previews/
data/manuales.db
license.json
logs/app.log
```

En modo instalado, los datos se guardan normalmente en:

```text
%LOCALAPPDATA%\Manualtech\
```

## Generar seriales beta

Manualtech usa un serial local simple para esta primera beta comercial. No hay
servidor, activación online, cuenta de usuario ni pagos integrados.

Generar un serial:

```powershell
python generar_serial.py
```

Generar varios seriales:

```powershell
python generar_serial.py --cantidad 10
```

Ejemplo de formato:

```text
MT-7K2D-91PQ-A8ZL-R4TX
```

El serial no se guarda en texto plano. Manualtech guarda un archivo local de
activación en `license.json` con producto, tipo de licencia, estado, fecha y
hash de validación.

## Uso básico

1. Activa Manualtech con un serial válido.
2. Pulsa `Añadir PDF` para importar un manual en PDF.
3. Completa los metadatos disponibles: categoría, título, tema, marca, modelo,
   año, motor, sistema, tipo, idioma y notas.
4. Manualtech copia el PDF a la biblioteca local.
5. Extrae el texto página por página.
6. Guarda las páginas en SQLite e indexa el contenido con FTS5.
7. Busca desde la barra superior.
8. Selecciona un resultado para ver la preview de la página.
9. Usa `Abrir PDF` para abrir el documento con el visor predeterminado.

## Rendimiento con bibliotecas grandes

Manualtech está preparado para manejar bibliotecas con muchos documentos y miles
de páginas, con estas decisiones técnicas:

- Indexado página a página por streaming para no cargar todo el texto del PDF en
  memoria antes de guardarlo.
- SQLite en modo WAL para mejorar lecturas y escrituras locales.
- SQLite FTS5 en modo external content para reducir duplicación de texto en la
  base de datos.
- Búsquedas limitadas a resultados relevantes para evitar saturar la interfaz.
- Cache de previews limitada para que `data/previews/` no crezca sin control.
- Reindexado con optimización del índice FTS al terminar.

Limitaciones actuales:

- La importación y el OCR se ejecutan en el proceso principal; durante manuales
  grandes la interfaz puede quedar ocupada aunque muestre progreso.
- El OCR de PDFs escaneados sigue siendo la operación más lenta.
- Carpetas con miles de imágenes muy pesadas pueden requerir mucha memoria al
  convertirse a PDF.

## Carpetas de imágenes y OCR

Manualtech puede importar una carpeta de imágenes y convertirla a PDF. Es útil
cuando un manual está formado por páginas sueltas en JPG o PNG.

Formatos aceptados:

- `.jpg`
- `.jpeg`
- `.png`
- `.bmp`
- `.tif`
- `.tiff`
- `.webp`

Después de crear el PDF, Manualtech intenta aplicar OCR local para que el
contenido sea buscable.

## OCR local

El OCR no usa nube ni APIs. Se hace en local mediante Tesseract/OCR integrado
por PyMuPDF.

El proyecto incluye datos OCR básicos en:

```text
data/tessdata/eng.traineddata
data/tessdata/spa.traineddata
```

Si necesitas una instalación completa de Tesseract en Windows, puedes instalarla
con:

```powershell
winget install --id UB-Mannheim.TesseractOCR -e
```

El OCR es más lento que extraer texto normal. Un manual escaneado grande puede
tardar varios minutos.

## Preparar beta comercial

Flujo recomendado para preparar una beta de pago:

1. Generar seriales para los testers:

```powershell
python generar_serial.py --cantidad 10
```

2. Compilar ejecutable, crear instalador y crear ZIP limpio:

```powershell
.\build_installer.ps1
```

3. Revisar el ZIP final:

```text
release/manualtech-1.0.zip
```

4. Probar en Windows limpio siguiendo:

```text
TEST_WINDOWS_CLEAN.md
```

5. Probar con documentos reales siguiendo:

```text
TEST_DOCUMENTS_PLAN.md
```

6. Entregar al usuario:

- ZIP final o enlace de descarga.
- Serial personal o clave de activación.
- Aviso de que Manualtech no incluye manuales.
- Aviso de que los documentos del usuario se guardan localmente.

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

## Crear el instalador y ZIP beta

Instala Inno Setup:

```powershell
winget install --id JRSoftware.InnoSetup -e
```

Después ejecuta:

```powershell
.\build_installer.ps1
```

Salidas esperadas:

```text
installer_output/Manualtech_1.0.0_Setup.exe
release/manualtech-1.0.zip
```

El ZIP final incluye:

- `Manualtech_1.0.0_Setup.exe`
- `LICENSE.txt`
- `EULA.txt`
- `TERMS_OF_SALE.md`
- `PRIVACY_POLICY.md`
- `REFUND_POLICY.md`
- `THIRD_PARTY_NOTICES.md`
- `README.md`

No incluye manuales, base de datos, previews, logs, builds anteriores ni PDFs
privados.

## Licencia

Manualtech es software propietario de MSL MotorSuiteLab. Su distribución
comercial autorizada se realiza exclusivamente desde `motorsuitelab.com`.

Consulta:

- `LICENSE.txt`
- `EULA.txt`
- `TERMS_OF_SALE.md`
- `PRIVACY_POLICY.md`
- `REFUND_POLICY.md`
- `THIRD_PARTY_NOTICES.md`
- `COMMERCIAL_RELEASE_CHECKLIST.md`

## Aviso sobre dependencias

PyMuPDF/MuPDF tiene condiciones de licencia importantes. Si Manualtech va a
distribuirse como producto propietario cerrado, conviene revisar la licencia
comercial de PyMuPDF/MuPDF o sustituir esa dependencia por una alternativa
compatible.

PySide6/Qt también tiene obligaciones de licencia open source/comercial que
deben revisarse antes de distribuir una versión final.
