import argparse

import numpy as np
from scipy.interpolate import Akima1DInterpolator, CubicSpline, PchipInterpolator

from utils import LoadDataAction, StoreOutputAction


class InterpolationModelAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        interpolators = {
            "linear": np.interp,
            "cubic": CubicSpline,
            "pchip": PchipInterpolator,
            "akima": Akima1DInterpolator,
        }
        if values not in interpolators:
            raise ValueError(f"Unknown interpolation method: {values}")
        setattr(namespace, self.dest, interpolators[values])


def main(reference, query, x_col, y_col, xnew_col, model, output_dataset):
    # Index is passed with base 1 so we need to subtract 1 to get the correct column names
    x_col = reference.columns[x_col - 1]
    y_col = reference.columns[y_col - 1]
    xnew_col = query.columns[xnew_col - 1]

    if model == np.interp:
        query[y_col] = model(query[xnew_col], reference[x_col], reference[y_col])
    else:
        model_instance = model(reference[x_col], reference[y_col])
        query[y_col] = model_instance(query[xnew_col]).astype(float)

    write_func, file_path = output_dataset
    write_func(query, file_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Interpolate data using various methods."
    )
    parser.add_argument(
        "--reference_dataset",
        nargs=2,
        action=LoadDataAction,
        required=True,
        help="Path to the reference dataset and its file extension (csv, tsv, parquet)",
    )
    parser.add_argument(
        "--query_dataset",
        nargs=2,
        action=LoadDataAction,
        required=True,
        help="Path to the query dataset and its file extension (csv, tsv, parquet)",
    )
    parser.add_argument(
        "--x_col",
        type=int,
        required=True,
        help="Index of the x column in the reference dataset (1-based)",
    )
    parser.add_argument(
        "--y_col",
        type=int,
        required=True,
        help="Index of the y column in the reference dataset (1-based)",
    )
    parser.add_argument(
        "--xnew_col",
        type=int,
        required=True,
        help="Index of the x column in the query dataset (1-based)",
    )
    parser.add_argument(
        "--method",
        type=str,
        choices=["linear", "cubic", "pchip", "akima"],
        action=InterpolationModelAction,
        required=True,
        help="Interpolation method",
    )
    parser.add_argument(
        "--output_dataset",
        nargs=2,
        action=StoreOutputAction,
        required=True,
        help="Path to the output dataset and its file extension (csv, tsv, parquet)",
    )

    args = parser.parse_args()
    main(
        args.reference_dataset,
        args.query_dataset,
        args.x_col,
        args.y_col,
        args.xnew_col,
        args.method,
        args.output_dataset,
    )
