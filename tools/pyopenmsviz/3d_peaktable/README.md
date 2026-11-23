# Synchronised 3D peakmaps for a folder of .mzml files

`main.py` reads every `.mzml` file of a folder, cuts it to the retention time and
m/z window you ask for and writes **one HTML file with one 3D peakmap panel per
measurement**. All panels share

- the same rotation (drag one plot, every plot follows),
- the same rt / m/z / intensity window,
- the same `log10(intensity + 1)` colour scale, which is drawn once in the header.

## Files

| file | what it is |
| --- | --- |
| `main.py` | command line entry point, argument parser and the build loop |
| `utils.py` | all plotting helpers: reading, labelling, colours, panels, HTML report |
| `templates/peakmaps_report.html.j2` | markup and CSS of the report, rendered with Jinja |
| `templates/peakmaps_report.js` | the browser script that keeps the panels in sync |
| `tests.py` | pytest suite for the helpers, the parser and one full end to end run |
| `test-data/` | three dummy `.mzml` files (about 0.5 MB in total) used by the tests |
| `OLD/make_test_data.py` | subsamples a real run into the small dummy files in `test-data/` |
| `OLD/` | the notebook this tool came from, the original reports and the data generator |

## Requirements

Tested in the conda env `pyopenms` with Python 3.12, `pyopenms` 3.7.0.dev,
`pyopenms_viz` 1.0.1, `pandas` 3.0, `plotly` 5.24, `jinja2` 3.1 and `numpy` 2.4.
`pyopenms_viz` registers the `ms_plotly` backend for `pandas.plot`, which is what draws
the 3D stems and `pytest`.

## Usage

Colour **every peak** that is inside the displayed window (`--colour-all` is the default):

```bash
python main.py --mzml_folder "path/to/mzml_folder" --rt-min 457 --rt-max 460 --mz-min 325 --mz-max 332
```

Colour **only the ion you select** and draw everything else lightgray
(`--no-colour-all` plus the ion and the half widths of its box):

```bash
python main.py --mzml_folder "path/to/mzml_folder" \
    --rt-min 457 --rt-max 460 --mz-min 325 --mz-max 332 \
    --no-colour-all \
    --ion-mz 329.3203 --ion-rt 458.6873 \
    --mz-to-colour-ppm 5 --rt-to-colour 2 \
    --annotation "Cholesterol 1TMS" \
    --output "Cholesterol 1TMS_peakmaps.html"
```

Every setting is an option, the folder and the four range bounds have to be given.

The report is written next to the terminal you run this from unless `--output` says
otherwise, and the browser can open it offline because plotly is bundled into the file.

### Options

| option | meaning | default |
| --- | --- | --- |
| `--mzml_folder` | folder with the `.mzml` files, one panel per file | required |
| `--rt-min`, `--rt-max` | retention time window every panel shows, in the time unit of the file | required |
| `--mz-min`, `--mz-max` | m/z window every panel shows | required |
| `--pattern` | glob that picks the files, use `*.mzML` if your files are named that way | `*.mzml` |
| `--colour-all` / `--no-colour-all` | colour the whole displayed window, or only the box around the ion below | `--colour-all` |
| `--ion-mz`, `--ion-rt` | centre of the box to colour, required with `--no-colour-all` | none |
| `--mz-to-colour-ppm` | half width of that box in m/z, in ppm of `--ion-mz` | `5.0` |
| `--rt-to-colour` | half width of that box in retention time | `2.0` |
| `--annotation` | name of the coloured region, it is also the legend entry | `target` |
| `--title` | title of the page | `<annotation> in raw data` |
| `--output` | HTML file to write | `<annotation>_peakmaps.html` in the current folder |
| `--colorscale` | plotly colorscale of the coloured peaks | `Plasma` |
| `--panel-width`, `--panel-height`, `--panels-per-row` | size of one panel and how many are put next to each other | `640`, `520`, `3` |
| `--max-live-plots` | how many plotly graphs the browser may keep alive at once, see the WebGL note below | `6` |

### One panel, one WebGL context

Every panel is one plotly `scene3D` graph and every such graph holds one WebGL
context. Chromium keeps only about **16 contexts per page** and takes the oldest one
away when the limit is crossed, even from a panel that is still on screen. Plotly then
notices the loss and asks for a new context once per animation frame, which takes the
context of the next panel, so a report that simply builds every panel freezes the page
after about fifteen of them.

Three things follow from that, all in `templates/peakmaps_report.js`:

- at most `--max-live-plots` panels are drawn at a time, a slot is freed **before** the
  next panel is built and the panel closest to the middle of the window is built first,
- one panel is built per animation frame, so a fast scroll costs one build (~0.2 s)
  instead of one build per panel that happened to come into view,
- throwing a panel away hands its context back on purpose
  (`canvas.getContext(...).getExtension("WEBGL_lose_context").loseContext()`), because
  `Plotly.purge()` removes the graph but the browser counts the context until the canvas
  is collected, which lags far behind scrolling.

`--max-live-plots` is a hard limit, not a hint. Raising it above about 10 is only safe
on a machine with a lot of graphics memory and a browser with a higher limit; measured on
an Intel UHD 620, 30 panels with the default of 6 never reach the limit, keep exactly 6
contexts alive and log no `Too many active WebGL contexts` warning at all.

### What gets coloured

`utils.label_peaks` writes the `label` column that `ms_plotly` groups traces by.

- `--colour-all`: every peak of the displayed window gets `--annotation`, so the whole
  window is drawn with the shared colour scale.
- `--no-colour-all`: only the peaks inside the m/z and retention time box around
  `--ion-mz` / `--ion-rt` get `--annotation`, both bounds inclusive. Everything else
  keeps the label `unknown` and is drawn flat lightgray.

The half widths used to be called `rt_tol` and `mz_tol_ppm` because they described
instrument tolerances. They are now `rt_to_colour` and `mz_to_colour_ppm` because they
simply describe the region that should be coloured, whatever the reason for it is.

## Peak aggregation

Panels with more than 2500 peaks in the displayed window are aggregated so the
report stays responsive: `pyopenms_viz` divides the rt / m/z plane into a 50 x 50
grid and every cell is drawn as one stem at the cell centre whose height is the
mean intensity of the peaks of that cell. The stems are grouped by label, so the
coloured and the grey peaks of a cell are averaged separately, and the same
window can therefore be drawn with different bar heights depending on
`--colour-all` / `--no-colour-all`. Individual peaks may not be visible, and bar
heights are cell averages rather than exact peak intensities.

Because of that, the intensity axis and the shared colour scale follow the bars
that are actually drawn: the axis top is the tallest drawn bar of the report and
the colour scale spans the drawn coloured stems. Both can differ between the two
colouring modes and from the raw peak intensities.

## Tests

The tests read raw data from `test-data/`, which holds three committed subsamples of
around the tested window: `dummy_peak_a.mzml` and `dummy_peak_b.mzml` both contain the
tested ion, `dummy_blank.mzml` contains nothing so that the "no peaks in this window"
path is covered as well. They are part of the project, so nothing has to be generated
before running the suite; `OLD/make_test_data.py` subsamples a longer run into those
files and is only needed when a test wants a different window or ion.

Run the suite with

```bash
pytest tests.py -v
```

`tests.py` covers reading and windowing, the ion box including its borders, the shared
colour and axis ranges, the stem colours, one built panel, the written HTML including the
WebGL budget and both ways of running `main.py`. It takes about fifteen seconds; the tests
that read raw data are skipped with a hint if `test-data/` is missing.

## Report features worth knowing

- Panels are created while you scroll and thrown away again when they leave the page,
  never more than `--max-live-plots` of them at a time, so a folder with a hundred
  measurements does not run out of WebGL contexts.
- If the browser takes a context away anyway, that panel shows a one line note instead of
  a half dead graph and is drawn again when you scroll back to it.
- The header has a filter for the file names, checkboxes for sync rotation and sync
  axes, a *Reset all views* button and the shared colour bar.
- The intensity axis is scaled to the tallest bar the panels actually draw and the
  colour scale to the drawn coloured stems, see *Peak aggregation* above.
- The panel that you are dragging is outlined in blue, the caption of every panel
  shows how many peaks it holds and how many of them are annotated.
- `window.peakmapDebug()` in the browser console returns the shared camera, the panels
  that are currently rendered, the panels the viewport asked for and the live budget.
