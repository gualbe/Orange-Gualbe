# Registro de cambios de Orange-Gualbe

Cambios sobre Orange oficial. Cada entrada indica qué cambia, por qué y el
efecto medido (benchmark, filas, antes → después). Tiempos medidos con
`gualbe/bench/large_data.py` y `gualbe/bench/widgets.py` en un Apple M4 Max;
los resultados están en `gualbe/bench/results/`.

## Sin publicar

Base: upstream master `bd6fef4ca` (3.41.0.dev, posterior a 3.40.0).

### Rendimiento

- **Escritura de .tab/.csv.** Los valores se formatean por columnas (los
  números en Cython con `PyOS_double_to_string`, los categóricos por
  indexación) en bloques de 10.000 filas. El fichero es idéntico byte a byte
  y la memoria máxima se queda en ~45 MB sea cual sea el tamaño.
  1M filas × 52 columnas: `tab_write` 25,3 s → 7,7 s (3,3×),
  `csv_write` 25,6 s → 7,4 s (3,5×).
- **Lectura de .tab/.csv.** Las columnas numéricas se convierten, se
  detectan sus ausentes y se cuentan sus decimales en una sola pasada en
  Cython (`Orange/data/_columns.pyx`), con la misma semántica que antes; el
  recolector de basura se pausa mientras se crean las filas; y se prueba
  UTF-8 antes que ASCII, así que los ficheros UTF-8 con tildes o eñes ya no
  se leen dos veces.
  1M filas: `tab_read` 21,0 s → 10,9 s (1,9×); fichero UTF-8 de 500k filas
  con un solo carácter no ASCII 7,1 s → 4,0 s.
- **Contingencias de variables numéricas** (Box Plot, Distributions, Naive
  Bayes, Rank…). Se ordenan los valores de cada clase por separado y se
  mezclan en una pasada lineal, en vez de ordenar indirectamente toda la
  columna. Resultados idénticos. 1M filas: `contingencies` 9,4 s → 3,0 s
  (3,1×).
- **Conversión de tablas por bloques adaptados a su anchura.**
  `Table.transform` convertía siempre bloques de 5000 filas; con
  transformaciones encadenadas (PCA, modelos, preprocesado) el coste fijo
  por bloque dominaba. Ahora cada bloque tiene unos 2,5 M de valores (entre
  5000 y 100.000 filas), con la memoria intermedia igual de acotada en
  tablas anchas. 1M filas, widgets: PCA 8,5 s → 3,4 s (2,5×), Impute
  0,54 → 0,26 s, Continuize 0,43 → 0,20 s, Preprocess 2,3 → 1,2 s,
  Predictions 2,2 → 1,4 s, Discretize 2,8 → 2,2 s.

### Correcciones

- **kNN con distancia de Mahalanobis** guardaba la covarianza del primer
  ajuste en el learner: en validación cruzada todas las particiones usaban
  la de la primera y, con otros datos, las predicciones eran erróneas
  ([#7311](https://github.com/biolab/orange3/issues/7311)). Además, con
  scikit-learn 1.9 fallaba al predecir con zoo o heart_disease (pedía `VI`).
- **`Table.add_column`/`set_column` con datos dispersos** perdía los valores:
  la columna nueva quedaba toda `NaN`, p. ej. en Aggregate Columns
  ([#6748](https://github.com/biolab/orange3/issues/6748)).
- **Group By con fechas discretizadas** fallaba al comparar discretizadores
  ([#7065](https://github.com/biolab/orange3/issues/7065)).
- **Datasets** cerraba Orange (SIGSEGV) al cambiar de dataset durante una
  descarga ([#7343](https://github.com/biolab/orange3/issues/7343)).
- **Merge Data** fallaba al concatenar tablas con columnas de PCA
  ([#7132](https://github.com/biolab/orange3/issues/7132)).
- **Excel sin clase** con cabecera de tres líneas se leía mal
  ([#7276](https://github.com/biolab/orange3/issues/7276)).
- **Predictions** fallaba al pasar de una clase discreta a una continua o
  sin clase, y su informe fallaba sin modelos
  ([#6672](https://github.com/biolab/orange3/issues/6672)).
- **Nomogram** mostraba probabilidades erróneas en vistas estrechas o con
  nombres de atributos largos: la regla tiene ahora un ancho mínimo.
- Los modelos entrenados con clases desconocidas guardaban un índice de
  clase basura (`used_vals`).
- Contingencias con datos dispersos, pesos y más de una columna numérica:
  fallaban con `IndexError` o usaban pesos erróneos.

### Compatibilidad

- **scikit-learn 1.10 y 1.11.** Regresión logística y MDS habrían dejado de
  funcionar con scikit-learn 1.10, y Gradient Boosting con 1.11. Sus
  parámetros obsoletos se traducen a los nuevos detectándolos por la firma
  del estimador (`Orange/misc/_skl_compat.py`), con resultados idénticos.
  De paso, la regresión logística con 1M filas pasa de 2,3 s a 1,7 s.
  Pendiente: `probability` de SVM (se elimina en 1.11), porque la
  alternativa cambia ligeramente las probabilidades.

### Tests

- La suite pasa sin fallos en macOS sin ventana (`offscreen`): los tests de
  StickyGraphicsView se omiten ahí, porque la geometría de las barras de
  desplazamiento difiere de la plataforma nativa.

### Herramientas

- Benchmarks de núcleo y de widgets (`gualbe/bench/`), script de
  sincronización con la versión oficial (`gualbe/sync_upstream.sh`) e
  informe de diagnóstico de la Fase 1 (`gualbe/reports/`).
