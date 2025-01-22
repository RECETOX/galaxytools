import argparse
from utils import LoadDataAction, StoreOutputAction


class KeyValuePairsAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        key_value_pairs = {}
        for item in values:
            key, value = item.split("=")
            key_value_pairs[int(key)] = value  # Convert key to integer
        setattr(namespace, self.dest, key_value_pairs)


def rename_columns(df, rename_dict):
    rename_map = {
        df.columns[key - 1]: value for key, value in rename_dict.items()
    }  # Convert 1-based index to column name
    return df.rename(columns=rename_map)


def main(input_dataset, rename_dict, output_dataset):
    df = input_dataset
    df = rename_columns(df, rename_dict)
    write_func, file_path = output_dataset
    write_func(df, file_path)


if __name__ == "__main__":
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
