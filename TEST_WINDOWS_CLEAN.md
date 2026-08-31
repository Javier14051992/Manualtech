# Prueba en Windows limpio sin Python

Objetivo: comprobar que Manualtech se instala y funciona en un Windows 10/11 limpio, sin Python ni dependencias instaladas manualmente y **sin solicitar códigos de instalación o activación**.

## Preparación

1. En el equipo de desarrollo, generar el ZIP:

```powershell
.\build_installer.ps1
```

2. Localizar el ZIP:

```text
release/Manualtech_1.0.0_Windows.zip
```

3. Confirmar que el paquete incluye al menos:

- `Manualtech_1.0.0_Setup.exe`
- `LICENSE.txt`
- `THIRD_PARTY_NOTICES.md`
- `README.md`
- `SOURCE_CODE.md`

## Pasos de prueba

1. Copiar el ZIP al Windows limpio o máquina virtual.
2. Extraer el ZIP.
3. Ejecutar `Manualtech_1.0.0_Setup.exe`.
4. Revisar la licencia AGPL mostrada por el instalador.
5. Instalar la aplicación.
6. Abrir Manualtech desde el menú Inicio o acceso directo.
7. Comprobar que no pide instalar Python.
8. Confirmar que **no solicita serial, clave, cuenta ni activación**.
9. Confirmar que se crea la estructura de datos local bajo:

```text
%LOCALAPPDATA%\Manualtech\
```

10. Abrir `Estado de licencia` y comprobar que muestra Manualtech como open source bajo GNU AGPL v3.0 o posterior y sin caducidad.
11. Cerrar Manualtech.
12. Desconectar internet.
13. Abrir Manualtech de nuevo.
14. Confirmar que arranca y funciona sin conexión.
15. Añadir un PDF de prueba que pueda utilizarse legalmente.
16. Buscar una palabra que exista en el PDF.
17. Seleccionar un resultado y visualizar la página.
18. Pulsar `Abrir PDF`.
19. Comprobar que Manualtech aparece en aplicaciones instaladas de Windows.
20. Ejecutar el desinstalador.
21. Comprobar que el desinstalador no borra la biblioteca del usuario sin aviso.

## Resultado esperado

- Manualtech abre sin errores.
- No existe ningún paso de activación.
- No se solicita serial ni código de instalación.
- Funciona offline.
- La interfaz se muestra correctamente.
- El logo aparece correctamente.
- Se puede añadir un PDF.
- Se puede buscar.
- Se puede visualizar una página.
- Se puede abrir el PDF desde la aplicación.
- No se necesita Python instalado en el equipo de prueba.
- El paquete informa de dónde obtener el código fuente.

## Errores frecuentes

### Falta DLL

Puede indicar que PyInstaller no incluyó alguna dependencia o que el sistema no tiene componentes de Windows esperados.

### No carga PySide6

Puede indicar un problema de empaquetado. Revisar `build/Manualtech/warn-Manualtech.txt`.

### No encuentra assets

Si no aparece el logo o icono, revisar que `assets/` esté incluido en `Manualtech.spec`.

### No encuentra tessdata

Si el OCR no funciona, revisar que se incluyan:

```text
data/tessdata/eng.traineddata
data/tessdata/spa.traineddata
```

### Windows bloquea el ejecutable por no estar firmado

Windows puede advertir sobre ejecutables nuevos o no firmados. La firma de código es independiente de que Manualtech sea open source.

### El antivirus muestra advertencia

Puede ocurrir con ejecutables nuevos generados con PyInstaller. Conviene probar el instalador en varios equipos y publicar hashes o releases verificables cuando se distribuyan binarios oficiales.

## Aprobación

- [ ] Instala sin Python.
- [ ] No solicita serial ni activación.
- [ ] Funciona sin conexión.
- [ ] Muestra licencia AGPL y sin caducidad.
- [ ] Crea carpetas locales correctamente.
- [ ] Añade PDF.
- [ ] Busca texto.
- [ ] Muestra preview.
- [ ] Abre PDF.
- [ ] Desinstala correctamente.
- [ ] Incluye referencia al código fuente.
