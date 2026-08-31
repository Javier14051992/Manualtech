# Manualtech

![Logo de Manualtech](assets/manualtech_logo.png)

**Manualtech** es una aplicación de escritorio open source para Windows pensada para guardar, clasificar, indexar y buscar documentación técnica de taller de forma local.

El objetivo es sencillo: añadir PDFs o carpetas de imágenes, extraer el texto página por página, aplicar OCR local cuando sea necesario, indexarlo con SQLite FTS5 y encontrar rápidamente una avería, pieza, procedimiento, código o sistema dentro de toda la biblioteca.

## Open source y privacidad

Manualtech funciona **sin cuenta, sin códigos de instalación, sin activación y sin suscripción**.

- El código fuente está disponible en este repositorio.
- Los documentos del usuario no se suben a la nube.
- La búsqueda y el indexado se realizan localmente.
- No existe servidor de activación ni comprobación de seriales.
- Los manuales, la base de datos, las previews y los logs se guardan en el equipo del usuario.

Manualtech se distribuye bajo **GNU Affero General Public License v3.0 o posterior (AGPL-3.0-or-later)**. Consulta `LICENSE.txt`.

## Funciones principales

- Aplicación de escritorio local creada con Python y PySide6.
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
- Vista previa de la página encontrada.
- Apertura del PDF desde el programa, intentando abrir en la página encontrada cuando el visor lo permite.
- Clasificación por categoría, marca, modelo, año, motor, sistema, tipo, idioma y notas.
- Gestión de biblioteca desde un diálogo separado.
- Reindexado completo.
- Eliminación de manuales.
- Instalador de Windows con Inno Setup.

## Qué NO incluye Manualtech

Manualtech **no incluye manuales de taller ni documentación oficial de fabricantes**. Cada usuario debe añadir únicamente documentación que tenga derecho a utilizar y es responsable de cumplir las condiciones aplicables a esos documentos.

## Requisitos

### Para ejecutar desde código fuente

- Python 3.11 o posterior recomendado.
- Windows 10/11 es la plataforma principal actualmente.
- Tesseract OCR es opcional para documentación escaneada.

Instala las dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Ejecuta Manualtech:

```powershell
python main.py
```

No se solicita ningún serial ni clave de activación.

## Datos locales

En modo instalado, los datos del usuario se guardan normalmente en:

```text
%LOCALAPPDATA%\Manualtech\
```

La biblioteca de documentos y la base de datos del usuario no forman parte del repositorio.

## Uso básico

1. Ejecuta Manualtech.
2. Pulsa `Añadir PDF` para importar un documento o `Añadir carpeta` para importar páginas en imágenes.
3. Completa los metadatos disponibles.
4. Manualtech copia el documento a la biblioteca local.
5. Extrae el texto página por página y aplica OCR local si es necesario.
6. Guarda las páginas en SQLite e indexa el contenido con FTS5.
7. Busca desde la barra superior.
8. Selecciona un resultado para ver la página encontrada.
9. Usa `Abrir PDF` para abrir el documento original.

## Rendimiento con bibliotecas grandes

Manualtech está preparado para trabajar con bibliotecas extensas mediante:

- Indexado página a página por streaming para no cargar todo el texto del PDF en memoria.
- SQLite en modo WAL para mejorar lecturas y escrituras locales.
- SQLite FTS5 en modo external content para reducir duplicación de texto.
- Límite de resultados para evitar saturar la interfaz.
- Caché de previews limitada.
- Optimización del índice FTS al terminar un reindexado.

Limitaciones actuales:

- La importación y el OCR se ejecutan en el proceso principal; documentos grandes pueden mantener la interfaz ocupada durante el procesamiento.
- El OCR de PDFs escaneados es la operación más lenta.
- Carpetas con miles de imágenes muy pesadas pueden requerir bastante memoria durante la conversión a PDF.

## OCR local

Manualtech no utiliza APIs cloud para OCR. Se apoya en Tesseract/PyMuPDF de forma local.

El repositorio incluye datos OCR básicos en:

```text
data/tessdata/eng.traineddata
data/tessdata/spa.traineddata
```

En Windows puedes instalar Tesseract con:

```powershell
winget install --id UB-Mannheim.TesseractOCR -e
```

## Crear el ejecutable e instalador de Windows

El script `build_installer.ps1` instala las dependencias necesarias, genera el ejecutable con PyInstaller y crea el instalador mediante Inno Setup.

```powershell
.\build_installer.ps1
```

El instalador generado no requiere códigos de activación.

## Dependencias y licencias de terceros

Manualtech utiliza, entre otros componentes:

- PySide6 / Qt for Python.
- PyMuPDF / MuPDF.
- Tesseract OCR.
- SQLite.
- Inno Setup para generar el instalador de Windows.

Consulta `THIRD_PARTY_NOTICES.md` para conocer sus licencias y avisos.

## Licencia

Copyright (c) 2026 MSL MotorSuiteLab.

El código de Manualtech se distribuye bajo **GNU Affero General Public License v3.0 o posterior (AGPL-3.0-or-later)**.

Puedes usar, estudiar, modificar y redistribuir el programa respetando las condiciones de la AGPL. Las versiones modificadas que se distribuyan deben conservar las obligaciones de esta licencia y facilitar el código fuente correspondiente cuando proceda.

## Marca

El nombre **Manualtech**, la identidad de **MSL MotorSuiteLab** y sus signos distintivos pueden estar protegidos como marcas o nombres comerciales. La licencia del código no concede permiso para presentar una versión modificada como producto oficial de MSL MotorSuiteLab ni para sugerir respaldo o afiliación inexistentes.

Los forks son bienvenidos, pero deben diferenciarse claramente si modifican sustancialmente el producto o su identidad.

## Contribuir

Issues, propuestas de mejora y pull requests son bienvenidos. Consulta `CONTRIBUTING.md` antes de enviar cambios.

Repositorio oficial:

https://github.com/Javier14051992/Manualtech
