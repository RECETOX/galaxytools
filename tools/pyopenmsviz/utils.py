"""Shared utility functions for pyopenmsviz interactive peak table plotting."""

import math
import colorsys
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial
import glob
import json
import os
import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from jinja2 import Environment, FileSystemLoader
from plotly.subplots import make_subplots
from pyteomics import mzml


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def mzml_to_df(file_path):
    """Convert mzML spectra to a long DataFrame with rt/mz/intensity columns."""
    records = []
    with mzml.MzML(file_path) as reader:
        for spectrum in reader:
            scan = spectrum["scanList"]["scan"][0]
            rt = scan.get("scan start time")
            mz_array = spectrum.get("m/z array", [])
            intensity_array = spectrum.get("intensity array", [])
            for mz_value, intensity_value in zip(mz_array, intensity_array):
                records.append(
                    {
                        "id": spectrum["id"],
                        "ms_level": spectrum["ms level"],
                        "rt": rt,
                        "mz": mz_value,
                        "intensity": intensity_value,
                    }
                )
    return pd.DataFrame(records)


loaders = {
    ".parquet": pd.read_parquet,
    ".csv": pd.read_csv,
    ".mzml": mzml_to_df,
    ".tsv": lambda x: pd.read_csv(x, sep="\t"),
    ".tabular": lambda x: pd.read_csv(x, sep="\t"),
}


def chunk_files(file_path, chunk_size):
    """Collect and chunk sample files for subplot pagination."""
    extensions = ["*.parquet", "*.csv", "*.mzml"]
    file_list = []
    for ext in extensions:
        file_list.extend(glob.glob(f"{file_path}/{ext}"))

    def numeric_sort_key(path):
        name = os.path.splitext(os.path.basename(path))[0]
        match = re.match(r"^(\d+)", name)
        return int(match.group(1)) if match else float("inf")

    file_list = sorted(file_list, key=numeric_sort_key)

    chunks = []
    for i in range(0, len(file_list), chunk_size):
        chunk = file_list[i : i + chunk_size]
        chunk_tuples = [(os.path.splitext(os.path.basename(f))[0], f) for f in chunk]
        while len(chunk_tuples) < chunk_size:
            chunk_tuples.append((None, None))
        chunks.append(chunk_tuples)
    return chunks


def compute_global_axes(file_path, threshold, signal_value):
    """Compute synchronized RT/mz axis ranges and global color maximum."""
    all_rt = []
    all_mz = []
    all_cmax = []

    for file in glob.glob(f"{file_path}/*"):
        loader = loaders.get(os.path.splitext(file)[1].lower())
        if loader is None:
            continue

        df = loader(file)

        all_rt += [df["rt"].min(), df["rt"].max()]
        all_mz += [df["mz"].min(), df["mz"].max()]

        above = df.loc[df[signal_value] >= threshold, signal_value]
        if not above.empty:
            all_cmax.append(above.max())

    rt_min, rt_max = min(all_rt), max(all_rt)
    mz_min, mz_max = min(all_mz), max(all_mz)
    rt_pad = (rt_max - rt_min) * 0.02
    mz_pad = (mz_max - mz_min) * 0.02
    global_cmax = np.log10(max(all_cmax))

    return rt_min, rt_max, mz_min, mz_max, rt_pad, mz_pad, global_cmax


def peak_table_multiplot(sample_groups, threshold, global_axes, signal_value):
    """Render one page of unaligned scatter subplots."""
    rt_min, rt_max, mz_min, mz_max, rt_pad, mz_pad, global_cmax = global_axes

    n = len(sample_groups)
    ncols = math.ceil(math.sqrt(n))
    nrows = math.ceil(n / ncols)

    subplot_titles = [name if name is not None else "" for name, _ in sample_groups]

    fig = make_subplots(
        rows=nrows,
        cols=ncols,
        subplot_titles=subplot_titles,
        horizontal_spacing=0.08,
        vertical_spacing=0.12,
    )

    for i, (name, group) in enumerate(sample_groups):
        row = i // ncols + 1
        col = i % ncols + 1

        if name is None:
            fig.add_trace(
                go.Scattergl(
                    x=[],
                    y=[],
                    mode="markers",
                    showlegend=False,
                    hoverinfo="skip",
                ),
                row=row,
                col=col,
            )
            continue

        under_threshold = group[group[signal_value] < threshold]
        fig.add_trace(
            go.Scattergl(
                x=under_threshold["rt"],
                y=under_threshold["mz"],
                mode="markers",
                marker=dict(color="lightgray", size=4, opacity=0.7),
                name=f"Below {threshold}",
                legendgroup="below",
                showlegend=(i == 0),
                hovertemplate="rt: %{x:.2f}<br>mz: %{y:.4f}<extra>Below threshold</extra>",
                customdata=(
                    under_threshold[["cluster"]].values
                    if "cluster" in under_threshold.columns
                    else np.full((len(under_threshold), 1), -1)
                ),
            ),
            row=row,
            col=col,
        )

    cmin = np.log10(threshold)
    last_real_idx = max(i for i, (name, _) in enumerate(sample_groups) if name is not None)

    for i, (name, group) in enumerate(sample_groups):
        row = i // ncols + 1
        col = i % ncols + 1
        show_colorbar = i == last_real_idx

        if name is None:
            continue

        above_threshold = group[group[signal_value] >= threshold].sort_values(
            signal_value, ascending=True
        )
        if len(above_threshold) == 0:
            continue

        log_area = np.log10(above_threshold[signal_value])
        tick_vals = np.linspace(cmin, global_cmax, 6)

        if signal_value == "area":
            fig.add_trace(
                go.Scattergl(
                    x=above_threshold["rt"],
                    y=above_threshold["mz"],
                    mode="markers",
                    error_x=dict(
                        type="data",
                        array=above_threshold["sd2"].values,
                        arrayminus=above_threshold["sd1"].values,
                        visible=True,
                        color="rgba(150,150,150,0.7)",
                        thickness=1,
                        width=2,
                    ),
                    marker=dict(
                        color=log_area,
                        colorscale="magma",
                        cmin=cmin,
                        cmax=global_cmax,
                        size=5,
                        sizemin=4,
                        opacity=0.75,
                        showscale=show_colorbar,
                        colorbar=(
                            dict(
                                title=signal_value.capitalize(),
                                tickvals=tick_vals,
                                ticktext=[f"{10 ** v:.0e}" for v in tick_vals],
                                x=1.02,
                            )
                            if show_colorbar
                            else None
                        ),
                    ),
                    name=f"Above {threshold}",
                    legendgroup="above",
                    showlegend=(i == 0),
                    hovertemplate=(
                        "rt: %{x:.2f}<br>mz: %{y:.4f}<br>cluster: %{customdata[0]}<br>"
                        + signal_value
                        + ": %{customdata[1]:.0f}<extra></extra>"
                    ),
                    customdata=(
                        above_threshold[["cluster", signal_value]]
                        if "cluster" in above_threshold.columns
                        else above_threshold[[signal_value]].assign(cluster=-1)
                    ),
                ),
                row=row,
                col=col,
            )
        else:
            fig.add_trace(
                go.Scattergl(
                    x=above_threshold["rt"],
                    y=above_threshold["mz"],
                    mode="markers",
                    error_x=dict(
                        type="data",
                        visible=True,
                        color="rgba(150,150,150,0.7)",
                        thickness=1,
                        width=2,
                    ),
                    marker=dict(
                        color=log_area,
                        colorscale="magma",
                        cmin=cmin,
                        cmax=global_cmax,
                        size=5,
                        sizemin=4,
                        opacity=0.75,
                        showscale=show_colorbar,
                        colorbar=(
                            dict(
                                title=signal_value.capitalize(),
                                tickvals=tick_vals,
                                ticktext=[f"{10 ** v:.0e}" for v in tick_vals],
                                x=1.02,
                            )
                            if show_colorbar
                            else None
                        ),
                    ),
                    name=f"Above {threshold}",
                    legendgroup="above",
                    showlegend=(i == 0),
                    hovertemplate=(
                        "rt: %{x:.2f}<br>mz: %{y:.4f}<br>cluster: %{customdata[0]}<br>"
                        + signal_value
                        + ": %{customdata[1]:.0f}<extra></extra>"
                    ),
                    customdata=(
                        above_threshold[["cluster", signal_value]]
                        if "cluster" in above_threshold.columns
                        else above_threshold[[signal_value]].assign(cluster=-1)
                    ),
                ),
                row=row,
                col=col,
            )

    fig.update_xaxes(range=[rt_min - rt_pad, rt_max + rt_pad])
    fig.update_yaxes(range=[mz_min - mz_pad, mz_max + mz_pad])

    for i in range(n):
        x_key = "xaxis" if i == 0 else f"xaxis{i + 1}"
        y_key = "yaxis" if i == 0 else f"yaxis{i + 1}"
        fig.update_layout(
            **{
                x_key: dict(matches="x", range=[rt_min - rt_pad, rt_max + rt_pad]),
                y_key: dict(matches="y", range=[mz_min - mz_pad, mz_max + mz_pad]),
            }
        )

    for c in range(1, ncols + 1):
        fig.update_xaxes(title_text="rt (sec)", row=nrows, col=c)
    for r in range(1, nrows + 1):
        fig.update_yaxes(title_text="m/z", row=r, col=1)

    fig.update_layout(
        width=None,
        height=500 * nrows,
        template="plotly_white",
        legend=dict(x=1.05, y=0.5),
    )

    trace_map = {}
    for i in range(n):
        if sample_groups[i][0] is None:
            continue
        trace_map[i] = {"below": i * 2, "above": i * 2 + 1}

    is_clustered = any(
        "cluster" in group.columns
        for _, group in sample_groups
        if group is not None and not isinstance(group, type(None))
    )

    return fig, trace_map, is_clustered


def render_single_chunk_worker(chunk_data, global_axes, title, threshold, signal_value):
    """Render one unaligned chunk in a worker process."""
    chunk_idx, chunk_files_tuples = chunk_data
    sample_groups = []

    for name, fpath in chunk_files_tuples:
        if name is None:
            sample_groups.append((None, None))
        else:
            loader = loaders.get(os.path.splitext(fpath)[1])
            if loader is None:
                continue
            df = loader(fpath)
            sample_groups.append((name, df))

    fig, trace_map, is_clustered = peak_table_multiplot(
        sample_groups=sample_groups,
        threshold=threshold,
        global_axes=global_axes,
        signal_value=signal_value,
    )
    return chunk_idx, fig.to_json(), trace_map, is_clustered


def render_chunks_parallel(chunks, global_axes, title, threshold, signal_value, max_workers=None):
    """Render all unaligned chunks in parallel."""
    if max_workers is None:
        max_workers = min(len(chunks), os.cpu_count() or 4)

    figures = [None] * len(chunks)
    trace_maps = [None] * len(chunks)
    is_clustered_flags = []

    chunk_data_list = [(i, chunk) for i, chunk in enumerate(chunks)]
    worker_func = partial(
        render_single_chunk_worker,
        global_axes=global_axes,
        title=title,
        threshold=threshold,
        signal_value=signal_value,
    )

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(worker_func, chunk_data_list)
        for result in results:
            chunk_idx, fig, trace_map, is_clustered = result
            figures[chunk_idx] = fig
            trace_maps[chunk_idx] = trace_map
            is_clustered_flags.append(is_clustered)

    return figures, trace_maps, any(is_clustered_flags)


def generate_html(figures, output_file, title="Peak Table Interactive Plots", trace_maps=None, is_clustered=False):
    """Render HTML for unaligned pipeline from serialized figure JSON."""
    figure_data_dict = {str(i): json.loads(fig) for i, fig in enumerate(figures)}
    trace_maps_dict = {str(i): tm for i, tm in enumerate(trace_maps or [])}

    env = Environment(loader=FileSystemLoader(SCRIPT_DIR))
    template = env.get_template("template_pipeline_1.html")

    html_content = template.render(
        title=title,
        total_chunks=len(figures),
        is_clustered=is_clustered,
        figure_data=figure_data_dict,
        trace_maps_data=trace_maps_dict,
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)


def load_markers(markers_path):
    """Load marker table in supported tabular format."""
    ext = os.path.splitext(markers_path)[1].lower()
    loader = loaders.get(ext)
    if loader is None:
        raise ValueError(f"Unsupported marker format: {ext}")
    return loader(markers_path)


def load_file(filename: str, markers, mz_tol_ppm: float, rt_tol_s: float):
    """Load one raw file and annotate matching rows to marker compounds."""
    ext = os.path.splitext(filename)[1].lower()
    loader = loaders.get(ext)
    if loader is None:
        raise ValueError(f"Unsupported format: {ext}")

    eics = loader(filename)
    eics["Annotation"] = "Unknown"
    eics.sort_values(["rt"], inplace=True)

    for _, marker in markers.iterrows():
        mask = (
            (eics["Annotation"] == "Unknown")
            & (eics["mz"] >= marker["mz"] - marker["mz"] * mz_tol_ppm * 1e-06)
            & (eics["mz"] <= marker["mz"] + marker["mz"] * mz_tol_ppm * 1e-06)
            & (eics["rt"] >= marker["rt"] - rt_tol_s)
            & (eics["rt"] <= marker["rt"] + rt_tol_s)
        )
        eics.loc[mask, "Annotation"] = marker["Compound Name"]

    return eics[eics["Annotation"] != "Unknown"]


def single_sample_eic(args):
    """Compute EIC traces for one sample."""
    fpath, sample, markers_records, mz_tol_ppm, rt_tol_s = args
    markers = pd.DataFrame(markers_records)

    compound_ions = {}
    for _, marker in markers.iterrows():
        name = marker["Compound Name"]
        if name not in compound_ions:
            compound_ions[name] = []
        compound_ions[name].append(float(marker["mz"]))
    for name in compound_ions:
        compound_ions[name].sort()

    try:
        eics = load_file(fpath, markers, mz_tol_ppm, rt_tol_s)
    except Exception as e:
        print(f"[EIC] Skipping {fpath}: {e}")
        return sample, {}

    sample_dict = {}
    for compound, cdf in eics.groupby("Annotation"):
        compound_dict = {}
        for pos, mz in enumerate(compound_ions.get(compound, [])):
            mz_lo = mz * (1 - mz_tol_ppm * 1e-6)
            mz_hi = mz * (1 + mz_tol_ppm * 1e-6)
            ion_df = cdf[(cdf["mz"] >= mz_lo) & (cdf["mz"] <= mz_hi)]
            if ion_df.empty:
                continue
            trace = ion_df.groupby("rt", sort=True)["intensity"].sum().reset_index()
            compound_dict[str(pos)] = {
                "mz": mz,
                "rt": trace["rt"].tolist(),
                "intensity": trace["intensity"].tolist(),
            }
        if compound_dict:
            sample_dict[compound] = compound_dict

    return sample, sample_dict


def compute_eic_data(raw_input_path: str, markers: pd.DataFrame, sample_names: list[str], mz_tol_ppm: float, rt_tol_s: float, cores_to_use: int) -> dict:
    """Compute EIC traces in parallel for all matching samples."""
    supported_ext = {".mzml", ".parquet", ".csv"}
    if cores_to_use > 0:
        max_workers = cores_to_use
    else:
        max_workers = max(1, (os.cpu_count() or 4) // 2)

    raw_files = {}
    for fname in os.listdir(raw_input_path):
        stem, ext = os.path.splitext(fname)
        if ext.lower() in supported_ext and stem in sample_names:
            raw_files[os.path.join(raw_input_path, fname)] = stem

    markers_records = markers.to_dict("records")
    args_list = [
        (fpath, sample, markers_records, mz_tol_ppm, rt_tol_s)
        for fpath, sample in raw_files.items()
    ]

    eic_data = {}
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(single_sample_eic, args): args[1] for args in args_list}
        for future in as_completed(futures):
            sample_name = futures[future]
            try:
                sample, sample_dict = future.result()
                eic_data[sample] = sample_dict
                print(f"[EIC] Completed {sample_name}")
            except Exception as e:
                print(f"[EIC] Error in {sample_name}: {e}")

    return eic_data


def load_aligned_tables(intensity_path, rt_path, metadata_path, annotation_path, show_only_annotated=None):
    """Load aligned table inputs and emit per-sample feature tables."""
    if show_only_annotated is None:
        raise ValueError("Show_only_annotated parameter is required")
    if annotation_path is None:
        raise ValueError("No annotation table provided. Please provide annotation_path.")

    if intensity_path.endswith(".parquet") and rt_path.endswith(".parquet") and metadata_path.endswith(".parquet"):
        intensity_df = pd.read_parquet(intensity_path)
        rt_df = pd.read_parquet(rt_path)
        metadata_df = pd.read_parquet(metadata_path)
        annotation_df = pd.read_table(annotation_path)
    elif intensity_path.endswith(".csv") and rt_path.endswith(".csv") and metadata_path.endswith(".csv"):
        intensity_df = pd.read_csv(intensity_path)
        rt_df = pd.read_csv(rt_path)
        metadata_df = pd.read_csv(metadata_path)
        annotation_df = pd.read_table(annotation_path)
    else:
        raise ValueError("Aligned intensity/rt/metadata inputs must be all .csv or all .parquet")

    sample_cols = [c for c in intensity_df.columns if c != "id"]

    def numeric_sort_key(name):
        match = re.match(r"^(\d+)", name)
        return int(match.group(1)) if match else float("inf")

    sample_cols = sorted(sample_cols, key=numeric_sort_key)
    annotation_map = annotation_df.set_index("id")["Compound Name"].to_dict()

    sample_dfs = []
    for sample in sample_cols:
        present_ids = metadata_df.loc[metadata_df[sample] == 1, "id"]
        df = pd.DataFrame()
        df["id"] = present_ids

        df = df.merge(metadata_df[["id", "mz"]], on="id", how="left")
        df = df.merge(rt_df[["id", sample]].rename(columns={sample: "rt"}), on="id", how="left")
        df = df.merge(
            intensity_df[["id", sample]].rename(columns={sample: "intensity"}),
            on="id",
            how="left",
        )

        df["compound_name"] = df["id"].map(annotation_map).fillna("")
        if show_only_annotated == 1:
            df = df[df["compound_name"] != ""]

        df = df.dropna(subset=["rt", "mz", "intensity"])
        sample_dfs.append((sample, df))

    return sample_dfs, annotation_df


def chunk_samples(sample_dfs, chunk_size=9):
    """Chunk per-sample aligned data for subplot pagination."""
    chunks = []
    for i in range(0, len(sample_dfs), chunk_size):
        chunk = sample_dfs[i : i + chunk_size]
        while len(chunk) < chunk_size:
            chunk.append((None, None))
        chunks.append(chunk)
    return chunks


def peak_table_multiplot_aligned(sample_groups, threshold, global_axes, annotation_df):
    """Render one page of aligned scatter subplots."""
    rt_min, rt_max, mz_min, mz_max, rt_pad, mz_pad, global_cmax = global_axes

    n = len(sample_groups)
    ncols = math.ceil(math.sqrt(n))
    nrows = math.ceil(n / ncols)

    subplot_titles = [name if name is not None else "" for name, _ in sample_groups]
    fig = make_subplots(
        rows=nrows,
        cols=ncols,
        subplot_titles=subplot_titles,
        horizontal_spacing=0.08,
        vertical_spacing=0.12,
    )

    cmin = np.log10(threshold) if threshold > 0 else 0
    tick_vals = np.linspace(cmin, global_cmax, 6)
    last_real_idx = max(i for i, (name, _) in enumerate(sample_groups) if name is not None)
    trace_map = {}

    for i, (name, df) in enumerate(sample_groups):
        row = i // ncols + 1
        col = i % ncols + 1
        show_colorbar = i == last_real_idx

        if name is None:
            fig.add_trace(
                go.Scattergl(
                    x=[],
                    y=[],
                    mode="markers",
                    showlegend=False,
                    hoverinfo="skip",
                ),
                row=row,
                col=col,
            )
            continue

        under_threshold = df[df["intensity"] < threshold]
        above_threshold = df[df["intensity"] >= threshold].sort_values("intensity", ascending=True)

        below_trace_idx = len(fig.data)
        fig.add_trace(
            go.Scattergl(
                x=under_threshold["rt"],
                y=under_threshold["mz"],
                mode="markers",
                marker=dict(color="lightgray", size=4, opacity=0.7),
                name="Below threshold",
                legendgroup="below",
                showlegend=(i == 0),
                customdata=under_threshold[["id", "compound_name"]].values,
                hovertemplate="rt: %{x:.2f}<br>mz: %{y:.4f}<br>id: %{customdata[0]}<br>%{customdata[1]}<extra>Below threshold</extra>",
            ),
            row=row,
            col=col,
        )

        above_trace_idx = len(fig.data)
        log_intensity = np.log10(above_threshold["intensity"].clip(lower=1e-10))
        fig.add_trace(
            go.Scattergl(
                x=above_threshold["rt"],
                y=above_threshold["mz"],
                mode="markers",
                marker=dict(
                    color=log_intensity,
                    colorscale="magma",
                    cmin=cmin,
                    cmax=global_cmax,
                    size=5,
                    opacity=0.75,
                    showscale=show_colorbar,
                    colorbar=(
                        dict(
                            title="Intensity",
                            tickvals=tick_vals,
                            ticktext=[f"{10 ** v:.0e}" for v in tick_vals],
                            x=1.02,
                        )
                        if show_colorbar
                        else None
                    ),
                ),
                name="Above threshold",
                legendgroup="above",
                showlegend=(i == 0),
                customdata=above_threshold[["id", "compound_name", "intensity"]].values,
                hovertemplate="rt: %{x:.2f}<br>mz: %{y:.4f}<br>id: %{customdata[0]}<br>%{customdata[1]}<br>intensity: %{customdata[2]:.0f}<extra></extra>",
            ),
            row=row,
            col=col,
        )

        trace_map[i] = {"below": below_trace_idx, "above": above_trace_idx}

    fig.update_xaxes(range=[rt_min - rt_pad, rt_max + rt_pad])
    fig.update_yaxes(range=[mz_min - mz_pad, mz_max + mz_pad])

    for i in range(n):
        x_key = "xaxis" if i == 0 else f"xaxis{i + 1}"
        y_key = "yaxis" if i == 0 else f"yaxis{i + 1}"
        fig.update_layout(
            **{
                x_key: dict(matches="x", range=[rt_min - rt_pad, rt_max + rt_pad]),
                y_key: dict(matches="y", range=[mz_min - mz_pad, mz_max + mz_pad]),
            }
        )

    for c in range(1, ncols + 1):
        fig.update_xaxes(title_text="rt (sec)", row=nrows, col=c)
    for r in range(1, nrows + 1):
        fig.update_yaxes(title_text="m/z", row=r, col=1)

    fig.update_layout(
        width=None,
        height=500 * nrows,
        template="plotly_white",
        legend=dict(x=1.05, y=0.5),
    )

    return fig, trace_map


def compute_global_axes_aligned(sample_dfs, threshold):
    """Compute synchronized RT/mz axis ranges for aligned pipeline."""
    all_rt, all_mz, all_cmax = [], [], []

    for name, df in sample_dfs:
        if name is None or df is None:
            continue
        all_rt += [df["rt"].min(), df["rt"].max()]
        all_mz += [df["mz"].min(), df["mz"].max()]
        above = df.loc[df["intensity"] >= threshold, "intensity"]
        if not above.empty:
            all_cmax.append(above.max())

    rt_min, rt_max = min(all_rt), max(all_rt)
    mz_min, mz_max = min(all_mz), max(all_mz)
    rt_pad = (rt_max - rt_min) * 0.02
    mz_pad = (mz_max - mz_min) * 0.02
    global_cmax = np.log10(max(all_cmax))

    return rt_min, rt_max, mz_min, mz_max, rt_pad, mz_pad, global_cmax


def render_chunks_aligned(chunks, global_axes, title, threshold, annotation_df):
    """Render all aligned chunks sequentially."""
    figures = []
    trace_maps = []
    for chunk in chunks:
        fig, trace_map = peak_table_multiplot_aligned(
            sample_groups=chunk,
            threshold=threshold,
            global_axes=global_axes,
            annotation_df=annotation_df,
        )
        figures.append(fig)
        trace_maps.append(trace_map)

    return figures, trace_maps


def hsv_hex(h, s, v):
    """Convert HSV values in [0, 1] range into uppercase HEX color."""
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, float(s), float(v))
    return "#{:02X}{:02X}{:02X}".format(round(r * 255), round(g * 255), round(b * 255))


def build_color_maps(annotation_df):
    """Build deterministic colors for compounds and their ions."""
    compounds = []
    for compound, grp in annotation_df.groupby("Compound Name"):
        if pd.isna(compound) or not str(compound).strip():
            continue
        rows = (
            grp[["id", "mz"]]
            .dropna()
            .drop_duplicates(subset=["id"])
            .sort_values(["mz", "id"])
        )
        compounds.append((str(compound), rows))

    compounds.sort(key=lambda x: x[0].lower())
    n = len(compounds)
    hues = (0.5 + np.arange(n) / 30) % 1.0

    compound_colors = {}
    ion_colors = {}
    ion_colors_by_pos = {}

    for (compound, rows), h in zip(compounds, hues):
        compound_colors[compound] = hsv_hex(h, 1.0, 1.0)

        m = len(rows)
        if m == 1:
            sv = [(1.0, 1.0)]
        else:
            sv = list(zip(np.linspace(1.0, 0.55, m), np.linspace(1.0, 0.35, m)))

        ion_colors[compound] = {}
        ion_colors_by_pos[compound] = {}

        for pos, ((s, v), (_, row)) in enumerate(zip(sv, rows.iterrows())):
            color = hsv_hex(h, s, v)
            ion_colors[compound][int(row["id"])] = color
            ion_colors_by_pos[compound][str(pos)] = color

    return compound_colors, ion_colors, ion_colors_by_pos


def generate_html_aligned(figures, output_file, title, trace_maps, annotation_df, eic_data):
    """Render HTML for aligned pipeline with EIC support."""
    figure_data_dict = {str(i): json.loads(fig.to_json()) for i, fig in enumerate(figures)}
    trace_maps_dict = {str(i): tm for i, tm in enumerate(trace_maps)}

    annotation_records = []
    for compound, group in annotation_df.groupby("Compound Name"):
        if pd.isna(compound) or not str(compound).strip():
            continue
        ions = [{"id": int(row["id"]), "mz": float(row["mz"])} for _, row in group.iterrows()]
        annotation_records.append({"Compound Name": str(compound), "ions": ions})
    annotation_records.sort(key=lambda x: x["Compound Name"].lower())

    env = Environment(loader=FileSystemLoader(SCRIPT_DIR))
    template = env.get_template("template_pipeline_2.html")

    compound_colors, ion_colors, ion_colors_by_pos = build_color_maps(annotation_df)
    html_content = template.render(
        title=title,
        total_chunks=len(figures),
        figure_data=figure_data_dict,
        trace_maps_data=trace_maps_dict,
        annotation_data=annotation_records,
        compound_colors=compound_colors,
        ion_colors=ion_colors,
        ion_colors_by_pos=ion_colors_by_pos,
        eic_data=eic_data,
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
