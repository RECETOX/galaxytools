import argparse

from utils import LoadDataAction, StoreOutputAction

def perform_operation(df, column_index, operation, operand):
    column_name = df.columns[column_index - 1]  # Convert base-1 index to zero-based index
    if operation == 'mul':
        df[column_name] = df[column_name] * operand
    elif operation == 'sub':
        df[column_name] = df[column_name] - operand
    elif operation == 'div':
        df[column_name] = df[column_name] / operand
    elif operation == 'add':
        df[column_name] = df[column_name] + operand
    elif operation == 'pow':
        df[column_name] = df[column_name] ** operand
    else:
        raise ValueError(f"Unsupported operation: {operation}")
    return df

def main(input_dataset, column_index, operation, operand, output_dataset):
    df = input_dataset
    df = perform_operation(df, column_index, operation, operand)
    write_func, file_path = output_dataset
    write_func(df, file_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Perform arithmetic operations on a dataframe column.')
    parser.add_argument('--input_dataset', nargs=2, action=LoadDataAction, required=True, help='Path to the input dataset and its file extension (csv, tsv, parquet)')
    parser.add_argument('--column', type=int, required=True, help='Base-1 index of the column to perform the operation on')
    parser.add_argument('--operation', type=str, choices=['mul', 'sub', 'div', 'add', 'pow'], required=True, help='Arithmetic operation to perform')
    parser.add_argument('--operand', type=float, required=True, help='Operand for the arithmetic operation')
    parser.add_argument('--output_dataset', nargs=2, action=StoreOutputAction, required=True, help='Path to the output dataset and its file extension (csv, tsv, parquet)')

    args = parser.parse_args()
    main(args.input_dataset, args.column, args.operation, args.operand, args.output_dataset)