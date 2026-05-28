# Prueba en Windows limpio sin Python

Objetivo: comprobar que Manualtech Beta se instala, activa y funciona en un
Windows 10/11 limpio, sin Python ni dependencias instaladas manualmente.

## Preparación

1. En el equipo de desarrollo, generar el ZIP Beta:

```powershell
.\build_installer.ps1
```

2. Localizar el ZIP:

```text
release/Manualtech_1.0.0_Beta_30dias_MSL.zip
```

3. Preparar un serial válido ya cargado en el servidor de activación.
4. Comprobar que el endpoint de producción responde por HTTPS:

```text
https://motorsuitelab.com/api/manualtech/activate
```

## Pasos de prueba

1. Copiar el ZIP Beta al Windows limpio o máquina virtual.
2. Extraer el ZIP.
3. Ejecutar `Manualtech_1.0.0_Setup.exe`.
4. Aceptar la EULA.
5. Instalar la aplicación.
6. Abrir Manualtech desde el menú Inicio o acceso directo.
7. Comprobar que no pide instalar Python.
8. Introducir un serial Beta válido.
9. Confirmar que se muestra:

```text
Manualtech Beta activado correctamente.
```

10. Comprobar que se crea:

```text
%LOCALAPPDATA%\Manualtech\license.json
%LOCALAPPDATA%\Manualtech\data\
%LOCALAPPDATA%\Manualtech\logs\
```

11. Abrir “Estado de licencia” y comprobar:

- Producto: Manualtech.
- Estado: Activado.
- Tipo de licencia: Beta 30 días.
- Fecha de activación.
- Fecha de caducidad.
- Días restantes.

12. Cerrar Manualtech.
13. Desconectar internet o bloquear temporalmente el servidor.
14. Abrir Manualtech de nuevo.
15. Confirmar que funciona offline sin pedir serial.
16. Añadir un PDF de prueba.
17. Buscar una palabra que exista en el PDF.
18. Seleccionar un resultado y visualizar la página.
19. Pulsar `Abrir PDF`.
20. Comprobar que Manualtech aparece en aplicaciones instaladas de Windows.
21. Ejecutar el desinstalador.
22. Comprobar que el desinstalador no borra la biblioteca del usuario sin aviso.

## Prueba de caducidad simulada

En una máquina de prueba, crear una copia de `license.json` antes de manipularlo.
Después:

1. Cambiar `expires_at` a una fecha pasada.
2. Abrir Manualtech.
3. Confirmar que la app bloquea el acceso por licencia no válida o caducada.
4. Restaurar el `license.json` original.

Nota: si se modifica manualmente una licencia firmada, la firma dejará de ser
válida. Para una prueba exacta de caducidad, generar una licencia caducada desde
un entorno controlado de pruebas.

## Resultado esperado

- Manualtech abre sin errores.
- La interfaz se muestra correctamente.
- El logo aparece correctamente.
- La activación inicial requiere internet.
- Después de activar, Manualtech funciona offline hasta la caducidad.
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

### No conecta con activación

Comprobar conexión a internet, HTTPS, DNS, firewall y disponibilidad del endpoint:

```text
https://motorsuitelab.com/api/manualtech/activate
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

- [ ] Instala sin Python.
- [ ] Activa online con serial válido.
- [ ] Rechaza serial inválido.
- [ ] Rechaza serial ya usado.
- [ ] Crea carpetas locales correctamente.
- [ ] Funciona offline después de activar.
- [ ] Muestra días restantes.
- [ ] Añade PDF.
- [ ] Busca texto.
- [ ] Muestra preview.
- [ ] Abre PDF.
- [ ] Desinstala correctamente.
