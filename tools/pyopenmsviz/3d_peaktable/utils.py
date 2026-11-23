"""
Build one synchronised peakmap panel per .mzml file into a single HTML report.

The module is the library part of main.py: it reads the raw data of a folder of
.mzml files, labels the peaks that should be coloured and writes every
measurement as its own 3D peakmap into one self contained HTML file whose panels
share rotation and axis ranges.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyopenms as oms
import pyopenms_viz  # noqa: F401  registers the "ms_plotly" pandas plotting backend
from jinja2 import Environment, FileSystemLoader, select_autoescape
from plotly.colors import sample_colorscale
from plotly.offline import get_plotlyjs
from plotly.utils import PlotlyJSONEncoder


# ------------------------------------------------------------------ defaults
# Everything that only affects the look of the report lives here so that the
# functions below stay generic and main.py can expose it as command line options.
ANNOTATION = "target"
UNKNOWN_LABEL = "unknown"
COLORSCALE = "Plasma"

# Half widths of the mz / rt box that is coloured when colour_all is False.
MZ_TO_COLOUR_PPM = 5.0
RT_TO_COLOUR = 2.0

# One panel per measurement in a responsive CSS grid: panels are at least
# panel_width wide and as many as fit are put in a row, so panels_per_row is
# only an upper bound for narrow screens.
panel_width = 640
panel_height = 520
panels_per_row = 3
grid_gap = 12

# One panel is one WebGL context and Chromium only keeps about 16 of them per
# page, and Plotly.purge() does not hand a context back until its canvas is
# collected, so the number of panels drawn at the same time is a hard budget.
max_live_plots = 6
preload_pixels = 400

# Color bar of the shared intensity color scale in the header of the report.
color_bar_steps = 11
color_bar_ticks = 5

# Same default view the single file plot uses (see pyopenms_viz).
default_camera = dict(
    up=dict(x=0, y=0, z=1),
    center=dict(x=0, y=0, z=0),
    eye=dict(x=1.25, y=1.8, z=1.25),
)


# ------------------------------------------------------------------ report template
# The markup lives in templates/ so that it can be edited as plain HTML, python
# only hands the values below to it and never builds markup itself.
template_folder = Path(__file__).resolve().parent / "templates"
report_template = "peakmaps_report.html.j2"

jinja_environment = Environment(
    loader=FileSystemLoader(template_folder),
    # panel titles and captions come from file names, so they are escaped, the
    # plotly payload is handed over with | safe because it is raw javascript
    autoescape=select_autoescape(enabled_extensions=("html", "j2")),
)



def load_mzml_df(mzml_file, rt_range, mz_range):
    """
    Read one .mzml file into a long format DataFrame cut to the given range.

    The range is applied while the file is read, so a full run that does not fit
    into memory is still fine as long as the displayed window does.

    Inputs:
        mzml_file=path to the .mzml file to read
        rt_range=(min, max) retention time window to keep, in the time unit of the file
        mz_range=(min, max) m/z window to keep
    outputs:
        df=DataFrame with the columns rt, mz, intensity and ms_level, one row per peak
    """

    options = oms.PeakFileOptions()
    options.setRTRange(oms.DRange1(rt_range[0], rt_range[1]))
    options.setMZRange(oms.DRange1(mz_range[0], mz_range[1]))

    mzml_reader = oms.MzMLFile()
    mzml_reader.setOptions(options)

    experiment = oms.MSExperiment()
    mzml_reader.load(str(mzml_file), experiment)

    return experiment.to_df(long_format=True)



def load_mzml_folder(mzml_folder, rt_range, mz_range, pattern="*.mzml"):
    """
    Read every .mzml file of a folder into the list of panels.

    The same rt and mz range is used for every file, which is what makes the
    panels comparable and keeps the shared rotation identical.

    Inputs:
        mzml_folder=path to the folder containing the .mzml files
        rt_range=(min, max) retention time window to show in every panel
        mz_range=(min, max) m/z window to show in every panel
        pattern=glob that picks the files, use "*.mzML" on a case sensitive filesystem
    outputs:
        list_of_mzml_dfs=list of (file stem, DataFrame) tuples sorted by file name
    """

    files = sorted(Path(mzml_folder).glob(pattern))
    if not files:
        raise ValueError(f"no files matching '{pattern}' in {mzml_folder}")

    list_of_mzml_dfs = []

    for file in files:
        df = load_mzml_df(file, rt_range, mz_range)

        # An empty window has nothing to plot and would poison the shared ranges.
        if df.empty:
            print(f"Skipped {file.name}: no peaks in the displayed range")
            continue

        list_of_mzml_dfs.append((file.stem, df))

    if not list_of_mzml_dfs:
        raise ValueError(f"every file in {mzml_folder} is empty in the displayed range")

    return list_of_mzml_dfs



def colour_window(ion_mz, ion_rt, mz_to_colour_ppm=MZ_TO_COLOUR_PPM, rt_to_colour=RT_TO_COLOUR):
    """
    Bounds of the mz / rt box whose peaks get coloured.

    Inputs:
        ion_mz=m/z of the ion of interest
        ion_rt=retention time of the ion of interest in the time unit of the .mzml file
        mz_to_colour_ppm=half width of the box in m/z, given in ppm of ion_mz
        rt_to_colour=half width of the box in retention time, in the time unit of the file
    outputs:
        window=dict with the keys mz_min, mz_max, rt_min and rt_max of the box
    """
    
    mz_to_colour_delta = ion_mz * mz_to_colour_ppm * 1e-6

    return {
        "mz_min": ion_mz - mz_to_colour_delta,
        "mz_max": ion_mz + mz_to_colour_delta,
        "rt_min": ion_rt - rt_to_colour,
        "rt_max": ion_rt + rt_to_colour,
    }



def label_peaks(
    df,
    annotation=ANNOTATION,
    colour_all=True,
    ion_mz=None,
    ion_rt=None,
    mz_to_colour_ppm=MZ_TO_COLOUR_PPM,
    rt_to_colour=RT_TO_COLOUR,
    unknown_label=UNKNOWN_LABEL,
):
    """
    Add the label column that decides which peaks of a panel are coloured.

    With colour_all every displayed peak gets `annotation` and is therefore drawn
    with the shared intensity color scale. With colour_all=False only the peaks
    inside the mz / rt box around (ion_mz, ion_rt) are annotated and everything
    else keeps unknown_label, which build_peakmap_figure draws in lightgray.

    The DataFrame is labelled in place and returned as well.

    Inputs:
        df=DataFrame of one measurement as returned by load_mzml_df
        annotation=label given to every coloured peak
        colour_all=colour the whole displayed range instead of only the ion box
        ion_mz=m/z of the ion of interest, required when colour_all is False
        ion_rt=retention time of the ion of interest, required when colour_all is False
        mz_to_colour_ppm=half width of the coloured box in m/z, given in ppm of ion_mz
        rt_to_colour=half width of the coloured box in retention time
        unknown_label=label of every peak that stays grey
    outputs:
        df=the same DataFrame with the extra column "label"
    """

    df["label"] = unknown_label

    if colour_all:
        df["label"] = annotation
        return df

    if ion_mz is None or ion_rt is None:
        raise ValueError("ion_mz and ion_rt are required when colour_all is False")

    window = colour_window(ion_mz, ion_rt, mz_to_colour_ppm, rt_to_colour)

    # Both bounds of the box are inclusive.
    mask = (
        (df["mz"] >= window["mz_min"])
        & (df["mz"] <= window["mz_max"])
        & (df["rt"] >= window["rt_min"])
        & (df["rt"] <= window["rt_max"])
    )
    df.loc[mask, "label"] = annotation

    return df



def shared_color_range(list_of_mzml_dfs, unknown_label=UNKNOWN_LABEL):
    """
    Common log10 intensity range of every annotated peak of every measurement.

    One range for all panels is what makes colours comparable between files.

    Inputs:
        list_of_mzml_dfs=list of (name, DataFrame) tuples with a "label" column
        unknown_label=label of the peaks that are not coloured
    outputs:
        cmin=lowest log10(intensity + 1) over all annotated peaks
        cmax=highest log10(intensity + 1) over all annotated peaks
    """

    logs = [
        np.log10(df.loc[df["label"] != unknown_label, "intensity"].astype(float) + 1)
        for _, df in list_of_mzml_dfs
    ]
    logs = [values for values in logs if len(values)]
    if not logs:
        raise ValueError("No annotated peaks found in any DataFrame")

    all_logs = pd.concat(logs, ignore_index=True)
    cmin, cmax = float(all_logs.min()), float(all_logs.max())
    if cmin == cmax:  # avoid a zero width color scale
        cmax = cmin + 1

    return cmin, cmax



def shared_axis_ranges(list_of_mzml_dfs):
    """
    Common rt / mz / intensity range so that every panel shows the same window.

    Inputs:
        list_of_mzml_dfs=list of (name, DataFrame) tuples to combine into one range
    outputs:
        ranges=dict with the keys "rt", "mz" and "intensity", each holding a
        [minimum, maximum] pair, the intensity axis always starts at zero
    """

    frames = [df for _, df in list_of_mzml_dfs]
    full = pd.concat(frames, ignore_index=True)

    return {
        "rt": [float(full["rt"].min()), float(full["rt"].max())],
        "mz": [float(full["mz"].min()), float(full["mz"].max())],
        "intensity": [0.0, float(full["intensity"].max())],
    }



def panel_summary(df, unknown_label=UNKNOWN_LABEL):
    """
    Short caption of a panel with the number of peaks it shows.

    Inputs:
        df=DataFrame of one measurement with a "label" column
        unknown_label=label of the peaks that are not coloured
    outputs:
        summary=string "N peaks, M annotated" shown next to the panel title
    """

    annotated = int((df["label"] != unknown_label).sum())

    return f"{len(df):,} peaks, {annotated:,} annotated"



def stem_colors(z_values, cmin):
    """
    One color per coordinate of a scatter3d stem trace.

    pyopenms_viz draws every peak as a stem: base point, top point, separator.
    The color array has to be numeric everywhere, so separators get cmin and the
    base point repeats the color of its peak.

    Inputs:
        z_values=z coordinate of the trace, a list of intensities with None at
            every stem separator, taken from an already built peakmap trace
        cmin=lowest value of the shared color scale, used for the separators
    outputs:
        colors=log10(intensity + 1) for every coordinate of the trace, the same
            length as z_values so that plotly can map it onto the color scale
    """

    colors = []

    for index, z in enumerate(z_values):
        if z is None:
            colors.append(float(cmin))
            continue

        value = z
        is_stem_base = index % 3 == 0 and index + 1 < len(z_values)
        if is_stem_base and z_values[index + 1] is not None:
            value = z_values[index + 1]
        colors.append(float(np.log10(float(value) + 1)))

    return colors



def build_peakmap_figure(
    sample_df,
    color_range,
    panel_ranges,
    colorscale=COLORSCALE,
    unknown_label=UNKNOWN_LABEL,
    width=panel_width,
    height=panel_height,
    show_legend=False,
):
    """
    Peakmap of one measurement, ready to be dropped into its own panel.

    Inputs:
        sample_df=DataFrame of one measurement with a "label" column
        color_range=(cmin, cmax) shared log10 intensity range of the report
        panel_ranges=shared rt / mz / intensity ranges from shared_axis_ranges,
            None lets this panel autoscale its own axes
        colorscale=name of the plotly colorscale of the coloured peaks
        unknown_label=label of the peaks that are not coloured
        width=width of the panel in pixels
        height=height of the panel in pixels
        show_legend=draw the legend inside this panel
    outputs:
        fig=plotly Figure with one 3D stem trace per label
    """

    cmin, cmax = color_range

    fig = sample_df.plot(
        x="rt",
        y="mz",
        z="intensity",
        zlabel="Intensity",
        kind="peakmap",
        backend="ms_plotly",
        by="label",
        plot_3d=True,
        show_plot=False,
        height=height,
        width=width,
    )

    # Unknown peaks are flat lightgray, annotated ones follow the shared scale.
    for trace in fig.data:
        if trace.name == unknown_label:
            trace.line.update(color="lightgray")
        else:
            trace.line.update(
                color=stem_colors(list(trace.z), cmin),
                colorscale=colorscale,
                cmin=cmin,
                cmax=cmax,
                # The color scale is drawn once in the header of the report.
                showscale=False,
            )
        trace.showlegend = show_legend
        trace.legendgroup = str(trace.name)

    scene = dict(camera=dict(default_camera))
    if panel_ranges is not None:
        scene.update(
            xaxis_range=panel_ranges["rt"],
            yaxis_range=panel_ranges["mz"],
            zaxis_range=panel_ranges["intensity"],
        )

    fig.update_layout(
        title=None,
        showlegend=show_legend,
        legend=dict(orientation="h", yanchor="bottom", y=1, x=0),
        margin=dict(l=0, r=0, t=8, b=0),
        # The panel caption is plain HTML above the plot, so no extra space here.
        scene=scene,
    )
    fig.update_scenes(xaxis_title="rt", yaxis_title="mz", zaxis_title="Intensity")

    return fig



def drawn_intensity_max(figures):
    """
    Height of the tallest bar that the figures actually draw.

    Binning inside pyopenms_viz can draw stems below the raw peak heights, so
    the intensity axis has to follow the bars on the page instead of the data.

    Inputs:
        figures=list of plotly Figures of the panels, as built by build_peakmap_figure
    outputs:
        z_max=largest non-None z coordinate of any trace, the height of the
            tallest drawn bar of the report
    """

    z_values = [
        float(z)
        for figure in figures
        for trace in figure.data
        for z in (trace.z or [])
        if z is not None
    ]

    if not z_values:
        raise ValueError("no drawn bars in any figure")

    return max(z_values)



def apply_shared_intensity_range(figures, z_max):
    """
    Scale the intensity axis of every figure to the tallest drawn bar.

    Inputs:
        figures=list of plotly Figures of the panels, as built by build_peakmap_figure
        z_max=height of the tallest drawn bar, from drawn_intensity_max
    outputs:
        applied=z_max with a floor of 1.0, so that a window of zero height
            peaks still gets a visible axis; what the figures now show
    """

    applied = max(float(z_max), 1.0)

    for figure in figures:
        figure.update_scenes(zaxis_range=[0.0, applied])

    return applied



def drawn_color_range(figures, unknown_label=UNKNOWN_LABEL):
    """
    Common log10 intensity range of the coloured stems the figures draw.

    The stem colours are the values build_peakmap_figure writes into the color
    array of every coloured trace, so this only collects them. A stem separator
    has a z of None and is not drawn, so its fill value is skipped.

    Inputs:
        figures=list of plotly Figures of the panels, as built by build_peakmap_figure
        unknown_label=name of the trace whose peaks stay grey
    outputs:
        cmin=lowest log10(intensity + 1) of any drawn coloured stem
        cmax=highest log10(intensity + 1) of any drawn coloured stem
    """

    values = []

    for figure in figures:
        for trace in figure.data:
            colors = trace.line.color

            if trace.name == unknown_label or not isinstance(colors, (list, tuple)):
                continue

            values.extend(
                float(color)
                for z, color in zip(trace.z or [], colors)
                if z is not None
            )

    if not values:
        raise ValueError("no drawn coloured stems in any figure")

    cmin, cmax = min(values), max(values)
    if cmin == cmax:  # avoid a zero width color scale
        cmax = cmin + 1

    return cmin, cmax



def apply_shared_color_range(figures, color_range, unknown_label=UNKNOWN_LABEL):
    """
    Map the coloured stems of every figure onto the given color scale.

    The colour values of the stems stay as they are, only the endpoints of the
    mapping are rewritten, so every panel and the color bar of the header share
    the same scale.

    Inputs:
        figures=list of plotly Figures of the panels, as built by build_peakmap_figure
        color_range=(cmin, cmax) shared log10 intensity range, from drawn_color_range
        unknown_label=name of the trace whose peaks stay grey
    outputs:
        none=the figures are updated in place
    """

    cmin, cmax = color_range

    for figure in figures:
        for trace in figure.data:
            if trace.name == unknown_label or not isinstance(trace.line.color, (list, tuple)):
                continue

            trace.line.update(cmin=cmin, cmax=cmax)



def color_scale_ticks(cmin, cmax, ticks=color_bar_ticks):
    """
    Numeric labels of the color bar of the header.

    Inputs:
        cmin=lowest value of the color scale
        cmax=highest value of the color scale
        ticks=number of labels spread over the bar
    outputs:
        labels=list of dicts with the "position" of a label in percent of the bar
            and its "value" on the color scale, the template places them
    """
    return [
        {
            "position": 100 * i / (ticks - 1),
            "value": cmin + (cmax - cmin) * i / (ticks - 1),
        }
        for i in range(ticks)
    ]



def panel_payload(figure):
    """
    Plotly payload of one panel as it is embedded into the report.

    Inputs:
        figure=plotly Figure of a single panel
    outputs:
        payload=dict with the "data" and "layout" of the figure, without the
            fixed width because the grid defines how wide a panel is
    """
    spec = figure.to_plotly_json()
    layout = spec.get("layout", {})

    # The panel defines the width, plotly only needs the height.
    layout.pop("width", None)
    layout.pop("autosize", None)

    return {"data": spec.get("data", []), "layout": layout}



def default_axes(figure):
    """
    Axis ranges a panel starts with, taken from the first figure of the report.

    Inputs:
        figure=plotly Figure of the first panel
    outputs:
        axes=dict with an entry per scene axis holding either autorange or the
            explicit range, used by the "Reset all views" button
    """
    scene = figure.to_plotly_json().get("layout", {}).get("scene", {})
    axes = {}

    for key in ("xaxis", "yaxis", "zaxis"):
        axis = scene.get(key, {})
        if axis.get("range"):
            axes[key] = {"autorange": False, "range": list(axis["range"])}
        else:
            axes[key] = {"autorange": True}

    return axes



def write_synchronized_peakmaps_html(
    figures,
    titles,
    output_file,
    panel_meta=None,
    page_title="Peakmaps",
    color_range=None,
    colorscale=COLORSCALE,
    min_column_width=panel_width,
    panel_height=panel_height,
    panels_per_row=panels_per_row,
    max_live_plots=max_live_plots,
    camera=default_camera,
    steps=color_bar_steps,
    hint="Drag any plot to rotate all of them - shift drag pans, scroll zooms, double click resets.",
):
    """
    Write one figure per measurement into a single HTML file with shared views.

    The file is self contained, plotly itself is bundled into it, so it can be
    mailed or opened from a network share. Panels are created and destroyed while
    scrolling and the view of the panel the user touches is copied to the others.
    The markup of the page comes from templates/peakmaps_report.html.j2.

    Inputs:
        figures=plotly Figures of the panels, one per measurement
        titles=title of every panel, usually the file name without the extension
        output_file=path of the HTML file to write
        panel_meta=caption of every panel, e.g. from panel_summary, None for none
        page_title=title of the page, shown in the header and the browser tab
        color_range=(cmin, cmax) shared color scale to draw in the header, None
            leaves the color bar out
        colorscale=name of the plotly colorscale of the color bar
        min_column_width=smallest panel width in pixels before the grid wraps
        panel_height=height of every panel in pixels
        panels_per_row=largest number of panels next to each other
        max_live_plots=number of plotly graphs the browser may keep alive at once
        camera=default camera of every panel, also what "Reset all views" restores
        hint=one line help text under the title
    outputs:
        output_file=path of the written HTML file
    """
    if len(figures) != len(titles):
        raise ValueError("figures and titles have to be the same length")

    # one plotly payload and one caption per panel
    payloads = [panel_payload(figure) for figure in figures]
    panels = [
        {
            "name": str(title),
            "meta": "" if panel_meta is None else str(panel_meta[index]),
            "height": panel_height,
        }
        for index, title in enumerate(titles)
    ]

    if color_range is None:
        color_stops, color_ticks, color_label = [], [], "intensity"
    else:
        color_stops = sample_colorscale(colorscale, [i / (steps - 1) for i in range(steps)])
        # color_stops = color_scale_stops(colorscale)
        color_ticks = color_scale_ticks(*color_range)
        color_label = "log10(intensity + 1)"

    config = {
        "figures": payloads,
        "camera": camera,
        "defaultAxes": default_axes(figures[0]) if figures else {},
        "axes": ["xaxis", "yaxis", "zaxis"],
        "syncRotation": True,
        "syncAxes": True,
        "maxLive": max_live_plots,
        "preload": preload_pixels,
    }

    # plotly payloads hold numpy arrays, and "</" is escaped so that no peak name
    # can close the script tag it is written into
    config_json = json.dumps(config, cls=PlotlyJSONEncoder).replace("</", "<\\/")

    html = jinja_environment.get_template(report_template).render(
        page_title=page_title,
        hint=hint,
        panels=panels,
        color_label=color_label,
        color_stops=color_stops,
        color_ticks=color_ticks,
        min_column_width=min_column_width,
        panels_per_row=panels_per_row,
        grid_gap=grid_gap,
        plotly_js=get_plotlyjs(),
        config_json=config_json,
    )

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html, encoding="utf8")

    return output_file
