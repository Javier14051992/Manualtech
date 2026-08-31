# Contribuir a Manualtech

Gracias por tu interés en mejorar Manualtech.

## Antes de empezar

- Revisa los issues existentes antes de abrir uno nuevo.
- No subas manuales de taller, documentación de fabricantes ni otros archivos cuyo derecho de redistribución no esté claro.
- No incluyas datos personales, credenciales, claves, tokens ni archivos generados por tu biblioteca local.
- Mantén los cambios centrados y explica qué problema resuelven.

## Entorno de desarrollo

En Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Tesseract OCR es opcional para documentos escaneados.

## Pull requests

1. Crea una rama desde `main`.
2. Realiza cambios pequeños y comprensibles.
3. Comprueba que Manualtech arranca sin solicitar seriales, claves ni activación.
4. Comprueba la importación y búsqueda con documentación de prueba que puedas utilizar legalmente.
5. Describe en el pull request el cambio realizado y cómo lo has probado.

## Licencia de las contribuciones

Al enviar una contribución aceptas que tu aportación se distribuya bajo la misma licencia que Manualtech: **GNU Affero General Public License v3.0 o posterior (AGPL-3.0-or-later)**.

## Marca

Las contribuciones al código no implican cesión ni licencia adicional sobre la marca Manualtech o la identidad de MSL MotorSuiteLab más allá de los usos permitidos legalmente para identificar el proyecto.
