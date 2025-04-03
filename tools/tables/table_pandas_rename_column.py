import argparse
import logging
from typing import Tuple

import pandas as pd
from utils import KeyValuePairsAction, LoadDataAction, StoreOutputAction


def rename_columns(df: pd.DataFrame, rename_dict: dict):
    """
    Rename columns in the dataframe based on the provided dictionary.

    Parameters:
    df (pd.DataFrame): The input dataframe.
    rename_dict (dict): A dictionary with 1-based column index as key and new column name as value.

    Returns:
    pd.DataFrame: The dataframe with renamed columns.
    """
    try:
        rename_map = {
            df.columns[key - 1]: value for key, value in rename_dict.items()
        }  # Convert 1-based index to column name
        return df.rename(columns=rename_map)
    except IndexError as e:
        logging.error(f"Invalid column index: {e}")
        raise
    except Exception as e:
        logging.error(f"Error renaming columns: {e}")
        raise


def main(input_dataset: pd.DataFrame, rename_dict: dict, output_dataset: Tuple[callable, str]):
    """
    Main function to load the dataset, rename columns, and save the result.

    Parameters:
    input_dataset (pd.DataFrame): The input dataset .
    rename_dict (dict): A dictionary with 1-based column index as key and new column name as value.
    output_dataset (tuple): The function to store the output dataset and the path.
    """
    try:
        write_func, file_path = output_dataset
        write_func(rename_columns(input_dataset, rename_dict), file_path)
    except Exception as e:
        logging.error(f"Error in main function: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Rename columns in a dataframe.")
    parser.add_argument(
        "--input_dataset",
        nargs=2,
        action=LoadDataAction,
        required=True,
        help="Path to the input dataset and its file extension (csv, tsv, parquet)",
    )
    parser.add_argument(
        "--rename",
        nargs="+",
        action=KeyValuePairsAction,
        required=True,
        help="List of key=value pairs with 1-based column index as key and new column name as value",
    )
    parser.add_argument(
        "--output_dataset",
        nargs=2,
        action=StoreOutputAction,
        required=True,
        help="Path to the output dataset and its file extension (csv, tsv, parquet)",
    )

    args = parser.parse_args()
    main(args.input_dataset, args.rename, args.output_dataset)
