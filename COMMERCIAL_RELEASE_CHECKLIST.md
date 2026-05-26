# Checklist comercial de Manualtech

Ultima actualizacion: 26 de mayo de 2026

Manualtech no debe publicarse como producto comercial final hasta completar esta
lista.

## Obligatorio antes de vender

- [ ] Poner el repositorio de GitHub en privado si el codigo no debe estar
      visible publicamente.
- [ ] Revisar `LICENSE.txt`, `EULA.txt`, `TERMS_OF_SALE.md`,
      `PRIVACY_POLICY.md` y `REFUND_POLICY.md` con asesoria legal.
- [ ] Resolver la licencia comercial de PyMuPDF/MuPDF o sustituir la
      dependencia por una alternativa compatible con venta propietaria.
- [ ] Revisar el cumplimiento de PySide6/Qt para distribucion comercial.
- [ ] Confirmar que los datos OCR incluidos se pueden redistribuir dentro del
      producto.
- [ ] Comprar o validar la licencia comercial de Inno Setup si se usa para
      crear instaladores comerciales.
- [ ] Firmar `Manualtech.exe` y `Manualtech_Setup.exe` con certificado de firma
      de codigo.
- [ ] Probar instalacion en un Windows limpio sin Python instalado.
- [ ] Probar importacion de PDF con texto.
- [ ] Probar importacion de PDF escaneado con OCR.
- [ ] Probar importacion de carpeta de imagenes.
- [ ] Probar busqueda, previews, apertura por pagina, reindexado y eliminacion.
- [ ] Verificar que el desinstalador no borra la biblioteca del usuario sin
      aviso explicito.
- [ ] Crear ZIP final sin datos privados y sin la palabra "Pruebas".
- [ ] Publicar terminos de venta, privacidad y reembolsos en motorsuitelab.com.
- [ ] Decidir si habra activacion, clave offline o control de licencia.

## Estado recomendado

Hasta completar la lista anterior, usar la etiqueta:

Manualtech 1.0.0 - Release Candidate

No usar todavia:

Producto comercial final
