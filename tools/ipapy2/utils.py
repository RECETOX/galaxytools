import argparse
import pandas as pd
from typing import Tuple


class LoadDataAction(argparse.Action):
    """
    Custom argparse action to load data from a file.
    Supported file formats: CSV, TSV, Tabular and Parquet.

    """

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Load data from a file and store it in the namespace.
        :param namespace: Namespace object
        :param values: Tuple containing the file path and file extension
        :param option_string: Option string
        :return: None
        """
        file_path, file_extension = values
        file_extension = file_extension.lower()
        if file_extension == "csv":
            df = pd.read_csv(file_path).replace("", None)
        elif file_extension in ["tsv", "tabular"]:
            df = pd.read_csv(file_path, sep="\t").replace("", None)
        elif file_extension == "parquet":
            df = pd.read_parquet(file_path).replace("", None)
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
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Tuple[str, str],
        option_string: str = None,
    ) -> None:
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
