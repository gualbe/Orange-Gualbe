# Plan de fusión: Orange 3.41.0 oficial → Orange-Gualbe 3.41.0+gualbe.2

Plan pensado para que una sesión de Claude Code lo ejecute de principio a fin
sin preguntar, salvo en los **puntos de parada** marcados con ⛔. Redactado el
23-11-2026 a partir de una fusión de prueba (abortada) de la etiqueta `3.41.0`
sobre `gualbe` (`cf05823a7`).

## 0. Alcance y autorización

- **Objetivo:** integrar la versión oficial 3.41.0 (etiqueta `3.41.0`,
  `46443558d`, publicada el 8-11-2026; 60 commits que no están en `gualbe`),
  verificarla y publicar `3.41.0+gualbe.2` con wheels e instaladores.
- **Base:** la etiqueta `3.41.0`, **no** `upstream/master` (que ya va por
  delante, en desarrollo de 3.42).
- **Autorización:** el usuario pide ejecutar este plan íntegro. Eso incluye
  push de `master` y `gualbe`, la etiqueta `3.41.0+gualbe.2`, la release de
  GitHub y los workflows de wheels e instaladores (fase 9). Nada más: ni
  comentarios en biolab/orange3, ni cambios en otros repos aparte de lanzar
  los workflows de `gualbe/Orange-Gualbe-installers`.
- **Puntos de parada ⛔:** si se da uno, no publiques nada. Deja la rama
  `sync/3.41.0` con lo hecho, escribe el informe (fase 7) con el motivo y
  termina explicándolo.

### Datos fijos

| Qué | Valor |
|---|---|
| Repo | `/Users/gualberto/Claude/Orange-Gualbe` (copia del usuario, en `gualbe`) |
| Worktree | `/tmp/orange-gualbe-sync-3.41.0`, rama `sync/3.41.0` |
| Python | `PY=/Users/gualberto/miniforge3/envs/orange-gualbe/bin/python` (no uses la función `conda` del shell) |
| conda | `/Users/gualberto/miniforge3/bin/conda` (binario, para el entorno temporal) |
| Tests | `QT_QPA_PLATFORM=offscreen $PY -m unittest Orange.tests Orange.widgets.tests` (~3 min; referencia: **0 fallos**) |
| Bench núcleo | `gualbe/bench/large_data.py --rows 1000000 --out <json>`; referencia `gualbe/bench/results/fase2c-1M.json` |
| Bench widgets | `QT_QPA_PLATFORM=offscreen BENCH_ROWS=1000000 BENCH_OUT=<json> $PY -m unittest gualbe/bench/widgets.py`; referencia `gualbe/bench/results/fase2d-widgets-1M.json` |
| Comparar | `$PY gualbe/bench/compare.py <antes.json> <después.json>` |

Usa `git -C <ruta>` o rutas absolutas: el `cd` no siempre se conserva entre
órdenes.

## 1. Preparación

```bash
cd /Users/gualberto/Claude/Orange-Gualbe
git status --porcelain            # debe salir vacío (si no: ⛔)
git fetch upstream --tags && git fetch origin
git rev-parse 3.41.0^{commit}     # debe ser 46443558d…
git rev-parse gualbe origin/gualbe   # deben coincidir (si no: ⛔, hay trabajo sin sincronizar)
git branch --list 'sync/3.41.0'
```

- Si ya existe `sync/3.41.0` y tiene commits que no están en `gualbe`
  (`git log gualbe..sync/3.41.0`), ⛔: no la pises. Si existe y no tiene
  commits propios, bórrala (`git branch -D sync/3.41.0`).
- Si `gualbe` ya no es `cf05823a7`, sigue igualmente, pero revisa en la fase 2
  que los conflictos sean los mismos. Si aparecen otros, resuélvelos con el
  mismo criterio (conservar lo de Orange-Gualbe y lo oficial) y anótalos en el
  informe.

```bash
git worktree add /tmp/orange-gualbe-sync-3.41.0 -b sync/3.41.0 gualbe
W=/tmp/orange-gualbe-sync-3.41.0
git -C $W merge --no-ff --no-commit 3.41.0
git -C $W diff --name-only --diff-filter=U
```

Los conflictos esperados son exactamente estos cinco:
`Orange/data/io.py`, `Orange/widgets/data/owdatasets.py`,
`Orange/widgets/visualize/tests/test_ownomogram.py`, `conda-recipe/meta.yaml`
y `requirements-core.txt`.

## 2. Resolución de conflictos (decisiones ya tomadas)

### 2.1 `requirements-core.txt`: conservar el límite de Orange-Gualbe

Orange oficial pone `scikit-learn<1.10` porque la 1.10 rompe
`LogisticRegression` y MDS. Orange-Gualbe ya cubre esos cambios con
`Orange/misc/_skl_compat.py` y decidió `<1.11` en la Fase 2 (commit
`8a6886c7c`; ver `gualbe/CHANGELOG.md`, «scikit-learn 1.10 y 1.11»). Deja
**solo** la línea de HEAD:

```text
scikit-learn>=1.5.1,<1.11  # 1.11 drops SVC(probability=True); see gualbe/CHANGELOG.md
```

`tzdata` (nuevo en la versión oficial) ya entra sin conflicto; compruébalo.

### 2.2 `conda-recipe/meta.yaml`: lo mismo

Deja `- scikit-learn >=1.5.1,<1.11`. El resto del bloque (`tzdata`, `xgboost
>=1.7.4` sin tope, `xlsxwriter` reordenado, `python.app  # [osx]`) queda como
lo trae la versión oficial.

### 2.3 `Orange/data/io.py`: adoptar la solución oficial de gh-7276

Las dos ramas arreglaron el mismo error (Excel con cabecera de tres líneas y
fila de indicadores vacía). Orange-Gualbe lo hacía con `_skip_empty_rows`;
Orange oficial (`80bb06c1a`) conserva las filas vacías tras la primera no
vacía y deja que `data_table` descarte las filas de datos vacías.

1. En los dos bloques en conflicto (`ExcelReader` y `XlsReader`), quédate con
   la versión de `3.41.0` (`dropwhile(...)` y el generador sin filtrar), con
   sus comentarios.
2. Borra la función `_skip_empty_rows` (hacia la línea 276) si ya no la usa
   nada: `grep -n _skip_empty_rows Orange/data/io.py`.
3. Quita `_RE_TYPES` de la importación de la línea ~31 si ya no se usa:
   `grep -n _RE_TYPES Orange/data/io.py`.
4. Comprueba que la importación diga `from itertools import chain, dropwhile`.
5. Conserva los tests de **las dos** ramas: `Orange/tests/test_xlsx_empty_flags.py`
   (Orange-Gualbe) y los nuevos de `Orange/tests/test_xlsx_reader.py`, con
   `header_3_no_flags.xls(x)` (oficiales).
6. Prueba rápida, después de compilar (fase 3.1):
   `$PY -m unittest Orange.tests.test_xlsx_reader Orange.tests.test_xlsx_empty_flags Orange.tests.test_io Orange.tests.test_tab_reader`
   - **Alternativa** si falla algo que no se arregle trivialmente, en
     especial `test_empty_rows_are_skipped`: vuelve a la versión de HEAD
     (`_skip_empty_rows` en los dos lectores) y comprueba que pasen también
     los tests oficiales. Si tampoco pasan así, ⛔.

### 2.4 `Orange/widgets/data/owdatasets.py`: trivial

El código es igual en las dos ramas (el arreglo de gh-7343, `Progress(self)`,
ya es oficial: `f4d891ed8`). Quédate con la versión de HEAD, que solo añade el
comentario. Comprueba que `git diff 3.41.0 -- Orange/widgets/data/owdatasets.py`
muestre únicamente esas dos líneas de comentario.

### 2.5 `Orange/widgets/visualize/tests/test_ownomogram.py`

Orange-Gualbe integró la PR #7331 (softmax del nomograma) antes de que se
fusionara en la versión oficial. Allí luego se quitó `w.show()` de tres tests
(`8b1a42f7e`) y se añadió `test_hidden_probability_ticks_not_in_scene`
(`b6a16b4d7`). `ownomogram.py` se fusiona sin conflicto: la única diferencia
con la oficial es el ancho mínimo de la regla, que es propio de Orange-Gualbe
(`max(w + name_offset - 30, 150)`).

- En los bloques 1, 2 y 4 (solo `w.show()`), quédate con la versión oficial,
  sin `show()`.
- En el bloque 3, quédate con la versión oficial (añade el test nuevo).
- `git diff 3.41.0 -- <fichero>` debe mostrar solo lo propio de Orange-Gualbe
  (tests del ancho mínimo, si están fuera de esos bloques) o nada.
- Ejecuta `$PY -m unittest Orange.widgets.visualize.tests.test_ownomogram`
  **3 veces** (con `QT_QPA_PLATFORM=offscreen`). Si algún test falla sin
  `show()` en offscreen, vuelve a poner `w.show()` solo en ese test y anótalo.

### 2.6 Ajustes después de la fusión (sin conflicto, pero necesarios)

- **`setup.py`:** la fusión trae `ISRELEASED = True` de la etiqueta oficial.
  Vuelve a `ISRELEASED = False` (las compilaciones de desarrollo de `gualbe`
  deben llevar `.dev0+<hash>`; el workflow de wheels lo pone a `True` para
  la release). `VERSION = '3.41.0'` se queda igual.
- **numpy y pandas:** Orange oficial quita los topes (`a1b479d01`,
  `060a6ee74`) y la fusión deja `numpy>=1.21.0` y `pandas>=2.0.1` en
  `requirements-core.txt`. En `gualbe` había `numpy<2.4` y `pandas<3`. Se
  decide en la fase 4: de momento deja lo que trae la fusión.
- No toques `i18n/es/msgs.jaml` (traducción oficial al castellano, nueva).

Cuando no queden marcas de conflicto
(`git -C $W diff --check` y `grep -rn '^<<<<<<<\|^>>>>>>>' $W/Orange $W/requirements-core.txt $W/conda-recipe`):

```bash
git -C $W add -A
git -C $W commit -m "Integrar Orange 3.41.0 oficial" -m "<resumen de cómo se resolvió cada conflicto>"
```

El commit de fusión lleva al final la línea de coautoría habitual.

## 3. Verificación A: tests en el entorno de referencia

En el entorno `orange-gualbe`: numpy 2.3.5, pandas 2.3.3, scikit-learn 1.9.1.

```bash
cd $W
$PY setup.py build_ext --inplace
PYTHONPATH=$W $PY -c "import Orange; print(Orange.__file__)"     # debe estar bajo $W
PYTHONPATH=$W QT_QPA_PLATFORM=offscreen $PY -m unittest Orange.tests Orange.widgets.tests 2>&1 | tee $W/tests-ref.log | tail -5
```

- Haz las pruebas rápidas de 2.3 y 2.5 antes de la suite completa.
- **Criterio:** 0 fallos y 0 errores. La versión gualbe.1 tenía 6098 tests;
  ahora deben ser más (los nuevos oficiales). Anota el número.
- Si hay fallos, investígalos y corrígelos en la rama, en commits aparte con
  mensaje en español (`fix(sync): …`). Cuando el fallo venga de la
  interacción entre un parche de Orange-Gualbe y un cambio oficial, conserva
  el comportamiento oficial salvo que contradiga un cambio intencionado de
  `gualbe/CHANGELOG.md`. Si tras un esfuerzo razonable sigue fallando algo, ⛔.
- Atención a los ficheros que cambiaron en las dos ramas y se fusionaron
  solos: `Orange/data/pandas_compat.py`, `Orange/data/table.py`,
  `Orange/widgets/data/owcsvimport.py` y `Orange/widgets/visualize/ownomogram.py`.

## 4. Verificación B: numpy y pandas sin tope

Orange oficial ya admite numpy ≥ 2.4 y pandas 3, pero el código en Cython y
los parches de lectura y escritura de Orange-Gualbe solo se han probado con
numpy 2.3 y pandas 2.3. Los instaladores no se ven afectados, porque
`Orange-Gualbe-installers` fija `numpy~=2.3.5` y `pandas~=2.3.3`. Sí afecta a
quien instale los wheels con pip.

```bash
E=/tmp/orange-gualbe-env-np-latest
/Users/gualberto/miniforge3/bin/conda create -y -p $E -c conda-forge python=3.12 numpy scipy \
    "scikit-learn<1.11" pandas bottleneck cython "pyqt=5.15" pyqtwebengine anyqt matplotlib \
    pyqtgraph qtconsole openpyxl xlrd xlsxwriter networkx opentsne python-louvain "xgboost<2.1" \
    serverfiles pyyaml requests tzdata
$E/bin/pip install --no-deps -q "orange-widget-base" "orange-canvas-core" baycomp chardet keyring keyrings.alt pip-install-hint  # si faltan; ajusta a requirements-*.txt
$E/bin/python -c "import numpy, pandas; print(numpy.__version__, pandas.__version__)"
```

- Si numpy < 2.4 o pandas < 3 (aún no hay versiones en conda-forge), no hay
  nada que probar. Deja los topes como estaban en `gualbe` (`numpy<2.4`,
  `pandas<3`) con un comentario y sáltate el resto de esta fase.
- Si no, compila una copia **aparte** (para no mezclar los `.so` con los del
  entorno de referencia):
  `git -C $W worktree add /tmp/orange-gualbe-np-latest HEAD`, después
  `build_ext --inplace` con `$E/bin/python` y la suite completa con
  `PYTHONPATH` en esa copia.
- **Decisión:**
  - Con 0 fallos, se acepta la retirada de los topes, como en la versión
    oficial. Anótalo en el CHANGELOG: «probado con numpy X y pandas Y».
  - Con fallos solo en el código de Orange-Gualbe, corrígelos si es algo
    acotado (commit `fix(compat): …`) y repite.
  - Si no, vuelve a poner `numpy>=1.21.0,<2.4` y `pandas>=2.0.1,<3` en
    `requirements-core.txt` (y en `conda-recipe/meta.yaml`, sección `run`)
    con el motivo, y anótalo en el CHANGELOG como limitación conocida.
  - Ninguno de estos casos es un punto de parada.
- Al terminar, borra el entorno y su worktree:
  `rm -rf $E`, `git worktree remove --force /tmp/orange-gualbe-np-latest`.

## 5. Verificación C: scikit-learn 1.10 (condicional)

```bash
curl -s https://pypi.org/pypi/scikit-learn/json | $PY -c "import json,sys; print(sorted(json.load(sys.stdin)['releases']))" | tr ',' '\n' | grep "1\.10"
```

- Si hay una versión 1.10 (definitiva o rc) en PyPI, créate otro entorno
  temporal como en la fase 4, pero con `scikit-learn==1.10.*` (y `--pre` si es
  rc). Ejecuta
  `Orange.tests.test_logistic_regression Orange.tests.test_manifold Orange.widgets.unsupervised.tests.test_owmanifoldlearning Orange.widgets.visualize.tests.test_ownomogram Orange.tests.test_classification`
  y anota el resultado. Si falla, no pares: anótalo en el informe como
  riesgo de mantener `<1.11`.
- Si no la hay (el 23-11-2026 la última era la 1.9.1), anota «no verificable
  aún» y sigue.

## 6. Benchmarks

En el entorno de referencia y con el código del worktree:

```bash
cd $W
PYTHONPATH=$W $PY gualbe/bench/large_data.py --rows 1000000 --out /tmp/og-sync-core.json
PYTHONPATH=$W $PY gualbe/bench/compare.py gualbe/bench/results/fase2c-1M.json /tmp/og-sync-core.json
PYTHONPATH=$W QT_QPA_PLATFORM=offscreen BENCH_ROWS=1000000 BENCH_OUT=/tmp/og-sync-widgets.json \
    $PY -m unittest gualbe/bench/widgets.py
PYTHONPATH=$W $PY gualbe/bench/compare.py gualbe/bench/results/fase2d-widgets-1M.json /tmp/og-sync-widgets.json
```

- Señala las operaciones que cambien más de un 15 %.
- Si una es más de un 15 % **más lenta**, repite esa medición dos veces más
  (`BENCH_ONLY=<nombre>` en los widgets) para descartar ruido.
  - Si se confirma y la causa es un cambio oficial (p. ej. `878f8ccde`, que
    desactiva por defecto la agregación de regiones densas del Scatter
    Plot), documéntalo como tal.
  - Si se confirma y la causa es la fusión con un parche de Orange-Gualbe
    (lectura de Excel, `table.py`, `pandas_compat.py`), intenta corregirlo.
    Si no lo consigues, ⛔.
- Guarda los resultados definitivos en
  `gualbe/bench/results/sync-3.41.0-1M.json` y
  `gualbe/bench/results/sync-3.41.0-widgets-1M.json`.

## 7. Documentación y commit

1. **Informe** `gualbe/reports/sync-3.41.0.md`:
   - versión oficial y fecha;
   - resumen de sus notas (`gh release view 3.41.0 -R biolab/orange3`);
   - cómo se resolvió cada conflicto y por qué;
   - los arreglos que ahora son oficiales (softmax del nomograma #7331,
     segfault de Datasets #7343, Excel sin indicadores #7276);
   - tests (número, fallos), resultados de las fases 4 y 5, tabla del
     benchmark y riesgos pendientes.
2. **`gualbe/CHANGELOG.md`:** convierte «## Sin publicar» en
   `## 3.41.0+gualbe.2 (<fecha de hoy>)`:
   - Base: versión oficial 3.41.0 (`46443558d`).
   - Suite: N tests sin fallos (entorno igual que en gualbe.1).
   - Mantén la entrada de ElasticNetCV y añade una sección **«Integración de
     Orange 3.41.0»**: qué arreglos propios pasan a ser los oficiales
     (Nomogram con softmax, Datasets, Excel con cabecera de tres líneas:
     ahora con la solución oficial), la decisión sobre scikit-learn (se
     mantiene `<1.11`; la oficial pone `<1.10`) y la de numpy y pandas
     (fase 4).
   - Deja una sección `## Sin publicar` vacía encima.
3. **`gualbe/releases/3.41.0+gualbe.2.md`:** sigue la estructura de
   `3.41.0+gualbe.1.md` (descargas, instalación, pip, SHA-256 y novedades),
   con los nombres de fichero de `+gualbe.2` y el enlace de pip
   `…/expanded_assets/3.41.0%2Bgualbe.2`. Deja los SHA-256 como
   `PENDIENTE`, que se rellenan en la fase 9. Arriba, un resumen: «Basada en
   la versión oficial Orange 3.41.0», con sus novedades principales
   (traducción al castellano, compatibilidad con pandas 3 y numpy 2.4,
   nomograma, ficheros recientes en QSettings…) y lo nuevo propio.
4. Si cambian los requisitos, revisa que el bloque de instalación de
   `gualbe/README.md` sea coherente con `requirements-core.txt`.
5. Haz commit en `sync/3.41.0` con un mensaje en español, p. ej. «Informe de
   integración de 3.41.0, changelog y notas de 3.41.0+gualbe.2», y la línea
   de coautoría.

⛔ **Puerta antes de publicar:** fase 3 con 0 fallos, ningún ⛔ abierto en las
fases 2 y 6, y el árbol del worktree limpio.

## 8. Integración local

```bash
R=/Users/gualberto/Claude/Orange-Gualbe
git -C $R status --porcelain                    # vacío
git -C $R switch gualbe
git -C $R merge --ff-only sync/3.41.0           # si no es fast-forward: ⛔
git -C $R fetch . upstream/master:master        # master = upstream/master (fast-forward, sin cambiar de rama)
cd $R && $PY setup.py build_ext --inplace       # el editable de la copia del usuario apunta aquí
$PY -c "import Orange, Orange.version as v; print(Orange.__file__, v.full_version)"
QT_QPA_PLATFORM=offscreen $PY -m unittest Orange.tests.test_xlsx_reader Orange.widgets.visualize.tests.test_ownomogram
```

`gualbe/sync_upstream.sh` no hace falta: su fusión ya está hecha, y el
fast-forward de `master` se hace con el `fetch .` de arriba.

## 9. Publicación (autorizada en la fase 0)

```bash
git -C $R push origin master
git -C $R push origin gualbe
git -C $R tag -a "3.41.0+gualbe.2" -m "Orange-Gualbe 3.41.0+gualbe.2" gualbe
git -C $R push origin "3.41.0+gualbe.2"
gh release create "3.41.0+gualbe.2" -R gualbe/Orange-Gualbe --title "Orange-Gualbe 3.41.0+gualbe.2" \
    --notes-file $R/gualbe/releases/3.41.0+gualbe.2.md --latest
```

Binarios, según `gualbe/README.md` («Release binaries»):

```bash
gh workflow run "Orange-Gualbe wheels" -R gualbe/Orange-Gualbe --ref gualbe -f tag=3.41.0+gualbe.2
gh workflow run "Build Windows Installer" -R gualbe/Orange-Gualbe-installers --ref orange-gualbe -f tag=3.41.0+gualbe.2
gh workflow run "Build macOS dmg" -R gualbe/Orange-Gualbe-installers --ref orange-gualbe -f tag=3.41.0+gualbe.2
```

- Sigue cada ejecución con `gh run list … -L 3` y `gh run watch <id>` (en
  segundo plano o con Monitor, no con `sleep`). Los instaladores ejecutan la
  suite completa sobre la app instalada y tardan.
- Si falla un workflow, lee el log (`gh run view <id> --log-failed`). Si es
  algo transitorio (red, runner), reintenta una vez con `gh run rerun`. Si es
  un fallo real, la release se queda publicada sin ese binario; anótalo y no
  borres la release.
- Instaladores: `gh run download <id> -R gualbe/Orange-Gualbe-installers -D /tmp/og-installers`.
  Después `shasum -a 256` de cada `.exe` y `.dmg` y
  `gh release upload "3.41.0+gualbe.2" <ficheros> -R gualbe/Orange-Gualbe`.
- Rellena los SHA-256 en `gualbe/releases/3.41.0+gualbe.2.md` y súbelo:
  - commit en `gualbe`, mensaje «Notas de 3.41.0+gualbe.2 con descargas», y push;
  - actualiza la release con
    `gh release edit "3.41.0+gualbe.2" -R gualbe/Orange-Gualbe --notes-file …`.
- Comprueba los ficheros adjuntos con
  `gh release view "3.41.0+gualbe.2" -R gualbe/Orange-Gualbe --json assets -q '.assets[].name'`:
  wheels de Linux, macOS y Windows (Python 3.11–3.14), un `.exe` y dos `.dmg`
  (arm64 y x86_64).

## 10. Limpieza

```bash
git -C $R worktree remove --force /tmp/orange-gualbe-sync-3.41.0
git -C $R worktree prune
rm -rf /tmp/og-sync-*.json /tmp/og-installers /tmp/orange-gualbe-env-* /tmp/orange-gualbe-np-latest
```

- La rama `sync/3.41.0` puede borrarse (`git branch -d`): ya está en `gualbe`.
- La copia del usuario debe acabar en `gualbe`, limpia e igual que
  `origin/gualbe`.

## 11. Mensaje final

Resumen breve en español:

- conflictos y cómo se resolvieron;
- tests (N, 0 fallos);
- decisiones de numpy, pandas y scikit-learn;
- cambios del benchmark de más del 15 %;
- enlace a la release y binarios adjuntos;
- lo que quede pendiente (p. ej. un workflow fallido o scikit-learn 1.10 sin
  verificar).

## Anexo: qué trae 3.41.0 sobre la base de gualbe.1 (`71c3613e0`)

| Qué | Relevancia para la fusión |
|---|---|
| Nomogram: softmax (#7331), ceros y ocultas, nombres visibles | Era un parche propio; ahora es oficial. Queda propio el ancho mínimo de la regla |
| Datasets: segfault (gh-7343) | Igual en las dos ramas |
| Excel: fila de indicadores vacía (gh-7276) | Se adopta la solución oficial (2.3) |
| scikit-learn `<1.10`; LinAlgError en Manifold Learning; LR más estable en un test | Se mantiene `<1.11` (2.1) |
| Sin topes de numpy y pandas; compatibilidad con numpy 2.4 y pandas 3 (`table.py`, `pandas_compat.py`, `owcsvimport.py`, `owpivot.py`) | Fase 4 |
| Traducción al castellano (`i18n/es/msgs.jaml`) | Sin conflicto. Las cadenas propias (p. ej. «Silhouette score») no tienen traducción; anótalo como pendiente opcional |
| Ficheros recientes en QSettings (File, Load Model, Load Distances) | Sin conflicto |
| Scatter Plot: agregación de regiones densas desactivada por defecto | Puede notarse en el benchmark de widgets |
| `tzdata`, cibuildwheel 4.3.5, Python 3.15 en CI | Sin efecto: los workflows oficiales están desactivados en el fork |
