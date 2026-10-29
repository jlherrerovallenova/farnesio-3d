# Lubens Farnesio · edificio 3D interactivo

Web de la promoción **Farnesio** (80 viviendas, Valladolid): edificio 3D con disponibilidad, ficha de cada vivienda con plano comercial e interactivo, simulación de sol, comparador, asistente de búsqueda y cuota de hipoteca orientativa.

Publicada en **https://lubens-farnesio.netlify.app**

## Contenido

| Archivo | Qué es |
|---|---|
| `index.html` | La aplicación completa (HTML + CSS + JavaScript, usa three.js desde CDN) |
| `data.json` | Geometría del edificio extraída del DXF de proyecto + datos públicos de las viviendas (estado, precio, superficies) |
| `plano-*.png` | Planos comerciales, uno por tipología (`1A-C`, `1B-AtD`…) |
| `r1.jpg` … `r5.jpg` | Renders del proyecto (galería) |
| `logo-lubens-farnesio.png` | Logo |
| `netlify.toml` | Configuración de Netlify (sitio estático, sin build) |
| `tools/` | Scripts Python usados para extraer la geometría del DXF y los planos (referencia; necesitan los archivos originales) |

`data.json` **no contiene datos personales**: ni compradores, ni teléfonos, ni comisiones. Solo estado, precio y superficies.

## Cambiar la disponibilidad o los precios

Los estados y precios están en `data.json`, dentro de `units` (un objeto por vivienda):

```json
{"id":"1B-4D", "estado":"LIBRE", "precio":280000, ...}
```

`estado` admite `LIBRE`, `RESERVADA`, `VENDIDA` o `BLOQUEADA`. Tras editar, sube el cambio a GitHub y vuelve a desplegar en Netlify.

## Probar en local

Cualquier servidor estático sirve, por ejemplo:

```bash
python3 -m http.server 8000
# y abrir http://localhost:8000
```

(Abrir `index.html` con doble clic no funciona porque el navegador bloquea la carga de `data.json` desde disco.)
