"""CLI for aligned interactive peak table plotting with EIC computation.

Usage example:
python peaktable_plot_aligned.py \
  --title Demo \
  --noise-threshold 100 \
  --chunk-size 9 \
  --raw-input-path /data/raw \
  --markers-path markers.tsv \
  --mz-tol-ppm 10 \
  --rt-tol-s 15 \
  --intensity-path intensity.csv \
  --rt-path rt.csv \
  --metadata-path metadata.csv \
  --annotation-path annotation.tsv
"""

import argparse
import os
import time

from utils import (
    chunk_samples,
    compute_eic_data,
    compute_global_axes_aligned,
    generate_html_aligned,
    load_aligned_tables,
    load_markers,
    render_chunks_aligned,
)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate interactive plots from aligned tables and EIC traces.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--title", required=True, help="Title shown in the HTML report.")
    parser.add_argument(
        "--noise-threshold",
        type=float,
        required=True,
        help="Threshold to classify points as below/above noise.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=9,
        help="Number of subplots per page.",
    )
    parser.add_argument(
        "--cores-to-use",
        type=int,
        default=0,
        help="CPU cores for EIC computation. Use 0 for automatic selection.",
    )
    parser.add_argument(
        "--show-only-annotated",
        action="store_true",
        help="Only plot aligned features with annotations.",
    )
    parser.add_argument(
        "--raw-input-path",
        required=True,
        help="Directory with raw files for EIC extraction.",
    )
    parser.add_argument(
        "--markers-path",
        required=True,
        help="Marker/transition list path.",
    )
    parser.add_argument(
        "--mz-tol-ppm",
        type=float,
        required=True,
        help="m/z tolerance in ppm for EIC extraction.",
    )
    parser.add_argument(
        "--rt-tol-s",
        type=float,
        required=True,
        help="RT tolerance in seconds for EIC extraction.",
    )
    parser.add_argument(
        "--intensity-path",
        required=True,
        help="Path to aligned intensity table (.csv or .parquet).",
    )
    parser.add_argument(
        "--rt-path",
        required=True,
        help="Path to aligned RT table (.csv or .parquet).",
    )
    parser.add_argument(
        "--metadata-path",
        required=True,
        help="Path to aligned metadata table (.csv or .parquet).",
    )
    parser.add_argument(
        "--annotation-path",
        required=True,
        help="Path to annotation table.",
    )
    parser.add_argument(
        "--output-html",
        default=None,
        help="Optional output HTML path. Defaults next to intensity table.",
    )
    return parser


def validate_args(parser, args):
    if args.noise_threshold <= 0:
        parser.error("--noise-threshold must be > 0.")
    if args.chunk_size <= 0:
        parser.error("--chunk-size must be > 0.")
    if args.cores_to_use < 0:
        parser.error("--cores-to-use must be >= 0.")
    if args.mz_tol_ppm <= 0:
        parser.error("--mz-tol-ppm must be > 0.")
    if args.rt_tol_s <= 0:
        parser.error("--rt-tol-s must be > 0.")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(parser, args)

    start = time.perf_counter()

    sample_dfs_full, _ = load_aligned_tables(
        intensity_path=args.intensity_path,
        rt_path=args.rt_path,
        metadata_path=args.metadata_path,
        annotation_path=args.annotation_path,
        show_only_annotated=0,
    )
    global_axes = compute_global_axes_aligned(sample_dfs_full, threshold=args.noise_threshold)

    sample_dfs, annotation_df = load_aligned_tables(
        intensity_path=args.intensity_path,
        rt_path=args.rt_path,
        metadata_path=args.metadata_path,
        annotation_path=args.annotation_path,
        show_only_annotated=1 if args.show_only_annotated else 0,
    )

    markers = load_markers(args.markers_path)
    sample_names = [name for name, _ in sample_dfs]

    start_eic = time.perf_counter()
    eic_data = compute_eic_data(
        raw_input_path=args.raw_input_path,
        markers=markers,
        sample_names=sample_names,
        mz_tol_ppm=args.mz_tol_ppm,
        rt_tol_s=args.rt_tol_s,
        cores_to_use=args.cores_to_use,
    )
    stop_eic = time.perf_counter()
    print(f"EIC computation time: {stop_eic - start_eic:.4}s")

    chunks = chunk_samples(sample_dfs, chunk_size=args.chunk_size)
    figures, trace_maps = render_chunks_aligned(
        chunks=chunks,
        global_axes=global_axes,
        title=args.title,
        threshold=args.noise_threshold,
        annotation_df=annotation_df,
    )

    output_html = args.output_html or os.path.join(
        os.path.dirname(args.intensity_path),
        f"peaktable_plot_aligned_{args.title}.html",
    )
    generate_html_aligned(
        figures,
        output_html,
        title=args.title,
        trace_maps=trace_maps,
        annotation_df=annotation_df,
        eic_data=eic_data,
    )

    stop = time.perf_counter()
    print(f"Output written to: {output_html}")
    print(f"Execution time: {stop - start:.4}s")


if __name__ == "__main__":
    main()
