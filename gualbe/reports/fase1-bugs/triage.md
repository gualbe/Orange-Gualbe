# Triaje de issues abiertos de Orange3 para Orange-Gualbe

- **Fecha:** 2026-10-19.
- **Código analizado:** rama `gualbe` (4021b62f5) = upstream master bd6fef4ca + parches de rendimiento de E/S `.tab/.csv` y de contingencias.
- **Entorno:** Python 3.12.15, PyQt5 5.15.11 / Qt 5.15.15, pyqtgraph 0.14.0, scikit-learn 1.9.1, numpy 2.3.5, pandas 2.3.3. Los widgets se ejecutaron con `QT_QPA_PLATFORM=offscreen`, salvo donde se indica.
- **Material:** los scripts de reproducción están en `repro/{groupA,groupB,groupC,tests_local}/` (junto a este informe). No se ha modificado el repositorio ni se ha escrito nada en GitHub.

## 1. Resumen

**Issues abiertos:** 106 (`gh issue list --state open`, 19-oct-2026).

| Categoría | Nº |
|---|---|
| Bug (resultado erróneo / crash / cuelgue / pérdida de datos) | 29 |
| Bug menor (UI, cosmético) | 9 |
| Petición de funcionalidad | 55 |
| Pregunta / otro (instalación, add-ons, entorno, discusión, docs) | 13 |

**Severidad de los 29 bugs**

| Severidad | Nº | Issues |
|---|---|---|
| S1: resultados erróneos en silencio | 10 | 7326, 7311, 6748, 6067, 6916, 7280, 7020, 6203, 6047, 6499 |
| S2: crash/excepción en flujo normal | 6 | 7343, 7132, 7065, 6672, 7276, 5700 |
| S3: crash raro o UI engañosa | 12 | 7308, 7344, 5914, 5485, 5632, 5961, 6427, 6808, 6431, 6105, 6721, 7268 |
| S4: cosmético | 1 | 6367 (resto pendiente) |

**Reproducción**

- **Reproducidos:** 27 de 29.
  - En #6367 y #5485 la mayor parte ya está corregida en el código actual; solo se reproduce un resto.
  - #6431 se reprodujo con un gestor de credenciales falso, sin llavero real.
- **No reproducido:** #7268.
- **No probado:** #6427 (sin base de datos; solo lectura de código).
- Los 9 bugs menores no se han intentado reproducir.

**PR abiertas upstream que arreglan bugs de esta lista** (ninguna fusionada): #7331 (→ #7326), #7345 (→ #7343), #7336 (→ #7308) y #6740, en borrador (→ #6721).

**Hallazgos sin issue abierta**

1. **kNN con `metric="mahalanobis"` falla siempre** cuando sklearn 1.9.1 elige el algoritmo *brute*: `ValueError: The 'VI' parameter is required…`. Le pasamos `V`, no `VI` (`Orange/base.py:656-658`). Pasa, por ejemplo, con zoo y heart_disease. **S2.**
2. **El nomograma calcula la probabilidad a partir de posiciones en píxeles recortadas.** Con un viewport estrecho o etiquetas largas muestra probabilidades erróneas (ver §4.1). **S4**: en uso real el widget visible tiene viewport ≥ 480 px.
3. **`Orange/data/sql/table.py:590`:** `_sample` lanza `NotImplementedError` si el nombre de la tabla contiene ",", y OWSql no lo captura. **Sin verificar.**

## 2. Tabla de bugs (ordenada por severidad y tamaño del arreglo)

Tamaño: S < 20 líneas · M = 20-100 · L > 100. "Sí*" = reproducido parcialmente o solo el mecanismo.

| Issue | Título (corto) | Sev. | ¿Repro? | Causa (fichero:línea) / notas | Tamaño | Riesgo |
|---|---|---|---|---|---|---|
| [#7311](https://github.com/biolab/orange3/issues/7311) | kNN mahalanobis modifica el learner | S1 | Sí | `Orange/base.py:656-658` escribe `self.params["metric_params"]={"V":cov}` en `fit`. La covarianza queda obsoleta: en CV todos los folds usan la del 1.er fold; con otros datos de igual anchura, 30/50 predicciones distintas; con otra anchura, error "size of V does not match" en el widget. Arreglo: copia local de params y `VI=pinv(cov)` (también resuelve el hallazgo 1). | S | Bajo |
| [#6748](https://github.com/biolab/orange3/issues/6748) | Aggregate Columns da NaN con datos dispersos | S1 | Sí | Bug del núcleo: `Table.add_column`→`set_column` (`Orange/data/table.py:1467`, `_get_column_view` en `:1670`) asigna sobre una copia de `X[:, i]` cuando X es disperso y el valor se pierde en silencio (comprobado: `iris.to_sparse().add_column(...)` → todo NaN). | S | Medio (núcleo) |
| [#6067](https://github.com/biolab/orange3/issues/6067) | El Sniffer toma `'` como comilla en .tab/.csv | S1 | Sí | `Orange/data/io.py:147-160` usa `dialect.quotechar` del Sniffer (muestra de 10 líneas). Un `'` sin cerrar engulle filas: se leen 4 de 6 sin error. Los parches locales de E/S no tocan esta parte. Arreglo: `quotechar='"'` fijo y del Sniffer solo el delimitador (probado con monkeypatch). | S | Bajo-medio |
| [#6916](https://github.com/biolab/orange3/issues/6916) | Números grandes con coma decimal "truncados" | S1 | Sí | En memoria el valor está bien. CSV Import crea la variable con `number_of_decimals=None` (`Orange/data/pandas_compat.py:310-312`), así que se usa el formato `%g` de 6 cifras (`Orange/data/variable.py:608-611`). Save Data escribe `-2.21122e+07` (`Orange/data/io_base.py:687-694`): pérdida real en el fichero. | S | Bajo |
| [#7280](https://github.com/biolab/orange3/issues/7280) | Silueta de k-Means ≠ Silhouette Plot | S1 | Sí | La meta "Silhouette" es `arctan(s)/π+0.5` (`Orange/widgets/unsupervised/owkmeans.py:539`), no la silueta: las negativas salen ≈0,49. Además k-Means normaliza por defecto y Silhouette Plot agrupa por la clase (`owsilhouetteplot.py:266`). Sin normalizar y agrupando por Cluster, las dos coinciden exactamente. | S | Medio (cambia salidas) |
| [#7020](https://github.com/biolab/orange3/issues/7020) | Select Columns: se mezclan configuraciones | S1 | Sí* | `SelectAttributesDomainContextHandler.match` (`Orange/widgets/data/owselectcolumns.py:197-211`) solo puntúa las variables seleccionadas. Si falta o se renombra una columna, el contexto global de otra instancia puntúa más (1,0 frente a 0,75) y se adopta su selección. Falta confirmar que sea el disparador exacto del usuario. | S | Medio |
| [#6203](https://github.com/biolab/orange3/issues/6203) | Enteros de 17 dígitos pierden precisión | S1 | Sí | `Orange/data/io_util.py:166-171` (`guess_data_type`) y `Orange/data/pandas_compat.py:309-312` los convierten a float64 sin comprobar 2^53. Cambiar después el tipo a texto no lo recupera. | S-M | Bajo-medio |
| [#6047](https://github.com/biolab/orange3/issues/6047) | DBSCAN: el eps guardado se pierde | S1 | Sí | `Orange/widgets/unsupervised/owdbscan.py:197`: `set_data`→`_compute_cut_point` (`:172-180`) sobrescribe `eps` (0,09 pasa a 0,8565 al recargar), y `:242-258` lo ajustan a los k-distances. Los clusters cambian al reabrir el workflow. | S-M | Bajo-medio |
| [#7326](https://github.com/biolab/orange3/issues/7326) | Nomograma: probabilidades LR multiclase erróneas | S1 | Sí | `Orange/widgets/visualize/ownomogram.py:1232-1244` aplica una sigmoide por clase (opcionalmente dividida por su suma), pero LR es multinomial (softmax). iris[53]: modelo 2/94/5 %; nomograma 15/92/34 % (sin normalizar) u 11/65/24 % (normalizado). Verificado: softmax(z) = predict_proba. PR #7331 abierta. Nota: NB multiclase también difiere (7/92/2 frente a 2/98/0); es la aproximación 1-vs-resto por diseño. | M | Medio |
| [#6499](https://github.com/biolab/orange3/issues/6499) | CSV Import confunde fechas dd/mm | S1 | Sí | `pd.to_datetime` sin formato (`Orange/widgets/data/owcsvimport.py:1699` y `:1620-1622`) recurre a dateutil fila a fila: 08/03/18 → 3 de agosto; 28/03/18 → 28 de marzo. Arreglo: probar formatos exactos por columna y aceptar solo uno que encaje en todas las filas. | M | Medio |
| [#7343](https://github.com/biolab/orange3/issues/7343) | Datasets: SIGSEGV al cambiar de dataset mientras descarga | S2 | Sí* | `Orange/widgets/data/owdatasets.py:695` crea `Progress()` sin padre; si `commit()` se repite (`:692`), se destruye mientras el hilo emite. Script de la issue: 4/8 SIGSEGV; con padre, 3/3 OK. PR #7345 (1 línea). | S | Bajo |
| [#7132](https://github.com/biolab/orange3/issues/7132) | Merge Data falla con PCA + concatenar | S2 | Sí | `Orange/widgets/data/owmergedata.py:615-624`: si `rightu` está vacío se ejecuta igualmente `extra_data[rightu].transform(...)`, y `compute_shared` de PCA falla con 0 filas. | S | Bajo |
| [#7065](https://github.com/biolab/orange3/issues/7065) | Group By falla con fecha discretizada | S2 | Sí | Bug del núcleo: `Discretizer.__eq__` (`Orange/preprocess/discretize.py:142-143`) compara `points` con `==` y `FixedTimeWidth` los crea como ndarray (`:294`) → "truth value of an array is ambiguous". Los NaN no influyen. Arreglo: `np.array_equal`. | S | Bajo |
| [#6672](https://github.com/biolab/orange3/issues/6672) | Predictions: `ContinuousVariable has no attribute values` | S2 | Sí | `Orange/widgets/evaluate/owpredictions.py:261`: `openContext(...values if discrete else ())` usa la misma clave para clase discreta vacía, continua o ausente, y se restaura `shown_probs`. `:696-703` no comprueba `is_discrete_class`; `:931` falla si no hay modelo (report). | S | Bajo |
| [#7276](https://github.com/biolab/orange3/issues/7276) | Excel sin clase y cabecera de 3 líneas se lee mal | S2 | Sí | `Orange/data/io.py:312` (`filter(any, cells)`) elimina también la fila de flags vacía; lo mismo en `.xls` (`:380`, no probado). Arreglo: `chain(islice(cells,3), filter(any, cells))` (probado con monkeypatch). | S | Bajo |
| [#5700](https://github.com/biolab/orange3/issues/5700) | Venn Diagram falla con datos dispersos | S2 | Sí | `Orange/widgets/visualize/owvenndiagram.py:438, 468-478, ~605-611` apilan como densas columnas que son dispersas (`table[:, var].X`). Falla en los dos modos. | S-M | Bajo |
| [#7308](https://github.com/biolab/orange3/issues/7308) | Scatter Plot: etiquetas del eje X obsoletas | S3 | Sí | `Orange/widgets/visualize/utils/widget.py:475-478` invalida por `domain.checksum()`, que no tiene en cuenta los valores discretos, así que no se llama `update_axes()`. PR #7336 abierta. | S | Bajo |
| [#7344](https://github.com/biolab/orange3/issues/7344) | Pythagorean Tree muestra una sola caja | S3 | Sí* | `depth_limit` es un ContextSetting (`Orange/widgets/visualize/owpythagorastree.py:62`). `openContext` (`:176-178`) restaura `depth_limit=0` guardado de un árbol trivial anterior. Mecanismo reproducido; el caso concreto del usuario no se ha verificado. | S | Bajo |
| [#5914](https://github.com/biolab/orange3/issues/5914) | Edit Domain: aumentar N al agrupar no surte efecto | S3 | Sí | `Orange/widgets/data/oweditdomain.py:1543-1548` (`complete_merge`) no devuelve su nombre original a los valores fusionados antes. Probado en el editor, no en el widget completo. | S | Bajo |
| [#5485](https://github.com/biolab/orange3/issues/5485) | Widget Color: errores | S3 | Sí* | El pickling y los datos duplicados ya están corregidos. Persiste un `IndexError` al tabular por celdas vacías (`Orange/widgets/data/owcolor.py:252-253` flags, `:324-333` setData). | S | Bajo |
| [#5632](https://github.com/biolab/orange3/issues/5632) | `Table.copy()` cambia la dispersión | S3 | Sí | `Orange/data/table.py:1502` → `from_table` → `assure_domain_conversion_sparsity` (`:2596-2613`) densifica según los flags `sparse`. Riesgo de memoria, no de valores. | S | Bajo-medio |
| [#5961](https://github.com/biolab/orange3/issues/5961) | Postgres: base de datos con "/" en el nombre | S3 | Sí (parseo) | `Orange/widgets/utils/owbasesql.py:111` hace `partition("/")` sobre "db/schema" sin forma de escapar. | S | Bajo |
| [#6427](https://github.com/biolab/orange3/issues/6427) | SQL: tablas de más de 1e6 filas "encogen" | S3 | No probado | Muestreo `TABLESAMPLE system` por diseño (`Orange/widgets/data/owsql.py:306-325`, `Orange/data/sql/table.py:587-631`), sin aviso persistente; la muestra se guarda como tabla y se reutiliza. Arreglo: aviso con tamaño de muestra y total. | S-M | Bajo |
| [#6808](https://github.com/biolab/orange3/issues/6808) | "NA" pasa a "?" de forma inconsistente | S3 | Sí | `Orange/data/io_util.py:124,154-191`: los NA se enmascaran solo si la columna sale discreta o numérica. Cambiar el tipo en el widget File convierte la tabla ya leída (`Orange/widgets/utils/domaineditor.py:328-357`), así que el "NA" no se recupera. | M | Medio |
| [#6431](https://github.com/biolab/orange3/issues/6431) | Dos SQL Table comparten credenciales | S3 | Sí* | La clave del llavero es solo host:port (`Orange/widgets/utils/owbasesql.py:84-102`). Probado con un gestor de credenciales falso. | M | Medio |
| [#6105](https://github.com/biolab/orange3/issues/6105) | El informe solo muestra los primeros gráficos | S3 | Sí | Está en orange-widget-base (`orangewidget/report/owreport.py:247-260`): `QWebEngineView.setHtml` tiene un límite de 2 MB; con 9 o 10 gráficos de 2000 puntos el resto no se muestra ni se guarda. | M | Medio |
| [#6721](https://github.com/biolab/orange3/issues/6721) | DomainContextHandler ignora el rol de la variable | S3 | Sí | `Orange/widgets/settings.py:83-101, 195-203`: el test de la issue falla con "Combo box does not contain item". PR #6740 (borrador). | L | Medio-alto |
| [#7268](https://github.com/biolab/orange3/issues/7268) | Box Plot desaparece al cambiar opciones | S3? | No | 416 combinaciones (titanic, housing, heart_disease, sintético) sin excepciones ni escenas vacías. Posible confusión de UI con las cajas "Display" alternas (`owboxplot.py:264-291`). Hacen falta los datos del usuario. | — | — |
| [#6367](https://github.com/biolab/orange3/issues/6367) | Widgets con variables ocultas | S4 | Sí* | Scatter Plot, Group By, Aggregate y Select Columns ya están corregidos. Queda Sieve: con `[oculta, x]` dibuja x×x sin avisar (`Orange/widgets/visualize/owsieve.py:270-276`). | S | Bajo |

## 3. Bugs menores (no reproducidos; estimación por la descripción)

| Issue | Título | Sev. | Nota |
|---|---|---|---|
| [#7272](https://github.com/biolab/orange3/issues/7272) | Ejes del Scatter Plot con prefijo SI (pyqtgraph 0.14) | S4 | Nuestro entorno usa pyqtgraph 0.14. Arreglo: `enableAutoSIPrefix(False)` en los ejes. S. |
| [#6543](https://github.com/biolab/orange3/issues/6543) | Ejes desalineados al copiar o guardar PNG | S4 | Windows con escalado. |
| [#6497](https://github.com/biolab/orange3/issues/6497) | Test & Score reinicia el ancho de columna | S4 | |
| [#6471](https://github.com/biolab/orange3/issues/6471) | Ventanas en el monitor equivocado | S4 | |
| [#5642](https://github.com/biolab/orange3/issues/5642) | Heat Map: aspecto al dividir por grupos | S4 | |
| [#5579](https://github.com/biolab/orange3/issues/5579) | Posiciones de ventanas en grupos | S4 | |
| [#5890](https://github.com/biolab/orange3/issues/5890) | Nomograma: los puntos deberían bloquearse con datos de entrada | S4 | |
| [#7330](https://github.com/biolab/orange3/issues/7330) | Nomograma: los valores elegidos se reinician | S4 | Más bien UX o mejora. |
| [#6839](https://github.com/biolab/orange3/issues/6839) | Concatenate: descripción engañosa | S4 | Texto de la opción. |

**Otros (13):**

- Instalación, add-ons o entorno: 7346, 7265, 7261, 6744, 6043, 5766, 5693.
- Pregunta: 6941.
- Mantenimiento o compatibilidad: 7328 (pyqtgraph `LegendItem.layout`, a vigilar con pyqtgraph ≥ 0.14), 6858.
- Documentación o discusión: 6986, 4090, 5550.

**Peticiones de funcionalidad (55):** el resto. #6005 está etiquetada como *wish* aunque un mantenedor la considera bug; aquí se ha clasificado como petición.
## 4. Los 5 fallos locales de tests en macOS

Resumen: **los 5 fallos son artefactos de ejecutar con `QT_QPA_PLATFORM=offscreen` en macOS. Ninguno tiene que ver con los parches de rendimiento ni con #7326.**

Evidencias comunes:

| Ejecución | test_ownomogram (2) | test_stickygraphicsview (3) |
|---|---|---|
| Rama `gualbe`, `offscreen` | FALLAN | FALLAN |
| Upstream bd6fef4ca sin parches (`git archive` extraído al scratchpad, con los mismos `.so`), `offscreen` | FALLAN | FALLAN |
| Rama `gualbe`, `QT_QPA_PLATFORM=cocoa` (nativo) | pasan (35/35 OK) | pasan |
| Rama `gualbe`, `QT_QPA_PLATFORM=minimal` | fallan 5 tests del nomograma (más que con offscreen) | — |

La CI de upstream ejecuta los tests de macOS **sin** `offscreen` (`.github/workflows/test.yml`, job `test_on_macos_and_windows`: `tox -e orange-released`, sin `QT_QPA_PLATFORM`) y los de Linux con `xvfb-run` (xcb). Por eso upstream no ve estos fallos.

### 4.1 test_nomogram_nb / test_nomogram_lr: no es #7326

- Los dos tests que fallan usan `heart_disease`, que es **binario**, y uno de ellos es **Naive Bayes**. #7326 solo afecta a la regresión logística **multiclase** (softmax). Los tests multiclase (`test_nomogram_lr_multiclass`, `test_nomogram_nb_multiclass`) **pasan** en offscreen.
- Causa: el nomograma calcula la probabilidad a partir de **posiciones en píxeles** de los marcadores, recortadas (`np.clip`) al rango de la regla (`DotItem.move_to_val`, `Orange/widgets/visualize/ownomogram.py:103-106`). El ancho útil es `max_width = viewport_width + name_offset - 30` (`ownomogram.py:1019-1021`), donde `name_offset` depende del ancho del texto más largo.
  - En el test el widget no se muestra: el viewport mide 300 px.
  - Con `offscreen` en macOS la fuente es `.AppleSystemUIFont` a 12,24 pt con DPI lógico 96-100, frente a 13 pt con 72 dpi en cocoa. El texto "Probabilities (%)" mide 133 px en lugar de 108. Resultado: `max_width` = 66,6 px (offscreen) frente a 100,2 px (cocoa).
  - Con solo 66 px, `get_ruler_values` genera una regla tan gruesa que el marcador de "Total" se recorta. NB muestra Total 5,0 → 99 % (se espera 0,0 → 54 %). LR muestra Total 6,73 → 0 % (se espera 57 %).
- Prueba de que depende solo de la geometría (`repro/tests_local/diag_nomo3.py`): en **cocoa**, con el mismo modelo y solo los nombres de los atributos alargados, el nomograma pasa de 54 % a 100 % (NB) y de 57 % a 0 % (LR). Con el widget visible el viewport mínimo es de unos 480 px y el resultado es correcto en ambas plataformas, también con nombres largos (`diag_nomo4.py`, `diag_nomo5.py`). Es una **fragilidad latente** (S4: solo aparece con viewports muy estrechos), no un fallo de cálculo.
- Arreglo propuesto para la rama: en los tests, `self.widget.show(); self.widget.resize(900, 700)` antes de enviar el clasificador, o forzar un `max_width` mínimo (p. ej. `max(max_width, 150)`) en `update_scene`. Tamaño S, riesgo bajo.

### 4.2 test_stickygraphicsview (test, test_fractional_1, test_fractional_2)

- Siempre falla la misma aserción: tras desplazar **hasta el final**, el pie (`footer`) sigue visible.
- Causa (`repro/tests_local/diag_sticky.py`):
  - Con `offscreen` el estilo es **Fusion**, con barras de desplazamiento no transitorias que ocupan sitio. En cocoa el estilo es `macintosh`, con barras superpuestas (`SH_ScrollBar_Transient` = 1) que no restan espacio al viewport.
  - Con 310×100 aparecen las dos barras. `QGraphicsView` reserva para la barra horizontal `PM_ScrollBarExtent` = **14 px**, pero la barra real mide **19 px** (`sizeHint`; 18 px con `QT_FONT_DPI=96`).
  - El rango vertical queda en 0..67 cuando harían falta 0..72 (escena de 151 px de alto, viewport de 79 px). Al "llegar al final", el borde inferior visible está en y=146 de la escena, y el pie (y 130-150) sigue cortado 4-5 px. Por eso `StickyGraphicsView.__updateView` (`Orange/widgets/utils/stickygraphicsview.py:229-232`) lo marca visible con toda lógica.
  - En cocoa el viewport sigue en 310×100, el final se alcanza y el pie se oculta.
- Es un artefacto de Qt/estilo Fusion en offscreen sobre macOS. En uso real el efecto sería, como mucho, cosmético (pie fijo visible unos px de más en Heat Map con estilo Fusion). S4. Lo más sencillo es saltar estos tests si `QApplication.platformName() == "offscreen"` y `sys.platform == "darwin"`, o ejecutar la suite de macOS con `cocoa`.

## 5. Top 10 recomendados para corregir primero

1. **#7311 kNN mahalanobis:** S1 que corrompe la CV en silencio; arreglo de ~10 líneas que además elimina el crash con *brute* en sklearn 1.9.1.
2. **#6748 `Table.add_column` con X disperso:** S1 en el núcleo (afecta a cualquier llamador, no solo a Aggregate Columns); arreglo S.
3. **#7343 Datasets SIGSEGV:** cierra un crash del proceso con una línea (`Progress(self)`, PR #7345).
4. **#6067 Sniffer y comillas:** S1 de lectura (filas perdidas sin aviso) en el código de E/S que ya estamos optimizando; arreglo S y probado.
5. **#6916 `%g` al guardar:** S1 de pérdida de precisión en ficheros escritos; arreglo S en `pandas_compat`/escritor, también dentro del área de E/S.
6. **#7065 `Discretizer.__eq__`:** S2 del núcleo con arreglo de una línea (`np.array_equal`); evita fallos en cualquier comparación de variables discretizadas por tiempo.
7. **#7326 Nomograma softmax:** S1 visible para usuarios docentes; ya existe la PR #7331 con tests para integrarla.
8. **#6203 Enteros > 2^53:** S1 en identificadores; regla simple (pasar a texto) en los dos lectores.
9. **#7020 Select Columns:** S1 (selección equivocada sin aviso en flujos grandes); arreglo S en `match`, con riesgo medio: añadir tests de contexto.
10. **#6672 Predictions:** S2 persistente vía settings; arreglo S de bajo riesgo.

Siguientes candidatos: #7132 y #7276 (S2, S, riesgo bajo), #6047 (S1, S-M), #7280 (S1, S, pero cambia salidas existentes), #7308 (S3, PR #7336 lista).

## 6. Limitaciones

- No se descargaron los ficheros adjuntos a las issues (#7344, #7268, #7308, #6808, #5485, etc.); se usaron datos sintéticos o los incluidos en Orange.
- No se probó nada contra Postgres ni MS SQL reales, ni contra el llavero del sistema.
- No se ejecutaron las suites de tests completas con los arreglos propuestos. Solo se validaron con monkeypatch #7276 y #6067.
- En #7020 y #7344 se reprodujo un mecanismo plausible; no está confirmado que sea el disparador del usuario.
- Las estimaciones de tamaño y riesgo son orientativas.
