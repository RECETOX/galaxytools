import argparse
import logging
from typing import List, Optional, Tuple


import pandas as pd
from utils import LoadDataAction, SplitColumnIndicesAction, StoreOutputAction


def drop_na_values(
    df: pd.DataFrame,
    axis: str,
    how: Optional[str] = None,
    subset: Optional[List[int]] = None,
) -> pd.DataFrame:
    """
    Drop rows or columns with NA values from a dataframe.

    Parameters:
    df (pd.DataFrame): The input dataframe.
    axis (str): {'index' or 'columns'} - Axis along which to apply the drop. 'index' for rows, 'columns' for columns.
    how (str, optional): {'any', 'all'} - Determine if row or column is removed from DataFrame, when we have
        at least one NA or all NA.
        - 'any' : If any NA values are present, drop that row or column.
        - 'all' : If all values are NA, drop that row or column.
    subset (List[int], optional): Labels along the other axis (columns for rows, rows for columns) to consider.

    Returns:
    pd.DataFrame: The dataframe with NA values dropped.
    """
    try:
        # Convert subset indices to column names if provided
        subset_cols = None
        if subset is not None:
            subset_cols = [df.columns[idx] for idx in subset]

        # Call dropna with appropriate parameters
        kwargs = {
            "axis": 0 if axis == "index" else 1,
            "subset": subset_cols,
        }

        kwargs["how"] = how if how else "any"

        df_result = df.dropna(**kwargs)
        return df_result
    except Exception as e:
        logging.error(f"Error applying dropna: {e}")
        raise


def main(
    input_dataset: pd.DataFrame,
    axis: str,
    how: Optional[str],
    subset: Optional[List[int]],
    output_dataset: Tuple[callable, str],
) -> None:
    """
    Main function to load the dataset, drop NA values, and save the result.

    Parameters:
    input_dataset (pd.DataFrame): The input dataset.
    axis (str): Axis along which to apply the drop.
    how (str, optional): How to determine if a row or column should be dropped.
    subset (List[int], optional): Column indices to consider for rows.
    output_dataset (Tuple[callable, str]): The output dataset writer function and file path.
    """
    try:
        df = drop_na_values(input_dataset, axis, how, subset)
        write_func, file_path = output_dataset
        write_func(df, file_path)
    except Exception as e:
        logging.error(f"Error in main function: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description="Drop rows or columns with NA values from a dataframe."
    )
    parser.add_argument(
        "--input_dataset",
        nargs=2,
        action=LoadDataAction,
        required=True,
        help="Path to the input dataset and its file extension (csv, tsv, parquet)",
    )
    parser.add_argument(
        "--axis",
        type=str,
        choices=["index", "columns"],
        default="index",
        help="Axis along which to apply the drop. 'index' to drop rows, 'columns' to drop columns.",
    )
    parser.add_argument(
        "--how",
        type=str,
        choices=["any", "all"],
        default=None,
        help="'any' to drop rows/columns with any NA values, 'all' to drop only rows/columns with all NA values.",
    )
    parser.add_argument(
        "--subset",
        action=SplitColumnIndicesAction,
        default=None,
        help="Comma-separated list of 1-based column indices to consider (only applies when axis='index').",
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
        args.input_dataset,
        args.axis,
        args.how,
        args.subset,
        args.output_dataset,
    )
