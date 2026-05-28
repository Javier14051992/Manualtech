# Servidor de activación de Manualtech Beta

Backend mínimo para activar seriales Beta de Manualtech una sola vez.

## Función

- Guarda seriales válidos en SQLite.
- Recibe activaciones desde Manualtech.
- Comprueba si el serial existe y está disponible.
- Marca el serial como usado.
- Devuelve una licencia Beta firmada de 30 días.

## Instalación local

```powershell
cd activation_server
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Variables recomendadas

Define al menos la ruta de la base de datos si quieres controlar dónde se guarda:

```powershell
$env:MANUALTECH_ACTIVATION_DB="activation_server.sqlite"
```

Importante: para esta beta, el servidor y la app compilada deben usar los mismos
secretos internos para validar seriales y licencias. No cambies
`MANUALTECH_SERIAL_SECRET`, `MANUALTECH_SERIAL_HASH_SECRET` ni
`MANUALTECH_LICENSE_SECRET` en el servidor salvo que recompiles Manualtech con
valores compatibles.

## Arrancar en local

```powershell
uvicorn main:app --host 127.0.0.1 --port 8000
```

Endpoint local:

```text
http://127.0.0.1:8000/api/manualtech/activate
```

Para probar la app contra el servidor local:

```powershell
$env:MANUALTECH_ACTIVATION_URL="http://127.0.0.1:8000/api/manualtech/activate"
python ..\main.py
```

## Generar y cargar seriales

Desde la carpeta principal de Manualtech:

```powershell
python generar_serial.py --cantidad 100 --salida seriales_beta.txt
```

Desde `activation_server/`:

```powershell
python seed_serials.py ..\seriales_beta.txt
```

No subas `seriales_beta.txt` ni la base de datos a Git.

## Probar con curl

```powershell
curl -X POST http://127.0.0.1:8000/api/manualtech/activate `
  -H "Content-Type: application/json" `
  -d "{\"product\":\"Manualtech\",\"serial\":\"MT-XXXX-XXXX-XXXX-XXXX\",\"machine_id_hash\":\"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\",\"version\":\"1.0.0-beta\"}"
```

## Despliegue

Despliega este servicio detrás de HTTPS en el dominio configurado en la app:

```text
https://motorsuitelab.com/api/manualtech/activate
```

La base SQLite debe persistir entre despliegues. Haz copias de seguridad antes
de actualizar el servidor.
