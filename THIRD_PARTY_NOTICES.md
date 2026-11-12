# Avisos de terceros

BioFig incluye o descarga recursos de terceros. Cada uno conserva su licencia original.

## Iconos e imágenes

| Recurso | Cómo se usa | Licencia | Atribución |
|---|---|---|---|
| [Bioicons](https://github.com/duerrsimon/bioicons) (Simon Dürr y colaboradores; incluye iconos de [Servier Medical Art](https://smart.servier.com)) | Se descarga con `instalar.py` (no se redistribuye en este repositorio) | Por icono: CC0, CC BY 3.0, CC BY 4.0, CC BY-SA, MIT o BSD | Obligatoria para CC BY / CC BY-SA: autor + licencia. El botón **Créditos** la genera |
| [Fluent Emoji](https://github.com/microsoft/fluentui-emoji) (Microsoft) | Se descarga con `instalar.py`; selección en `fuentes_extra.py` | MIT | Recomendada |
| [Health Icons](https://healthicons.org) (Resolve to Save Lives) | Se descarga con `instalar.py` | CC0 (dominio público) | No obligatoria |
| [PhyloPic](https://www.phylopic.org) | Se consulta en línea al buscar; se guarda en caché local | Por imagen: CC0, Public Domain Mark, CC BY, CC BY-SA (BioFig **excluye** las NC y ND) | Obligatoria para CC BY / CC BY-SA. El botón **Créditos** la genera |
| [RCSB Protein Data Bank](https://www.rcsb.org) | Coordenadas descargadas al usar el visor 3D; ejemplos en `static/pdb/` | Datos de dominio público (CC0) | Se recomienda citar la publicación de cada estructura |
| Iconos propios de BioFig (`static/builtin/`, `static/extra/`, `static/demo/`) | Incluidos | Libres, creados para este proyecto | — |

Estructuras de los ejemplos: 1JFF (Löwe J. et al. 2001, *J Mol Biol* 313:1045), 6A69 (Gong D. et al. 2018, *Nature* 563:516),
4F5S (Bujacz A. 2012, *Acta Cryst D* 68:1278).

## Software

| Componente | Licencia |
|---|---|
| [Konva](https://konvajs.org) (`static/vendor/konva.min.js`) | MIT |
| [3Dmol.js](https://3dmol.csb.pitt.edu) (`static/vendor/3Dmol-min.js`) | BSD-3-Clause |
| [rembg](https://github.com/danielgatis/rembg) (opcional) | MIT |
| Modelos de segmentación U²-Net / IS-Net (los descarga rembg) | Apache 2.0 |
| [ONNX Runtime](https://onnxruntime.ai) | MIT |
| [FastAPI](https://fastapi.tiangolo.com) / [Starlette](https://www.starlette.io) | MIT / BSD-3-Clause |
| [Uvicorn](https://www.uvicorn.org), [HTTPX](https://www.python-httpx.org), [watchfiles](https://github.com/samuelcolvin/watchfiles) | BSD-3-Clause / BSD-3-Clause / MIT |

## Servicios externos opcionales

- **Google Gemini** y **DeepSeek**: solo si cargás tu propia clave para generar figuras con IA. Se rigen por los términos de cada proveedor.
