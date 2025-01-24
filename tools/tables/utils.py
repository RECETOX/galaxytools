import argparse
import pandas as pd
from typing import Callable, Tuple


class KeyValuePairsAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        """
        Parse key=value pairs from the command line arguments.

        Parameters:
        parser (argparse.ArgumentParser): The argument parser instance.
        namespace (argparse.Namespace): The namespace to hold the parsed values.
        values (list): The list of key=value pairs.
        option_string (str): The option string.

        Sets:
        namespace.dest (dict): A dictionary with 1-based column index as key and new column name as value.
        """
        key_value_pairs = {}
        for item in values:
            try:
                key, value = item.split("=")
                key_value_pairs[int(key)] = value  # Convert key to integer
            except ValueError:
                parser.error(f"Invalid format for --rename: {item}. Expected format: key=value")
        setattr(namespace, self.dest, key_value_pairs)

class LoadDataAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        file_path, file_extension = values
        file_extension = file_extension.lower()
        if file_extension == "csv":
            df = pd.read_csv(file_path)
        elif file_extension in ["tsv", "tabular"]:
            df = pd.read_csv(file_path, sep="\t")
        elif file_extension == "parquet":
            df = pd.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
        setattr(namespace, self.dest, df)


def write_csv(df: pd.DataFrame, file_path: str) -> None:
    """
    Write the dataframe to a CSV file.

    Parameters:
    df (pd.DataFrame): The dataframe to write.
    file_path (str): The path to the output CSV file.
    """
    df.to_csv(file_path, index=False)


def write_tsv(df: pd.DataFrame, file_path: str) -> None:
    """
    Write the dataframe to a TSV file.

    Parameters:
    df (pd.DataFrame): The dataframe to write.
    file_path (str): The path to the output TSV file.
    """
    df.to_csv(file_path, sep="\t", index=False)


def write_parquet(df: pd.DataFrame, file_path: str) -> None:
    """
    Write the dataframe to a Parquet file.

    Parameters:
    df (pd.DataFrame): The dataframe to write.
    file_path (str): The path to the output Parquet file.
    """
    df.to_parquet(file_path, index=False)


class StoreOutputAction(argparse.Action):
    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace, values: Tuple[str, str], option_string: str = None) -> None:
        """
        Custom argparse action to store the output function and file path based on file extension.

        Parameters:
        parser (argparse.ArgumentParser): The argument parser instance.
        namespace (argparse.Namespace): The namespace to hold the parsed values.
        values (Tuple[str, str]): The file path and file extension.
        option_string (str): The option string.
        """
        file_path, file_extension = values
        file_extension = file_extension.lower()
        if file_extension == "csv":
            write_func = write_csv
        elif file_extension in ["tsv", "tabular"]:
            write_func = write_tsv
        elif file_extension == "parquet":
            write_func = write_parquet
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
        setattr(namespace, self.dest, (write_func, file_path))


class SplitColumnIndicesAction(argparse.Action):
    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace, values: str, option_string: str = None) -> None:
        """
        Custom argparse action to split a comma-separated list of column indices and convert to 0-based indices.

        Parameters:
        parser (argparse.ArgumentParser): The argument parser instance.
        namespace (argparse.Namespace): The namespace to hold the parsed values.
        values (str): The comma-separated list of 1-based column indices.
        option_string (str): The option string.
        """
        indices = [int(x) - 1 for x in values.split(',')]  # Convert to 0-based indices
        setattr(namespace, self.dest, indices)
