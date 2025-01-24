import argparse
import logging

import numpy as np


from utils import LoadDataAction, SplitColumnIndicesAction, StoreOutputAction


# Constants for operations
OPERATIONS = {
    "mul": np.multiply,
    "sub": np.subtract,
    "div": np.divide,
    "add": np.add,
    "pow": np.power,
}


def perform_operation(df, column_indices, operation, operand):
    """
    Perform the specified arithmetic operation on the given columns of the dataframe.

    Parameters:
    df (pd.DataFrame): The input dataframe.
    column_indices (list): The 0-based indices of the columns to perform the operation on.
    operation (str): The arithmetic operation to perform.
    operand (float): The operand for the arithmetic operation.

    Returns:
    pd.DataFrame: The dataframe with the operation applied.
    """
    for column_index in column_indices:
        column_name = df.columns[column_index]
        df[column_name] = OPERATIONS[operation](df[column_name], operand)
    return df


def main(input_dataset, column_indices, operation, operand, output_dataset):
    """
    Main function to load the dataset, perform the operation, and save the result.

    Parameters:
    input_dataset (tuple): The input dataset and its file extension.
    column_indices (list): The 0-based indices of the columns to perform the operation on.
    operation (str): The arithmetic operation to perform.
    operand (float): The operand for the arithmetic operation.
    output_dataset (tuple): The output dataset and its file extension.
    """
    try:
        df = perform_operation(input_dataset, column_indices, operation, operand)
        write_func, file_path = output_dataset
        write_func(df, file_path)
    except Exception as e:
        logging.error(f"Error in main function: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description="Perform arithmetic operations on dataframe columns."
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
        help="Comma-separated list of 1-based indices of the columns to perform the operation on",
    )
    parser.add_argument(
        "--operation",
        type=str,
        choices=OPERATIONS.keys(),
        required=True,
        help="Arithmetic operation to perform",
    )
    parser.add_argument(
        "--operand",
        type=float,
        required=True,
        help="Operand for the arithmetic operation",
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
        args.operation,
        args.operand,
        args.output_dataset,
    )
