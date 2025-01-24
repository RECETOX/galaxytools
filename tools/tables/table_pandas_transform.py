import argparse
import logging
from typing import Callable, List, Tuple


import numpy as np
import pandas as pd
from utils import LoadDataAction, SplitColumnIndicesAction, StoreOutputAction


# Define the available transformations
TRANSFORMATIONS = {
    "log": np.log,
    "log10": np.log10,
    "ln": np.log,
    "sqrt": np.sqrt,
    "exp": np.exp,
    "abs": np.abs,
    "floor": np.floor,
    "ceil": np.ceil,
}


def apply_transformation(
    df: pd.DataFrame, columns: List[int], transformation: str
) -> pd.DataFrame:
    """
    Apply the specified transformation to the given columns of the dataframe.

    Parameters:
    df (pd.DataFrame): The input dataframe.
    columns (List[int]): The 0-based indices of the columns to transform.
    transformation (str): The transformation to apply.

    Returns:
    pd.DataFrame: The dataframe with the transformation applied.
    """
    try:
        transform_func = TRANSFORMATIONS[transformation]
        for column_index in columns:
            column_name = df.columns[column_index]
            df[column_name] = transform_func(df[column_name])
        return df
    except KeyError as e:
        logging.error(f"Invalid transformation: {e}")
        raise
    except IndexError as e:
        logging.error(f"Invalid column index: {e}")
        raise
    except Exception as e:
        logging.error(f"Error applying transformation: {e}")
        raise


def main(
    input_dataset: Tuple[pd.DataFrame, str],
    columns: List[int],
    transformation: str,
    output_dataset: Tuple[Callable[[pd.DataFrame, str], None], str],
) -> None:
    """
    Main function to load the dataset, apply the transformation, and save the result.

    Parameters:
    input_dataset (Tuple[pd.DataFrame, str]): The input dataset and its file extension.
    columns (List[int]): The 0-based indices of the columns to transform.
    transformation (str): The transformation to apply.
    output_dataset (Tuple[Callable[[pd.DataFrame, str], None], str]): The output dataset and its file extension.
    """
    try:
        df, _ = input_dataset
        df = apply_transformation(df, columns, transformation)
        write_func, file_path = output_dataset
        write_func(df, file_path)
    except Exception as e:
        logging.error(f"Error in main function: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description="Apply mathematical transformations to dataframe columns."
    )
    parser.add_argument(
        "--input_dataset",
        nargs=2,
        action=LoadDataAction,
        required=True,
        help="Path to the input dataset and its file extension (csv, tsv, parquet)",
    )
    parser.add_argument(
        "--columns",
        action=SplitColumnIndicesAction,
        required=True,
        help="Comma-separated list of 1-based indices of the columns to apply the transformation on",
    )
    parser.add_argument(
        "--transformation",
        type=str,
        choices=TRANSFORMATIONS.keys(),
        required=True,
        help="Transformation to apply",
    )
    parser.add_argument(
        "--output_dataset",
        nargs=2,
        action=StoreOutputAction,
        required=True,
        help="Path to the output dataset and its file extension (csv, tsv, parquet)",
    )

    args = parser.parse_args()
    # Adjust column indices to be 0-based
    column_indices = [index - 1 for index in args.columns]
    main(args.input_dataset, column_indices, args.transformation, args.output_dataset)
