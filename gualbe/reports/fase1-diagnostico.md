# Orange-Gualbe · Fase 1: diagnóstico

Fecha: 19 de octubre de 2026 · Base: `gualbe` (upstream master `bd6fef4ca` +
mejoras de E/S y contingencias ya integradas).

Equipo de medida: Apple M4 Max (16 núcleos), Python 3.12, numpy 2.3.5,
scikit-learn 1.9.1. Datos sintéticos de 1M filas × 50 atributos (40 numéricos,
10 categóricos, 2 % de valores ausentes), clase binaria y un meta de texto.
Herramientas: `gualbe/bench/large_data.py` (núcleo) y `gualbe/bench/widgets.py`
(widgets, del envío de datos a la salida lista). Resultados en
`gualbe/bench/results/`.

## 1. Resumen

- **Rendimiento.** Hay 8 mejoras con resultados idénticos y buena relación
  esfuerzo/beneficio. Las tres primeras atacan lo más lento de un workflow
  típico: el árbol de clasificación (domina Test & Score, 87 s), el tamaño de
  bloque de las transformaciones (PCA 2,6×, Predictions 1,7× con un cambio de
  una línea) y Correlations (10,5 s).
- **Robustez.** El riesgo más urgente es externo: scikit-learn 1.10 eliminará
  parámetros que Orange usa en regresión logística, SVM, Gradient Boosting y
  MDS; esos modelos fallarán al actualizar.
- **Bugs.** De 106 issues abiertos, 29 son bugs reales (10 dan resultados
  erróneos sin aviso); 27 reproducidos aquí. Hay 7 con arreglo de pocas líneas
  que conviene hacer ya. Los 5 fallos de nuestra suite de tests son
  artefactos de macOS, no errores de Orange.

## 2. Rendimiento

### 2.1 Mediciones (1M filas)

| Widget / operación | Tiempo | Dónde se va el tiempo |
|---|---:|---|
| Test & Score (NB + LogReg + árbol, CV 5) | 87,2 s | ~70 % en el árbol de Orange: `argsort` de cada atributo en cada nodo (`Orange/classification/tree.py:143`) |
| k-Means (k=5, 10 reinicios) | 17,4 s | scikit-learn (96 %); se deja como está (decidido) |
| Validación cruzada Naive Bayes | 13,9 s | discretización en cada partición + conversión por bloques de 5000 filas |
| Lectura `.tab` | 10,9 s | parseo CSV en C + construcción de columnas (ya 1,9× más rápida) |
| Correlations | 10,5 s | `scipy.stats.pearsonr` par a par (780 pares) en Python; con datos grandes usa una heurística que no calcula todos los pares |
| PCA | 8,5 s | ~60 % en crear ~14.000 tablas intermedias por convertir en bloques de 5000 filas con transformaciones anidadas |
| Escritura `.tab` / `.csv` | 7,7 / 7,4 s | ya 3,3–3,5× más rápida |
| Rank | 6,5 s | discretización por bloques + ordenaciones para cada puntuador |
| Feature Statistics | 4,6 s | moda de columnas numéricas con `scipy.stats.mode` (ordena cada columna) |
| Merge Data | 3,5 s | emparejamiento de claves de texto con diccionarios y tuplas en Python |
| Contingencias | 3,0 s | ya 3,1× más rápidas |
| Discretize | 2,8 s | `np.sort` por columna (límite práctico) |
| Unique | 2,7 s | tuplas por fila en Python (`owunique.py:86`) |
| Preprocess (imputar + continuizar + normalizar) | 2,3 s | conversión por bloques de 5000 filas |
| Predictions | 2,2 s | conversión por bloques de 5000 filas |
| Scatter Plot | 1,1 s | — |
| Resto (Group By, Impute, Continuize, Data Table, Feature Constructor, Distributions, Pivot, Data Sampler, Concatenate, Box Plot) | < 0,8 s cada uno | sin problema |

### 2.2 Mejoras propuestas (por prioridad)

Todas mantienen resultados idénticos salvo donde se indica.

| # | Mejora | Afecta a | Ganancia estimada | Esfuerzo | Riesgo |
|---|---|---|---|---|---|
| P1 | Bloques de conversión de 5000 a ~50.000 filas (`Table._FromTableConversion.max_rows_at_once`) | PCA, Predictions, Preprocess, Rank, Naive Bayes, cualquier modelo aplicado a datos nuevos | PCA 2,6×, Predictions 1,7×, NB ~1,2× (medido) | S (1 línea + tests) | Bajo: más memoria por bloque (~40 MB) |
| P2 | Árbol de Orange: ordenar cada atributo una vez en la raíz y filtrar el orden en los hijos | Tree, Test & Score, Random Forest de Orange no (usa sklearn) | 3–5× en el árbol; Test & Score ~2× | M | Medio: tocar el núcleo del árbol; árbol idéntico verificable |
| P3 | Correlations vectorizado (Pearson con productos de matrices; Spearman con rangos) | Correlations | 10× o más; además calcula todos los pares sin heurística | M | Bajo; diferencias solo de redondeo (1e-12) |
| P4 | Feature Statistics: moda de numéricas sin ordenar columnas completas | Feature Statistics | ~3× | S | Bajo |
| P5 | Unique con `np.unique`/pandas sobre filas | Unique | ~5× | S | Bajo |
| P6 | Merge Data: emparejar claves con pandas/numpy | Merge Data | ~3× | M | Medio (muchos casos: claves múltiples, duplicados, tipos) |
| P7 | Rank: reutilizar la discretización entre puntuadores | Rank | ~2× | M | Bajo |
| P8 | Discretización con `searchsorted` en vez de ordenar todo | Discretize, Naive Bayes, Rank | ~1,3× | S | Bajo |

Descartadas: k-means (decidido), regresión logística y Random Forest (tiempo
en scikit-learn), segunda vuelta a la lectura `.tab` (lo que queda exige
reescribir el lector).

## 3. Bugs

Revisión de los 106 issues abiertos de biolab/orange3 (19-oct-2026) contra la
rama `gualbe`. Informe completo, con causa, tamaño y riesgo de cada bug, en
[`fase1-bugs/triage.md`](fase1-bugs/triage.md); scripts de reproducción en
`fase1-bugs/repro/`.

| Categoría | Nº |
|---|---:|
| Bugs | 29 (S1: 10 · S2: 6 · S3: 12 · S4: 1) |
| Bugs menores (interfaz) | 9 |
| Peticiones de funcionalidad | 55 |
| Preguntas / otros | 13 |

S1 = resultados erróneos sin aviso · S2 = error en un flujo normal ·
S3 = error raro o interfaz engañosa · S4 = cosmético.
Reproducidos 27 de 29 (#7268 no se reproduce; #6427 necesita una base de
datos SQL).

### 3.1 Bugs que dan resultados erróneos o rompen flujos (S1 y S2)

| Issue | Problema | Sev. | Tamaño |
|---|---|---|---|
| [#7311](https://github.com/biolab/orange3/issues/7311) | kNN con distancia de Mahalanobis guarda la covarianza en el learner: en validación cruzada todas las particiones usan la de la primera. Además falla al predecir con scikit-learn 1.9 (verificado con zoo y heart_disease) | S1 | S |
| [#6748](https://github.com/biolab/orange3/issues/6748) | `Table.add_column` con datos dispersos: la columna nueva queda toda `NaN` (verificado) | S1 | S |
| [#6067](https://github.com/biolab/orange3/issues/6067) | Lectura `.tab`/`.csv`: un apóstrofo se toma como comilla y se pierden filas sin aviso | S1 | S |
| [#6916](https://github.com/biolab/orange3/issues/6916) | Al guardar, los números sin decimales fijados se escriben con 6 cifras (`%g`): pérdida de precisión en el fichero | S1 | S |
| [#6203](https://github.com/biolab/orange3/issues/6203) | Enteros de más de 15–16 cifras (identificadores) pierden precisión al leerlos | S1 | S–M |
| [#7326](https://github.com/biolab/orange3/issues/7326) | Nomograma: probabilidades erróneas con regresión logística multiclase (hay PR upstream #7331) | S1 | M |
| [#7020](https://github.com/biolab/orange3/issues/7020) | Select Columns puede adoptar la selección guardada de otra instancia del widget | S1 | S |
| [#6047](https://github.com/biolab/orange3/issues/6047) | DBSCAN: el `eps` guardado se sobrescribe al reabrir el workflow | S1 | S–M |
| [#6499](https://github.com/biolab/orange3/issues/6499) | CSV Import interpreta fechas dd/mm de forma inconsistente fila a fila | S1 | M |
| [#7280](https://github.com/biolab/orange3/issues/7280) | La "silueta" que añade k-Means es `arctan(s)/π + 0,5`, no la silueta | S1 | S (cambia salidas) |
| [#7343](https://github.com/biolab/orange3/issues/7343) | Datasets: cierre de Orange (SIGSEGV) al cambiar de dataset mientras descarga | S2 | S (1 línea) |
| [#7065](https://github.com/biolab/orange3/issues/7065) | Group By falla con fechas discretizadas (`Discretizer.__eq__`) | S2 | S (1 línea) |
| [#7132](https://github.com/biolab/orange3/issues/7132) | Merge Data falla con PCA + Concatenate | S2 | S |
| [#7276](https://github.com/biolab/orange3/issues/7276) | Excel sin clase y con cabecera de 3 líneas se lee mal | S2 | S |
| [#6672](https://github.com/biolab/orange3/issues/6672) | Predictions falla tras cambiar de clase discreta a continua | S2 | S |
| [#5700](https://github.com/biolab/orange3/issues/5700) | Venn Diagram falla con datos dispersos | S2 | S–M |

### 3.2 Los 5 fallos locales de la suite de tests

No son errores de Orange ni de nuestros cambios: fallan igual en la versión
oficial y pasan los 35 tests afectados con la plataforma Qt nativa (`cocoa`).
Son artefactos de ejecutar sin ventana (`offscreen`) en macOS: fuentes más
anchas (Nomogram) y barras de desplazamiento que ocupan sitio con el estilo
Fusion (StickyGraphicsView). Se puede dejar la suite limpia omitiendo esos
tests en macOS + offscreen o ensanchando el widget en el test.

## 4. Calidad y compatibilidad

Suite completa: 5.997 tests, 5 fallos conocidos (artefactos de macOS, ver 3.2), 710 omitidos.

| # | Problema | Dónde | Gravedad | Propuesta |
|---|---|---|---|---|
| Q1 | scikit-learn 1.10 eliminará `penalty` y `n_jobs` en `LogisticRegression` (302 avisos) | `Orange/classification/logistic_regression.py` | Alta: fallará al actualizar | Usar `l1_ratio`/`C` según la versión instalada |
| Q2 | `probability` de `SVC` obsoleto (85 avisos) | `Orange/classification/svm.py` | Alta | `CalibratedClassifierCV` o comprobar versión |
| Q3 | `criterion` de Gradient Boosting obsoleto (134 avisos) | `Orange/classification/gb.py`, `Orange/regression/gb.py` | Media | Dejar de pasarlo |
| Q4 | MDS: `metric`, `dissimilarity` e `init` cambian (59 avisos) | `owmanifoldlearning.py:309`, `Orange/projection/manifold.py` | Media | Nuevos nombres de parámetros |
| Q5 | Clase con valores desconocidos: `NaN` convertido a entero en `used_vals` | `Orange/base.py:152` | Media (valor basura silencioso) | Excluir `NaN` antes de convertir |
| Q6 | APIs obsoletas de orange-widget-base (`ListViewSearch`, `RecentPathsWidgetMixin`, `callbackOnReturn`) y widgets de modelos sin `@gui.deferred` | varios widgets | Baja | Modernizar cuando se toquen |
| Q7 | Conversión a entero con `NaN` antes de enmascarar (avisos) | `Orange/preprocess/transformation.py:248` | Baja (resultado correcto) | Enmascarar antes de convertir |

## 5. Plan propuesto para la Fase 2

En bloques cortos; cada cambio con su test, la suite completa y el benchmark
antes y después, como en la primera tanda.

1. **Bloque A: rápido y de bajo riesgo.**
   P1 (bloques de conversión), Q1–Q4 (compatibilidad con scikit-learn 1.10),
   Q5, bugs de una línea o pocas líneas: #7311 (+ fallo con Mahalanobis),
   #6748, #7065, #7343, #7132, #7276, #6672; y dejar la suite de macOS sin
   fallos (3.2).
2. **Bloque B: lectura y escritura de ficheros** (área ya conocida):
   #6067, #6916 y #6203.
3. **Bloque C: rendimiento con más trabajo:** P2 (árbol), P3 (Correlations),
   P4 (Feature Statistics), P5 (Unique).
4. **Bloque D: resto:** #7326 (integrar la PR #7331), #7020, #6047, #6499,
   #5700; P6 (Merge Data), P7 (Rank), P8 (discretización).

**Estado (19-oct-2026):** bloques A, B, C y D hechos (ver
`gualbe/CHANGELOG.md`). Descartadas por no compensar: P5 (Unique: agrupar
con pandas no es más rápido que el diccionario actual) y P8 (la
discretización por frecuencias necesita la distribución ordenada completa
para dar los mismos cortes). Decidido (19-20 oct): #6916 se aplica escribiendo
todas las cifras; #7280 añade la columna "Silhouette score" sin tocar la
actual; SVM se limita a scikit-learn<1.11 hasta migrar con la 1.11.

**Decisiones que necesitan tu visto bueno**, porque cambian salidas
existentes:

- **#6916.** Escribir los números con todas sus cifras (formato exacto más
  corto) en vez de 6 cifras. Los ficheros guardados cambiarían, pero sin
  perder información.
- **#7280.** Que k-Means añada la silueta real (de −1 a 1) en lugar de la
  transformación actual (de 0 a 1). Cambia el significado de la columna para
  workflows que ya la usan.
