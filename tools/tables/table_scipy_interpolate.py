import argparse
import logging
from typing import Callable, Tuple


import numpy as np
import pandas as pd
from scipy.interpolate import Akima1DInterpolator, CubicSpline, PchipInterpolator
from utils import LoadDataAction, StoreOutputAction


class InterpolationModelAction(argparse.Action):
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str,
        option_string: str = None,
    ) -> None:
        """
        Custom argparse action to map interpolation method names to their corresponding functions.

        Parameters:
        parser (argparse.ArgumentParser): The argument parser instance.
        namespace (argparse.Namespace): The namespace to hold the parsed values.
        values (str): The interpolation method name.
        option_string (str): The option string.
        """
        interpolators = {
            "linear": np.interp,
            "cubic": CubicSpline,
            "pchip": PchipInterpolator,
            "akima": Akima1DInterpolator,
        }
        if values not in interpolators:
            raise ValueError(f"Unknown interpolation method: {values}")
        setattr(namespace, self.dest, interpolators[values])


def interpolate_data(
    reference: pd.DataFrame,
    query: pd.DataFrame,
    x_col: int,
    y_col: int,
    xnew_col: int,
    model: Callable,
    output_dataset: Tuple[Callable[[pd.DataFrame, str], None], str],
) -> None:
    """
    Interpolate data using the specified model.

    Parameters:
    reference (pd.DataFrame): The reference dataset.
    query (pd.DataFrame): The query dataset.
    x_col (int): The 1-based index of the x column in the reference dataset.
    y_col (int): The 1-based index of the y column in the reference dataset.
    xnew_col (int): The 1-based index of the x column in the query dataset.
    model (Callable): The interpolation model to use.
    output_dataset (Tuple[Callable[[pd.DataFrame, str], None], str]): The output dataset and its file extension.
    """
    try:
        # Convert 1-based indices to 0-based indices
        x_col_name = reference.columns[x_col - 1]
        y_col_name = reference.columns[y_col - 1]
        xnew_col_name = query.columns[xnew_col - 1]

        # Check if y_col already exists in the query dataset
        if y_col_name in query.columns:
            raise ValueError(
                f"Column '{y_col_name}' already exists in the query dataset."
            )

        if model == np.interp:
            query[y_col_name] = model(
                query[xnew_col_name], reference[x_col_name], reference[y_col_name]
            )
        else:
            model_instance = model(reference[x_col_name], reference[y_col_name])
            query[y_col_name] = model_instance(query[xnew_col_name]).astype(float)

        write_func, file_path = output_dataset
        write_func(query, file_path)
    except Exception as e:
        logging.error(f"Error in interpolate_data function: {e}")
        raise


def main(
    reference_dataset: Tuple[pd.DataFrame, str],
    query_dataset: Tuple[pd.DataFrame, str],
    x_col: int,
    y_col: int,
    xnew_col: int,
    model: Callable,
    output_dataset: Tuple[Callable[[pd.DataFrame, str], None], str],
) -> None:
    """
    Main function to load the datasets, perform interpolation, and save the result.

    Parameters:
    reference_dataset (Tuple[pd.DataFrame, str]): The reference dataset and its file extension.
    query_dataset (Tuple[pd.DataFrame, str]): The query dataset and its file extension.
    x_col (int): The 1-based index of the x column in the reference dataset.
    y_col (int): The 1-based index of the y column in the reference dataset.
    xnew_col (int): The 1-based index of the x column in the query dataset.
    model (Callable): The interpolation model to use.
    output_dataset (Tuple[Callable[[pd.DataFrame, str], None], str]): The output dataset and its file extension.
    """
    try:
        reference_df, _ = reference_dataset
        query_df, _ = query_dataset
        interpolate_data(
            reference_df, query_df, x_col, y_col, xnew_col, model, output_dataset
        )
    except Exception as e:
        logging.error(f"Error in main function: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
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
        help="1-based index of the x column in the reference dataset",
    )
    parser.add_argument(
        "--y_col",
        type=int,
        required=True,
        help="1-based index of the y column in the reference dataset",
    )
    parser.add_argument(
        "--xnew_col",
        type=int,
        required=True,
        help="1-based index of the x column in the query dataset",
    )
    parser.add_argument(
        "--model",
        type=str,
        action=InterpolationModelAction,
        required=True,
        help="Interpolation model to use (linear, cubic, pchip, akima)",
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
        args.model,
        args.output_dataset,
    )
