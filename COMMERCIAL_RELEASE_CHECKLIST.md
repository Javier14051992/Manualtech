# Checklist comercial de Manualtech

Última actualización: 26 de mayo de 2026

Manualtech no debe publicarse como producto comercial final hasta completar esta
lista.

Fecha prevista de salida de la Beta: 5 de junio de 2026.

## Obligatorio antes de vender

- [ ] Poner el repositorio de GitHub en privado si el código no debe estar
      visible públicamente.
- [ ] Revisar `LICENSE.txt`, `EULA.txt`, `TERMS_OF_SALE.md`,
      `PRIVACY_POLICY.md` y `REFUND_POLICY.md` con asesoría legal.
- [ ] Resolver la licencia comercial de PyMuPDF/MuPDF o sustituir la
      dependencia por una alternativa compatible con venta propietaria.
- [ ] Revisar el cumplimiento de PySide6/Qt para distribución comercial.
- [ ] Confirmar que los datos OCR incluidos se pueden redistribuir dentro del
      producto.
- [ ] Comprar o validar la licencia comercial de Inno Setup si se usa para
      crear instaladores comerciales.
- [ ] Firmar `Manualtech.exe` y `Manualtech_Setup.exe` con certificado de firma
      de código.
- [ ] Probar instalación en un Windows limpio sin Python instalado.
- [ ] Probar activación online inicial con serial válido no usado.
- [ ] Probar rechazo de serial inválido.
- [ ] Probar rechazo de serial ya usado.
- [ ] Probar funcionamiento offline después de activar.
- [ ] Probar bloqueo por licencia caducada.
- [ ] Probar importación de PDF con texto.
- [ ] Probar importación de PDF escaneado con OCR.
- [ ] Probar importación de carpeta de imágenes.
- [ ] Probar búsqueda, previews, apertura por página, reindexado y eliminación.
- [ ] Verificar que el desinstalador no borra la biblioteca del usuario sin
      aviso explícito.
- [ ] Crear ZIP final sin datos privados y sin la palabra "Pruebas".
- [ ] Publicar términos de venta, privacidad y reembolsos en motorsuitelab.com.
- [ ] Verificar que el ZIP final no incluye `activation_server/`,
      `generar_serial.py`, seriales, bases de datos ni código fuente.

## Estado recomendado

Hasta completar la lista anterior, usar la etiqueta:

Manualtech 1.0.0 - Beta comercial

No usar todavía:

Producto comercial final
