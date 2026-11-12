# BioFig — guía técnica

## Visión general

```
Navegador (static/)                         Servidor local (server.py, FastAPI en 127.0.0.1:8765)
┌───────────────────────────┐   HTTP/JSON   ┌──────────────────────────────────────────────┐
│ app.js       editor Konva │ ────────────► │ /api/icons, /api/projects, /api/export        │
│ pdb3d.js     visor 3Dmol  │               │ /api/pdb (RCSB) · /api/phylopic (PhyloPic)    │
│ custom_icons.js           │               │ /api/remove-bg (rembg, local)                 │
│ index.html, style.css     │               │ /api/ai/* (Gemini o DeepSeek, con tu clave)   │
└───────────────────────────┘               └──────────────────────────────────────────────┘
                                                     │ archivos
                                  data/ (proyectos, Mis iconos, cachés) · vendor_src/ (bibliotecas)
```

- El **frontend** es HTML, CSS y JavaScript sin compilación. El lienzo usa [Konva](https://konvajs.org) y el visor 3D, [3Dmol.js](https://3dmol.csb.pitt.edu); los dos están en `static/vendor/`.
- El **backend** es un único proceso de Python (FastAPI + Uvicorn) que escucha solo en `127.0.0.1`. Se recarga solo cuando cambia un `.py`, gracias a `watchfiles`.
- **Sin base de datos**: todo se guarda como archivos JSON y SVG/PNG en `data/`.

## Archivos principales

| Archivo | Responsabilidad |
|---|---|
| `server.py` | API, archivos estáticos, IA (cliente único para Gemini y DeepSeek), exportación |
| `phylopic.py` | Búsqueda en la API de PhyloPic, nombres comunes → científicos, caché en `data/phylopic/` |
| `bgremove.py` | Quitar fondo con rembg (sesiones por modelo, recorte del borde transparente) |
| `build_index.py` | Genera `data/icons.json` a partir de Bioicons, los iconos propios, Fluent Emoji y Health Icons |
| `fuentes_extra.py` | Lista curada de Fluent Emoji y Health Icons, con nombres en español y categoría |
| `make_builtin.py`, `make_extra_icons.py` | Generan los SVG propios (procedurales: lípidos, gráficos, etc.) |
| `instalar.py` | Instalador idempotente: entorno virtual, dependencias, bibliotecas fijadas por commit, índice y ejemplos |
| `static/app.js` | Editor: nodos, conectores, historial, propiedades, biblioteca, exportación, panel de IA |
| `static/pdb3d.js` | Visor 3D: carga del PDB, orientación por componentes principales, estilos, captura y tamaño real en Å |
| `static/custom_icons.js` | Ventana de icono personalizado, quitar fondo, Mis iconos |

## API

| Método y ruta | Uso |
|---|---|
| `GET /api/icons` · `GET /api/icons/search?q=` | Biblioteca completa y búsqueda (la usa la IA para elegir iconos) |
| `GET /api/phylopic/search?q=` · `GET /phylopic/{uuid}.svg` | Siluetas de organismos (proxy con caché) |
| `GET/POST /api/projects` · `GET/PUT/DELETE /api/projects/{id}` | Proyectos (`data/projects/*.json`) |
| `POST /api/export` | Guarda en `exports/` un PNG/JPG renderizado en el navegador |
| `GET /api/pdb/{código}` · `POST /api/pdb/render` | Coordenadas del RCSB (caché en `data/pdb_cache/`) y guardado de renders 3D |
| `GET /api/remove-bg/status` · `POST /api/remove-bg` | Estado de rembg y modelos; quitar fondo (data URL → PNG transparente) |
| `GET/POST /api/custom-icons` · `DELETE /api/custom-icons/{id}` | Mis iconos (`data/custom_icons/`) |
| `GET /api/ai/status` · `POST /api/ai/key` · `POST /api/ai/provider` · `POST /api/ai/figure` | IA: estado, guardar y verificar la clave, elegir proveedor, generar figura |
| `GET /api/version` | Permite a la página detectar un servidor desactualizado |

Archivos servidos: `/static` (la app), `/icons` (Bioicons), `/fluent`, `/healthicons`, `/custom` (Mis iconos).

## Formato de un proyecto (`data/projects/<id>.json`)

```jsonc
{
  "id": "mi-figura-1a2b3c", "name": "Mi figura", "updated": 1731400000.0,
  "thumb": "data:image/jpeg;base64,…",        // miniatura para «Abrir»
  "doc": {
    "w": 1600, "h": 1000, "bg": "#ffffff",
    "items": [                                  // en orden de dibujo (el último queda arriba)
      { "kind": "icon", "id": "n1", "x": 400, "y": 300, "width": 160, "height": 120, "rotation": 0,
        "src": "/icons/…svg", "iconId": "bi:…", "meta": {"name": "…", "author": "…", "license": "CC BY 4.0", "source": "Bioicons"},
        "tint": null, "flip": false, "alts": [], "pdb": null, "realW": null },
      { "kind": "text", "id": "n2", "text": "Etiqueta", "fontSize": 18, "anchorTo": "n1", "halo": true },
      { "kind": "connector", "id": "n3", "pts": [x1,y1, xm,ym, x2,y2], "head": "arrow", "tail": "none",
        "dashed": false, "from": "n1", "to": "n4" },
      { "kind": "rect" }, { "kind": "ellipse" }
    ]
  }
}
```

- `x`, `y` de los iconos son el **centro**; de rectángulos y textos, la esquina superior izquierda.
- `anchorTo`: la etiqueta acompaña al icono. `labelOf`: la etiqueta acompaña a una flecha. `from`/`to`: la flecha queda pegada a esos iconos.
- `pdb`: configuración del visor 3D (código, cadenas, colores, vista) para poder reorientar. `realW`: ancho real en Å.

## Agregar una fuente de iconos

1. Descargarla en `vendor_src/` y agregarla a `LIBRARIES` en `instalar.py`, con el commit fijado.
2. Montar su carpeta en `server.py`, como se hace con `/fluent`.
3. En `build_index.py`, agregar entradas al índice con: `id`, `name`, `src`, `category`, `groups`, `author`, `license`, `source` y `aspect`.
4. Si es monocroma, sumar su `source` a la lista del tinte de color plano (`TintFilter` en `app.js`).

`groups` decide en qué filtros aparece: `ecologia`, `molecular`, `celular`, `laboratorio`, `agricultura`, `membranas`, `graficos`, `satelite`, `mis`.

## Variables de entorno (`.env`)

| Variable | Uso |
|---|---|
| `AI_PROVIDER` | `gemini` o `deepseek` (se elige desde la app) |
| `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_BASE_URL` | Gemini (si falta el modelo, se elige el Flash estable más nuevo) |
| `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, `DEEPSEEK_BASE_URL` | DeepSeek o cualquier API compatible con OpenAI |
| `BIOFIG_PORT` | Puerto (por defecto 8765) |
| `BIOFIG_ENV` | Ruta alternativa del archivo `.env` (útil para pruebas) |
| `U2NET_HOME` | Carpeta de los modelos de rembg (por defecto `~/.u2net`) |
