# Prueba de activación Beta 30 días

Objetivo: comprobar el sistema de serial de un solo uso, licencia local de 30
días y funcionamiento offline posterior.

## Preparación

1. Generar seriales Beta:

```powershell
python generar_serial.py --cantidad 5 --salida seriales_beta.txt
```

2. Arrancar el servidor de activación local:

```powershell
cd activation_server
python -m pip install -r requirements.txt
python seed_serials.py ..\seriales_beta.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

3. En otra terminal, apuntar Manualtech al servidor local:

```powershell
$env:MANUALTECH_ACTIVATION_URL="http://127.0.0.1:8000/api/manualtech/activate"
python main.py
```

## Casos de prueba

| Nº | Prueba | Pasos | Resultado esperado | Aprobado |
| --- | --- | --- | --- | --- |
| 1 | Serial válido no usado | Introducir un serial cargado en el servidor. | Manualtech activa la Beta, crea `license.json` y abre la app. | [ ] |
| 2 | Serial inválido | Introducir una clave inventada o con formato incorrecto. | Muestra “Clave de activación no válida.” | [ ] |
| 3 | Serial ya usado | Intentar activar de nuevo con el mismo serial. | Muestra “Esta clave de activación ya ha sido utilizada.” | [ ] |
| 4 | Sin internet en primera activación | Cerrar el servidor o quitar conexión antes de activar. | Muestra que la activación inicial requiere conexión a internet. | [ ] |
| 5 | Licencia local válida | Abrir Manualtech después de activar. | Abre sin pedir internet ni serial. | [ ] |
| 6 | Licencia caducada | Editar una copia de prueba con `expires_at` pasado y firma inválida, o generar una licencia de prueba caducada. | Bloquea el uso e informa de caducidad o licencia no válida. | [ ] |
| 7 | Licencia manipulada | Cambiar cualquier campo de `license.json`. | Muestra “La licencia local no es válida.” | [ ] |
| 8 | Licencia copiada a otro equipo | Copiar `license.json` a otro Windows. | Muestra “Esta licencia no corresponde a este equipo.” | [ ] |
| 9 | Offline después de activar | Activar, cerrar internet/servidor y abrir Manualtech. | Funciona offline hasta la fecha de caducidad. | [ ] |
| 10 | Días restantes | Abrir “Estado de licencia”. | Muestra tipo Beta 30 días, fechas y días restantes. | [ ] |

## Criterio de aceptación

- [ ] El serial queda marcado como usado en SQLite.
- [ ] El mismo serial no puede activar otro equipo.
- [ ] La licencia local no guarda el serial en texto plano.
- [ ] La licencia contiene `serial_hash` y `machine_id_hash`.
- [ ] Manualtech funciona offline después de activar.
- [ ] La caducidad bloquea el uso al finalizar el periodo Beta.
