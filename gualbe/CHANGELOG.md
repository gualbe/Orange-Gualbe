# Registro de cambios de Orange-Gualbe

Cambios sobre Orange oficial. Cada entrada indica qué cambia, por qué y el
efecto medido (benchmark, filas, antes → después). Tiempos medidos con
`gualbe/bench/large_data.py` y `gualbe/bench/widgets.py` en un Apple M4 Max;
los resultados están en `gualbe/bench/results/`.

## 3.41.0+gualbe.1 (20 de octubre de 2026)

Base: upstream master `71c3613e0` (desarrollo de 3.41.0, posterior a la
versión oficial 3.40.0). Suite completa: 6098 tests sin fallos en macOS
(Apple M4 Max, Python 3.12, scikit-learn 1.9.1, numpy 2.3.5).

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

- **Árbol de clasificación de Orange** (widget Tree, Test & Score). Cada
  atributo numérico se ordena una sola vez en la raíz y el orden se reparte
  entre los hijos, en vez de reordenar en cada nodo. Árbol idéntico.
  Validación cruzada (5) con 200k filas: 10,4 s → 5,9 s. El árbol de
  regresión no cambia, porque allí el orden entre empates podría alterar
  los últimos bits de las sumas.
- **Correlations.** Todos los pares a la vez con productos de matrices, en
  lugar de `pearsonr`/`spearmanr` par a par; misma tabla de resultados
  (diferencias de redondeo < 1e-13) y sin la heurística de k-means hasta
  1000 atributos. 1M filas × 40 atributos: 10,5 s → 1,9 s.
- **Moda (`nanmode`, Feature Statistics).** Por columnas, con `bincount`
  para valores categóricos y ordenando copias contiguas para el resto, con
  la misma semántica que scipy. Feature Statistics con 1M filas:
  4,1 s → 2,4 s.

- **Merge Data.** Para elegir columnas de emparejamiento contaba los valores
  comunes ordenando todas las cadenas (`np.intersect1d`); ahora usa
  conjuntos. 1M filas: 3,1 s → 1,2 s.
- **Rank.** Information Gain, Gain Ratio y Gini comparten discretización y
  cada uno la repetía; ahora se hace una vez. Puntuaciones idénticas.
  200k filas, 7 métodos: 2,6 s → 1,4 s.

### Correcciones

- **Silueta en k-Means.** La columna "Silhouette" que añade k-Means es
  `arctan(s)/π + 0,5` (entre 0,25 y 0,75), no la silueta: no coincidía con
  Silhouette Plot y un punto mal asignado aparecía como ~0,49
  ([#7280](https://github.com/biolab/orange3/issues/7280)). Se mantiene esa
  columna, para no alterar workflows existentes, y se añade
  **"Silhouette score"** con la silueta real (de −1 a 1), también como media
  por cluster en los centroides.
- **Nomogram con regresión logística multiclase** mostraba probabilidades
  erróneas (sigmoide por clase en vez de softmax): en iris[53], 15/92/34 %
  frente a 2/94/5 % del modelo
  ([#7326](https://github.com/biolab/orange3/issues/7326)). Se integra la
  PR upstream #7331 (aún sin fusionar allí), verificada aquí con 40
  instancias, varias configuraciones y arrastrando marcadores.
- **Select Columns** podía adoptar en silencio la selección de otro Select
  Columns del workflow cuando a los datos les faltaba una columna
  ([#7020](https://github.com/biolab/orange3/issues/7020)); ahora prefiere
  su propio contexto.
- **DBSCAN** sustituía el `eps` elegido por el usuario al recibir datos o
  al abrir el workflow, y no permitía valores fuera de la gráfica
  ([#6047](https://github.com/biolab/orange3/issues/6047)). En workflows
  guardados antes basta con fijarlo una vez.
- **CSV Import** leía fechas de una misma columna unas como mes/día y otras
  como día/mes ([#6499](https://github.com/biolab/orange3/issues/6499));
  ahora usa un solo formato por columna.
- **Venn Diagram** fallaba con datos dispersos
  ([#5700](https://github.com/biolab/orange3/issues/5700)).

- **Guardar sin perder cifras.** Las variables numéricas sin decimales
  fijados (CSV Import, datos creados desde numpy) se escribían con `%g`, es
  decir, con 6 cifras: -22112215 se guardaba como -2.21122e+07
  ([#6916](https://github.com/biolab/orange3/issues/6916)). Ahora se escribe
  la representación exacta más corta; las variables con decimales fijados
  mantienen su formato (p. ej. `0.500`) mientras sea exacto. La ida y vuelta
  es exacta en .tab, .csv y Excel. Coste: los números de precisión completa
  ocupan unas 17 cifras, así que con datos aleatorios de 1M filas la
  escritura pasa de 7,2 s a ~15,7 s y la lectura de 10,9 s a ~15 s; con
  datos de 3 decimales no cambia (7,0 s).
- **Apóstrofos al leer .tab/.csv.** Un apóstrofo se tomaba como comilla y
  uno sin cerrar se tragaba filas sin aviso
  ([#6067](https://github.com/biolab/orange3/issues/6067)).
- **Enteros largos (identificadores).** Los enteros de más de 2^53 se leían
  como números y perdían cifras; sin tipo declarado, ahora se leen como
  texto en .tab/.csv, `table_from_frame` y CSV Import
  ([#6203](https://github.com/biolab/orange3/issues/6203)).
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
  SVM: scikit-learn 1.11 elimina `probability=True`, y la alternativa
  (calibrar aparte) cambiaría ligeramente las probabilidades (no las
  clases). Por ahora se limita a `scikit-learn<1.11` en
  `requirements-core.txt` y en la receta de conda, sin cambiar resultados;
  se migrará cuando se anuncie la 1.11, idealmente alineado con Orange
  oficial.

### Tests

- La suite pasa sin fallos en macOS sin ventana (`offscreen`): los tests de
  StickyGraphicsView se omiten ahí, porque la geometría de las barras de
  desplazamiento difiere de la plataforma nativa.

### Herramientas

- Benchmarks de núcleo y de widgets (`gualbe/bench/`), script de
  sincronización con la versión oficial (`gualbe/sync_upstream.sh`) e
  informe de diagnóstico de la Fase 1 (`gualbe/reports/`).
