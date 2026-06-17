"""CLI for unaligned interactive peak table plotting.

Usage example:
python peaktable_plot_unaligned.py \
  --title Demo \
  --noise-threshold 100 \
  --chunk-size 9 \
  --file-path /data/peaks \
  --signal-value intensity
"""

import argparse
import os
import time

from utils import (
    chunk_files,
    compute_global_axes,
    generate_html,
    render_chunks_parallel,
)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate interactive plots from unaligned peak tables.",
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
        "--file-path",
        required=True,
        help="Directory containing peak tables (.mzml, .parquet, .csv).",
    )
    parser.add_argument(
        "--signal-value",
        choices=["area", "intensity"],
        required=True,
        help="Signal column used for coloring and thresholding.",
    )
    parser.add_argument(
        "--output-html",
        default=None,
        help="Optional output HTML path. Defaults next to input directory.",
    )
    return parser


def validate_args(parser, args):
    if args.noise_threshold <= 0:
        parser.error("--noise-threshold must be > 0.")
    if args.chunk_size <= 0:
        parser.error("--chunk-size must be > 0.")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(parser, args)

    start = time.perf_counter()

    chunks = chunk_files(args.file_path, chunk_size=args.chunk_size)
    global_axes = compute_global_axes(
        args.file_path,
        threshold=args.noise_threshold,
        signal_value=args.signal_value,
    )

    figures, trace_maps, is_clustered = render_chunks_parallel(
        chunks=chunks,
        global_axes=global_axes,
        title=args.title,
        threshold=args.noise_threshold,
        signal_value=args.signal_value,
    )

    output_html = args.output_html or os.path.join(
        os.path.dirname(args.file_path),
        f"peaktable_plot_combined_{args.title}.html",
    )
    generate_html(
        figures,
        output_html,
        title=args.title,
        trace_maps=trace_maps,
        is_clustered=is_clustered,
    )

    stop = time.perf_counter()
    print(f"Output written to: {output_html}")
    print(f"Execution time: {stop - start:.4}s")


if __name__ == "__main__":
    main()
