# Plan de prueba con documentos reales

Objetivo: validar Manualtech con documentos técnicos típicos antes de publicar una versión estable.

## Tabla de pruebas

| Nº | Documento | Objetivo | Pasos | Resultado esperado | Posibles errores | Criterio de aprobado |
|---:|---|---|---|---|---|---|
| 1 | PDF normal con texto seleccionable | Confirmar indexado inmediato sin OCR. | Añadir PDF, completar metadatos, buscar una palabra visible. | El PDF se añade, se indexa y la búsqueda devuelve resultados con página y fragmento. | PDF corrupto, texto mal extraído, consulta demasiado específica. | Se encuentra una palabra real y se muestra preview correcta. |
| 2 | PDF escaneado sin texto | Confirmar comportamiento OCR. | Activar OCR local, añadir PDF escaneado, esperar extracción, buscar una palabra visible. | Con OCR disponible, extrae texto e indexa. Sin OCR, muestra aviso claro. | OCR lento, idioma incorrecto, mala calidad de escaneo, falta tessdata. | No se cierra la app y el usuario recibe resultado o aviso comprensible. |
| 3 | PDF grande de muchas páginas | Confirmar estabilidad con volumen. | Añadir PDF grande, observar progreso, buscar varias palabras. | Manualtech no se cierra, muestra progreso y permite buscar al terminar. | Proceso lento, consumo alto de memoria, usuario cree que está bloqueado. | Finaliza sin error y la búsqueda funciona. |
| 4 | PDF protegido con contraseña | Confirmar error controlado. | Intentar añadir PDF protegido. | Muestra: `El PDF está protegido con contraseña y no se puede indexar.` | Mensaje genérico, excepción sin controlar, PDF parcialmente dañado. | La app no se cierra y muestra el mensaje esperado. |
| 5 | Carpeta de imágenes JPG/PNG convertida a PDF | Validar conversión + OCR. | Seleccionar carpeta de imágenes, completar metadatos, convertir, aplicar OCR, buscar texto visible. | Convierte imágenes a PDF, aplica OCR local si está disponible e indexa el resultado. | Imágenes enormes, nombres desordenados, OCR no disponible, formato no soportado. | El PDF generado aparece en biblioteca y se puede buscar o muestra aviso claro. |

## Detalle de pruebas

### Prueba 1: PDF normal con texto seleccionable

Debe añadirse, indexarse y permitir búsqueda inmediata sin depender de OCR.

### Prueba 2: PDF escaneado sin texto

Debe añadirse. Con OCR local activado debe intentar extraer texto. Si no hay Tesseract/OCR disponible, debe mostrar un aviso claro.

### Prueba 3: PDF grande

Debe comprobarse que Manualtech no se cierra y que muestra progreso. Si tarda, debe informar al usuario mediante la barra de estado.

### Prueba 4: PDF protegido con contraseña

Debe mostrar el mensaje:

```text
El PDF está protegido con contraseña y no se puede indexar.
```

### Prueba 5: Carpeta de imágenes

Debe convertir imágenes a PDF, aplicar OCR local si está disponible e indexar el resultado.

## Checklist final

- [ ] Añadir PDF funciona.
- [ ] Añadir carpeta funciona.
- [ ] OCR local probado.
- [ ] Búsqueda probada.
- [ ] Vista previa probada.
- [ ] Abrir PDF probado.
- [ ] Reindexar probado.
- [ ] Eliminar manual probado.
- [ ] Manualtech arranca sin serial, cuenta ni activación.
- [ ] La funcionalidad principal funciona sin internet.
- [ ] No se sube automáticamente ningún manual del usuario a internet.
- [ ] No se incluyen manuales privados en el ZIP final.
- [ ] El paquete incluye licencia y referencia al código fuente.
