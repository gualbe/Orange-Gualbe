# Integración de Orange 3.41.0 oficial (3.41.0+gualbe.2)

Fecha: 23 de noviembre de 2026. Plan seguido:
[`gualbe/plans/fusion-3.41.0+gualbe.2.md`](../plans/fusion-3.41.0+gualbe.2.md).

## Versión oficial integrada

- **Orange 3.41.0**: etiqueta `3.41.0` (`46443558d`), publicada el 8 de
  noviembre de 2026. Son 60 commits que no estaban en 3.41.0+gualbe.1, cuya
  base era upstream master `71c3613e0`, del 20 de octubre.
- **Novedades principales de sus notas:**
  - Python 3.15.
  - Traducción al castellano.
  - Silhouette Plot muestra la silueta media.
  - kNN con distancia del coseno, y métricas de Neighbors unificadas con
    Distances.
  - Opciones de vista en Distributions.
  - Scatter Plot: reposicionar puntos a mano y agrupar regiones densas
    (desactivado por defecto).
  - Rutas relativas al workflow en CSV Import.
  - Los ficheros recientes se guardan en QSettings (File, Load Model,
    Distance File).
  - Compatibilidad con numpy 2.4 y pandas 3, que dejan de tener tope.
  - Unas 40 correcciones. Entre ellas, tres que Orange-Gualbe ya traía:
    softmax en Nomogram (#7331), el segfault de Datasets (#7345 / gh-7343) y
    la fila de indicadores vacía en Excel (#7334 / gh-7276).

## Conflictos y cómo se resolvieron

| Fichero | Resolución |
|---|---|
| `requirements-core.txt`, `conda-recipe/meta.yaml` | Se mantiene `scikit-learn<1.11`; la oficial pone `<1.10`. `Orange/misc/_skl_compat.py` ya traduce los parámetros de regresión logística y MDS que cambian en la 1.10. El resto de la receta de conda queda como en la oficial (`tzdata`, xgboost sin tope, `python.app`). |
| `Orange/data/io.py` | Se adopta la solución oficial de gh-7276: `dropwhile` y que `data_table` descarte las filas vacías. Se elimina `_skip_empty_rows` y la importación de `_RE_TYPES`. Pasan los tests de las dos ramas (`test_xlsx_empty_flags.py` y los nuevos de `test_xlsx_reader.py`). |
| `Orange/widgets/data/owdatasets.py` | El código es el mismo; se conserva el comentario sobre gh-7343. |
| `Orange/widgets/visualize/tests/test_ownomogram.py` | Versión oficial: sin los `w.show()` innecesarios y con `test_hidden_probability_ticks_not_in_scene`. Pasa 3 de 3 veces sin ventana (`offscreen`). |
| `setup.py` (sin conflicto) | `ISRELEASED` vuelve a `False` en la rama de desarrollo. |

`ownomogram.py` se fusionó sin conflicto. Ahora solo difiere del oficial en
el ancho mínimo de la regla, que es propio de Orange-Gualbe.

## Correcciones hechas durante la integración

1. **CSV Import con pandas 3** (`e97a0a046`). El parche propio de gh-6499
   comprobaba `dtype == "object"` para decidir si convertir a UTC. Con
   pandas 3, el texto es `str`, así que una columna de fechas con zonas
   horarias mezcladas se quedaba como texto (`test_tz_local`). Ahora se
   comprueba si el resultado es de tipo fecha. Con pandas 2 no cambia nada.
2. **`table_from_frame` y categóricas de texto** (`5b072d0f6`). Es un efecto
   de un cambio de Orange 3.41.0. Para admitir el `str` de pandas 3 se usa
   `is_string_dtype`, que también es cierto para las categóricas con
   categorías de texto. Cada columna categórica se intentaba interpretar
   entera como fechas con `dateutil`. Además, una categórica cuyas
   categorías parecen fechas pasaba a `TimeVariable`. Se excluyen las
   categóricas, como antes. Test nuevo:
   `test_table_from_frame_categorical_of_dates_is_discrete`. Con 1M filas,
   `from_pandas` pasa de 0,50 s a 0,34 s, igual que en gualbe.1. Este fallo
   también está en Orange oficial y convendría comunicarlo allí. No lo he
   hecho: queda a decisión del usuario.

## Tests

| Entorno | Resultado |
|---|---|
| Referencia: Python 3.12, numpy 2.3.5, pandas 2.3.3, scikit-learn 1.9.1, orange-widget-base 4.29.0 | 6105 tests, **0 fallos** (755 omitidos) |
| numpy 2.5.5, pandas 3.1.1, scipy 1.18.1, scikit-learn 1.9.1 (conda-forge, temporal) | 6105 tests, **0 fallos** (756 omitidos) |

- La primera ejecución dio 7 fallos en File, Load Model y los workflows de
  ejemplo, porque el entorno tenía `orange-widget-base` 4.28.0 y la 3.41.0
  exige 4.29.0 (ficheros recientes en QSettings). Se actualizó el entorno
  `orange-gualbe` a la 4.29.0 y desaparecieron.
- En el entorno de numpy 2.5, otros dos fallos (`test_get_entry_point`,
  `test_scheme_examples`) eran del propio entorno, por no tener Orange
  instalado como paquete. Con `pip install -e` pasan.
- **scikit-learn 1.10:** no verificable aún. No está publicada; la última en
  PyPI es la 1.9.1.

## Benchmarks (1M filas, Apple M4 Max)

### Núcleo: `fase2c-1M.json` → `sync-3.41.0-1M.json`

Todas las operaciones quedan dentro del ±15 % salvo dos:

| Operación | fase2c | Tras la fusión | Cambio |
|---|---:|---:|---:|
| `knn_predict_20k` | 0,43 s | 0,10 s | 4,4× más rápido |
| `kmeans_k5` | 16,7 s | 22,0 s | 0,76× (no lo causa la fusión; ver abajo) |
| `from_pandas` | 0,34 s | 0,36 s | 0,96× (era 0,50 s antes de la corrección 2) |

- `kmeans_k5`: la diferencia con `fase2c` no viene de la fusión. Midiendo
  `gualbe` sin fusionar y la fusión en las mismas condiciones (3 veces cada
  una) salen 20,1–20,8 s y 20,2–20,3 s. `fase2c` es anterior a los últimos
  cambios de gualbe.1.
- `knn_predict_20k`: unas 4× más rápido, por los cambios oficiales en kNN y
  sus métricas (#7309, #7320).

### Widgets: `fase2d-widgets-1M.json` → `sync-3.41.0-widgets-1M.json`

Ningún widget cambia más de un 15 %, salvo Pivot, que es un 16 % más
rápido. Test & Score: 59,5 → 61,8 s (−4 %, dentro del ruido).

## Decisiones sobre dependencias

- **scikit-learn:** se mantiene `>=1.5.1,<1.11`.
- **numpy y pandas:** se aceptan sin tope, como en la versión oficial, tras
  pasar la suite completa con numpy 2.5.5 y pandas 3.1.1. Los instaladores
  siguen con numpy 2.3.5 y pandas 2.3.3, fijados en
  `Orange-Gualbe-installers`.
- **orange-widget-base:** `>=4.29.0`, como en la versión oficial.

## Pendiente (no bloqueante)

- Las cadenas propias de Orange-Gualbe (p. ej. «Silhouette score») no están
  en la nueva traducción al castellano (`i18n/es/msgs.jaml`).
- Comunicar a Orange oficial el problema de las categóricas de texto en
  `table_from_frame` (corrección 2).
- Probar con scikit-learn 1.10 cuando se publique.

## Recomendación

Integrar. Tests a 0 fallos en los dos entornos y sin regresiones de
rendimiento atribuibles a la fusión.
