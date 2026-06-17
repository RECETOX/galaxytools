"""Compatibility entry point for interactive peak table plotting.

Use dedicated scripts for each workflow:
- peaktable_plot_unaligned.py
- peaktable_plot_aligned.py

This wrapper keeps the old command path available and dispatches based on
`--mode`.
"""

import argparse

from peaktable_plot_aligned import main as aligned_main
from peaktable_plot_unaligned import main as unaligned_main


def build_parser():
    parser = argparse.ArgumentParser(
        description="Compatibility wrapper for split aligned/unaligned CLIs.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=["aligned", "unaligned"],
        required=True,
        help="Which dedicated CLI should handle the run.",
    )
    parser.add_argument(
        "remaining_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the selected CLI.",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    forwarded = args.remaining_args
    if forwarded and forwarded[0] == "--":
        forwarded = forwarded[1:]

    if args.mode == "aligned":
        aligned_main(forwarded)
    else:
        unaligned_main(forwarded)


if __name__ == "__main__":
    main()
