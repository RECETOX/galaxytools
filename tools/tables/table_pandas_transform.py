import argparse

import numpy as np
from utils import LoadDataAction, StoreOutputAction, SplitColumnIndicesAction

def apply_transformation(df, columns, transformation):
    for column_index in columns:
        column_name = df.columns[column_index]  # Use 0-based index directly
        if transformation == "log2":
            df[column_name] = np.log2(df[column_name])
        elif transformation == "log10":
            df[column_name] = np.log10(df[column_name])
        elif transformation == "ln":
            df[column_name] = np.log(df[column_name])
        elif transformation == "sqrt":
            df[column_name] = np.sqrt(df[column_name])
        elif transformation == "exp":
            df[column_name] = np.exp(df[column_name])
        elif transformation == "abs":
            df[column_name] = np.abs(df[column_name])
        elif transformation == "floor":
            df[column_name] = np.floor(df[column_name])
        elif transformation == "ceil":
            df[column_name] = np.ceil(df[column_name])
        else:
            raise ValueError(f"Unsupported transformation: {transformation}")
    return df

def main(input_dataset, columns, transformation, output_dataset):
    df = input_dataset
    df = apply_transformation(df, columns, transformation)
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
        "--transformation",
        type=str,
        choices=["log", "log10", "ln", "sqrt", "exp", "abs", "floor", "ceil"],
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
    main(
        args.input_dataset,
        args.columns,
        args.transformation,
        args.output_dataset
    )