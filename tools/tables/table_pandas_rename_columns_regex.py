import re

import argparse
import pandas as pd
from utils import LoadDataAction, SplitColumnIndicesAction, StoreOutputAction


def rename_columns(df: pd.DataFrame, columns, regex_check, regex_replace):
    # Map column indices to column names
    column_names = [df.columns[i] for i in columns]

    # Rename the specified columns using the regex patterns
    for column in column_names:
        if column in df.columns:
            new_column_name = re.sub(regex_check, regex_replace, column)
            df.rename(columns={column: new_column_name}, inplace=True)
    return df

def main(input_dataset, columns, regex_check, regex_replace, output_dataset):
    df = input_dataset
    df = rename_columns(df, columns, regex_check, regex_replace)
    write_func, file_path = output_dataset
    write_func(df, file_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Apply transformations on multiple dataframe columns."
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
    main(
        args.input_dataset,
        args.columns,
        args.regex_check,
        args.regex_replace,
        args.output_dataset
    )
