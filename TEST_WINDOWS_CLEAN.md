# Prueba en Windows limpio sin Python

Objetivo: comprobar que Manualtech Beta se instala y funciona en un Windows 10
u 11 limpio, sin Python ni dependencias instaladas manualmente.

## Preparación

1. En el equipo de desarrollo, crear el instalador:

```powershell
.\build_installer.ps1
```

2. Localizar el instalador:

```text
installer_output/Manualtech_1.0.0_Setup.exe
```

3. Copiar el instalador o el ZIP beta a un Windows limpio o máquina virtual:

```text
release/Manualtech_1.0.0_Beta_MSL.zip
```

4. Tener preparado un serial válido generado con:

```powershell
python generar_serial.py
```

## Pasos de prueba

1. Extraer el ZIP beta en el Windows limpio.
2. Ejecutar `Manualtech_1.0.0_Setup.exe`.
3. Aceptar la EULA.
4. Instalar la aplicación.
5. Abrir Manualtech desde el menú Inicio o el acceso directo.
6. Comprobar que no pide instalar Python.
7. Comprobar que arranca correctamente.
8. Introducir el serial en la ventana de activación.
9. Confirmar que se muestra:

```text
Manualtech activado correctamente.
```

10. Comprobar que se crea la carpeta:

```text
%LOCALAPPDATA%\Manualtech\
```

11. Comprobar que se crean:

```text
%LOCALAPPDATA%\Manualtech\data\
%LOCALAPPDATA%\Manualtech\logs\
%LOCALAPPDATA%\Manualtech\license.json
```

12. Añadir un PDF de prueba.
13. Buscar una palabra que exista en el PDF.
14. Seleccionar un resultado y visualizar la página.
15. Pulsar `Abrir PDF`.
16. Verificar que Manualtech aparece en aplicaciones instaladas de Windows.
17. Ejecutar el desinstalador.
18. Comprobar que el desinstalador no borra la biblioteca del usuario sin aviso.

## Resultado esperado

- Manualtech abre sin errores.
- La interfaz se muestra correctamente.
- El logo aparece correctamente.
- Se puede introducir serial.
- Después de activar, se puede usar la app.
- Se puede añadir un PDF.
- Se puede buscar.
- Se puede visualizar una página.
- Se puede abrir el PDF desde la aplicación.
- No se necesita Python instalado en el equipo de prueba.

## Errores frecuentes

### Falta DLL

Puede indicar que PyInstaller no incluyó alguna dependencia o que el sistema no
tiene componentes de Windows esperados.

### No carga PySide6

Puede indicar problema de empaquetado. Revisar `build/Manualtech/warn-Manualtech.txt`.

### No encuentra assets

Si no aparece el logo o icono, revisar que `assets/` esté incluido en
`Manualtech.spec`.

### No encuentra tessdata

Si el OCR no funciona, revisar que se incluyan:

```text
data/tessdata/eng.traineddata
data/tessdata/spa.traineddata
```

### Windows bloquea el ejecutable por no estar firmado

Es normal en beta si el instalador no tiene firma digital. Para venta final,
firmar `Manualtech.exe` y `Manualtech_1.0.0_Setup.exe`.

### El antivirus muestra advertencia

Puede ocurrir con ejecutables nuevos generados con PyInstaller. Para reducirlo:

- Firmar el ejecutable.
- Distribuir solo desde `motorsuitelab.com`.
- Evitar empaquetados modificados por terceros.
- Probar en varios equipos antes de entregar a clientes.

## Aprobación

Marcar esta prueba como aprobada solo si:

- [ ] Instala sin Python.
- [ ] Arranca sin errores.
- [ ] Permite activar con serial.
- [ ] Crea carpetas locales correctamente.
- [ ] Añade PDF.
- [ ] Busca texto.
- [ ] Muestra preview.
- [ ] Abre PDF.
- [ ] Desinstala correctamente.
