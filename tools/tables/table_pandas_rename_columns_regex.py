import re
import argparse
import logging
import pandas as pd
from typing import List, Tuple
from utils import LoadDataAction, SplitColumnIndicesAction, StoreOutputAction


def rename_columns(
    df: pd.DataFrame, columns: List[int], regex_check: str, regex_replace: str
) -> pd.DataFrame:
    """
    Rename columns in the dataframe based on regex patterns.

    Parameters:
    df (pd.DataFrame): The input dataframe.
    columns (List[int]): The 0-based indices of the columns to rename.
    regex_check (str): The regex pattern to check for in column names.
    regex_replace (str): The regex pattern to replace with in column names.

    Returns:
    pd.DataFrame: The dataframe with renamed columns.
    """
    try:
        # Map column indices to column names
        column_names = [df.columns[i] for i in columns]

        # Rename the specified columns using the regex patterns
        for column in column_names:
            if column in df.columns:
                new_column_name = re.sub(regex_check, regex_replace, column)
                df.rename(columns={column: new_column_name}, inplace=True)
        return df
    except IndexError as e:
        logging.error(f"Invalid column index: {e}")
        raise
    except re.error as e:
        logging.error(f"Invalid regex pattern: {e}")
        raise
    except Exception as e:
        logging.error(f"Error renaming columns: {e}")
        raise


def main(
    input_dataset: Tuple[pd.DataFrame, str],
    columns: List[int],
    regex_check: str,
    regex_replace: str,
    output_dataset: Tuple[callable, str],
) -> None:
    """
    Main function to load the dataset, rename columns, and save the result.

    Parameters:
    input_dataset (Tuple[pd.DataFrame, str]): The input dataset and its file extension.
    columns (List[int]): The 0-based indices of the columns to rename.
    regex_check (str): The regex pattern to check for in column names.
    regex_replace (str): The regex pattern to replace with in column names.
    output_dataset (Tuple[callable, str]): The output dataset and its file extension.
    """
    try:
        df, _ = input_dataset
        df = rename_columns(df, columns, regex_check, regex_replace)
        write_func, file_path = output_dataset
        write_func(df, file_path)
    except Exception as e:
        logging.error(f"Error in main function: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description="Apply regex-based transformations on multiple dataframe columns."
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
        "--regex_check",
        type=str,
        required=True,
        help="Regex pattern to check for in column names",
    )
    parser.add_argument(
        "--regex_replace",
        type=str,
        required=True,
        help="Regex pattern to replace with in column names",
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
    main(
        args.input_dataset,
        column_indices,
        args.regex_check,
        args.regex_replace,
        args.output_dataset,
    )
